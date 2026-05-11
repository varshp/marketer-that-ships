#!/usr/bin/env python3
"""Competitor Page Decoder — fetch a URL, extract visible text, analyze with Claude."""

import sys
import re
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────

DOTENV_PATH = Path(__file__).resolve().parent.parent / ".env"
HEADERS = {"User-Agent": "gtm-signal-miner/1.0"}

NOISE_TAGS = [
    "nav", "footer", "header", "aside",
    "script", "style", "noscript", "iframe",
]
NOISE_CLASSES = re.compile(
    r"(cookie|banner|consent|modal|popup|overlay|toast|alert|"
    r"nav|navbar|navigation|footer|sidebar|breadcrumb|announcement)",
    re.I,
)

PMM_PROMPT = """\
You are a senior product marketing manager doing competitive intelligence.
Analyze the following text extracted from a competitor's website and produce a
concise strategic briefing.

Respond using EXACTLY this markdown structure (keep the headers verbatim):

### Their core pitch
One crisp sentence capturing what they claim to do and for whom.

### Who they're targeting
2–3 bullet points on buyer persona, company size, pain points signaled.

### Top 3 positioning bets
Numbered list. Each bet = the claim they're making + why it matters competitively.

### What they're not saying
2–3 bullet points on notable omissions, weaknesses they're hiding, or topics they avoid.

### PMM actions
3 concrete next steps for your team (e.g. messaging to sharpen, gaps to exploit, content to create).

---
PAGE TEXT:
{page_text}
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_api_key() -> str:
    load_dotenv(DOTENV_PATH)
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("Error: ANTHROPIC_API_KEY not found in environment or .env file.")
    return key


def fetch_page(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        sys.exit(f"Error fetching {url}: {e}")


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags entirely
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    # Remove elements whose class/id suggests chrome or cookie noise
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag) or tag.attrs is None:
            continue
        classes = " ".join(tag.get("class", []))
        tag_id = tag.get("id") or ""
        if NOISE_CLASSES.search(classes) or NOISE_CLASSES.search(tag_id):
            tag.decompose()

    # Collapse whitespace
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines()]
    cleaned = "\n".join(ln for ln in lines if ln)

    # Truncate to ~12 000 chars to stay well within context limits
    return cleaned[:12_000]


def analyze_with_claude(client: anthropic.Anthropic, page_text: str) -> str:
    print("Sending to Claude for analysis…", flush=True)
    full_response = []

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[
            {
                "role": "user",
                "content": PMM_PROMPT.format(page_text=page_text),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response.append(text)

    print()  # newline after streamed output
    return "".join(full_response)


def save_output(url: str, analysis: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(url).netloc.lower()).strip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"output-{slug}-{timestamp}.md"
    outpath = Path(filename)

    content = f"## Competitor Page Decoder: {url}\n\n{analysis}\n"
    outpath.write_text(content, encoding="utf-8")
    return outpath


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 decode.py <URL>")

    url = sys.argv[1]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    api_key = load_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    print(f"Fetching {url}…")
    html = fetch_page(url)

    print("Extracting visible text…")
    page_text = extract_text(html)
    print(f"Extracted {len(page_text):,} characters.\n")

    analysis = analyze_with_claude(client, page_text)

    outpath = save_output(url, analysis)
    print(f"\nSaved → {outpath}")


if __name__ == "__main__":
    main()
