#!/usr/bin/env python3
"""
10-K / 20-F SEC filing analyser — PMM competitive intelligence.

Usage:
    python3 analyse.py CRM
    python3 analyse.py MSFT
    python3 analyse.py MNDY
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

# ── SEC API config ────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "gtm-signal-miner hello@varshaa.dev"}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"
)

# ── helpers ───────────────────────────────────────────────────────────────────


def load_api_key() -> str:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not found. Copy .env.example to .env at the repo root.")
    return key


def get_cik(ticker: str) -> tuple[str, str]:
    """Return (zero-padded CIK, company name) for a ticker symbol."""
    resp = requests.get(TICKERS_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    ticker_upper = ticker.upper()
    for entry in resp.json().values():
        if entry["ticker"].upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10), entry["title"]
    raise ValueError(f"Ticker '{ticker}' not found in EDGAR company list")


def get_latest_annual_filing(cik: str) -> dict:
    """Fetch the submissions JSON and return metadata for the most recent 10-K or 20-F."""
    url = SUBMISSIONS_URL.format(cik=cik)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    filings = data["filings"]["recent"]
    for i, form in enumerate(filings["form"]):
        if form in ("10-K", "20-F"):
            return {
                "form_type": form,
                "accession": filings["accessionNumber"][i],
                "primary_doc": filings["primaryDocument"][i],
                "filing_date": filings["filingDate"][i],
            }

    # Some large filers overflow into additional filing files — surface a clear error
    raise ValueError(
        f"No 10-K or 20-F found in recent filings for CIK {cik}. "
        "The company may have too many historical filings; check EDGAR directly."
    )


def strip_html(html: str) -> str:
    """Strip HTML tags and decode common entities."""
    # Remove script / style blocks entirely
    html = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", " ", html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Drop all remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode entities
    replacements = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&apos;": "'",
    }
    for ent, char in replacements.items():
        html = html.replace(ent, char)
    # Collapse whitespace
    return re.sub(r"\s+", " ", html).strip()


def fetch_10k_text(cik: str, filing: dict) -> tuple[str, str]:
    """Download the primary annual filing document and return (plain_text, source_url)."""
    cik_int = str(int(cik))  # URL path uses integer CIK (no leading zeros)
    accession_no_dashes = filing["accession"].replace("-", "")
    primary_doc = filing["primary_doc"]

    url = ARCHIVES_URL.format(
        cik=cik_int,
        accession=accession_no_dashes,
        doc=primary_doc,
    )
    print(f"  URL: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=90)
    resp.raise_for_status()

    text = resp.text
    if primary_doc.lower().endswith((".htm", ".html")):
        text = strip_html(text)

    # Cap at ~200k chars — enough to cover the narrative sections Claude needs
    max_chars = 200_000
    if len(text) > max_chars:
        text = text[:max_chars]
        text += "\n\n[Document truncated at 200,000 characters for analysis]"

    return text, url


# ── Claude analysis ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a senior Product Marketing Manager (PMM) specialising in competitive intelligence. \
You read SEC annual filings (10-K and 20-F) to surface strategic signals that matter to competing or partnering PMMs.

Your analysis is precise, opinionated, and actionable. \
You quote directly from filings. You highlight what changed, not just what exists. \
You skip boilerplate and go straight to signal.\
"""

ANALYSIS_TEMPLATE = """\
Analyse this {form_type} SEC filing and produce a structured PMM signal report.

Company:      {company}
Ticker:       {ticker}
Filing type:  {form_type}
Filing date:  {filing_date}
Analysis date: {analysis_date}

<filing>
{doc_text}
</filing>

---

Produce the report using EXACTLY the section headers below. \
Do not add extra sections. Quote the filing directly wherever it strengthens a point.

## {form_type} Signal Report: {ticker}

**Company:** {company}
**Filing Type:** {form_type}
**Filing Date:** {filing_date}
**Analysis Date:** {analysis_date}

---

### How they describe their market and customers
Analyse the specific language, terminology, and framing used to describe their TAM, \
customer segments, use cases, and ICP. Quote key phrases verbatim. \
Note any evolution in who they say they serve.

### Where they're investing vs pulling back
Identify R&D priorities, new product bets, headcount signals, capex trends, geographic moves, \
and any areas of divestment or reduced emphasis. Use specific numbers where available.

### Risk factors a competitor PMM should know
Surface the most strategically revealing admissions — vulnerabilities they acknowledge, \
market threats they name, competitive pressures they flag, and regulatory exposure. \
Quote from the risk factors section.

### Competitors they name and how they frame them
List every named competitor or competitive category. \
Analyse the framing: minimising, acknowledging, or repositioning? \
Note any significant competitors conspicuously absent.

### Narrative shifts from prior year
Identify what is new, what is de-emphasised, and what language has changed. \
What themes are rising? What was prominent before that is now buried or gone?

### PMM actions
5–7 specific, tactical actions a competing or partnering PMM should take \
based on these signals. Be direct and concrete.\
"""


def analyse_with_claude(
    ticker: str,
    company_name: str,
    form_type: str,
    filing_date: str,
    doc_text: str,
    api_key: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    analysis_date = datetime.now().strftime("%Y-%m-%d")
    user_content = ANALYSIS_TEMPLATE.format(
        ticker=ticker,
        company=company_name,
        form_type=form_type,
        filing_date=filing_date,
        analysis_date=analysis_date,
        doc_text=doc_text,
    )

    chunks: list[str] = []

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            chunks.append(text)

        final = stream.get_final_message()
        cached = final.usage.cache_read_input_tokens
        created = final.usage.cache_creation_input_tokens
        if cached:
            print(f"\n  [cache hit: {cached:,} tokens read from cache]")
        elif created:
            print(f"\n  [cache written: {created:,} tokens cached for next run]")

    print()
    return "".join(chunks)


# ── output ────────────────────────────────────────────────────────────────────


def save_output(ticker: str, form_type: str, content: str) -> str:
    slug = form_type.lower().replace("-", "")  # "10-K" → "10k", "20-F" → "20f"
    filename = f"{ticker.lower()}-{slug}-{datetime.now().strftime('%Y%m%d')}.md"
    Path(filename).write_text(content, encoding="utf-8")
    return filename


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage:   python3 analyse.py <TICKER>")
        print("Example: python3 analyse.py CRM")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"\n{'═' * 58}")
    print(f"  10-K / 20-F Analyser  ·  {ticker}")
    print(f"{'═' * 58}\n")

    print("[1/5] Loading API key...")
    api_key = load_api_key()
    print("  ✓ Loaded\n")

    print(f"[2/5] Looking up CIK for {ticker}...")
    cik, company_name = get_cik(ticker)
    print(f"  ✓ {company_name}  (CIK: {cik})\n")

    print("[3/5] Finding most recent annual filing (10-K or 20-F)...")
    filing = get_latest_annual_filing(cik)
    form_type = filing["form_type"]
    print(f"  ✓ {form_type}  ·  Filed {filing['filing_date']}  ·  {filing['primary_doc']}\n")

    print("[4/5] Fetching document...")
    doc_text, doc_url = fetch_10k_text(cik, filing)
    print(f"  ✓ {len(doc_text):,} characters\n")

    print(f"[5/5] Analysing with Claude (streaming)...\n")
    print("─" * 58)
    analysis = analyse_with_claude(
        ticker, company_name, form_type, filing["filing_date"], doc_text, api_key
    )
    print("─" * 58)

    filename = save_output(ticker, form_type, analysis)

    print(f"\n{'═' * 58}")
    print(f"  Done!")
    print(f"  Output : {filename}")
    print(f"  Source : {doc_url}")
    print(f"{'═' * 58}\n")


if __name__ == "__main__":
    main()
