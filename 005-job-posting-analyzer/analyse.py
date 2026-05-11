#!/usr/bin/env python3
"""
Job Posting Analyser — PMM Signal Report
Uses Ashby (or Greenhouse fallback) + Claude to surface hiring signals.

Usage:
    python3 analyse.py <company-slug>
    python3 analyse.py notion
"""

import sys
import os
import re
import json
import html
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
import anthropic

# ── Load API key ─────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not found. Copy .env.example to .env at the repo root.")
    sys.exit(1)


# ── HTML → plain text ─────────────────────────────────────────────────────────

def strip_html(raw: str) -> str:
    """Strip HTML tags and decode entities, preserving structure."""
    if not raw:
        return ""
    # Preserve newlines from block elements before stripping tags
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|li|h[1-6]|div|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Collapse whitespace/blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ── Job fetchers ──────────────────────────────────────────────────────────────

def fetch_ashby(company: str) -> list[dict]:
    """
    Try Ashby's public posting API.
    Returns a normalised list of {title, department, location, description}.
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            if not raw_jobs:
                return []
            jobs = []
            for j in raw_jobs:
                dept = j.get("department") or {}
                dept_name = dept.get("name", "Unknown") if isinstance(dept, dict) else str(dept)
                loc = j.get("location") or {}
                loc_name = loc.get("name", "") if isinstance(loc, dict) else str(loc)
                desc_html = j.get("descriptionHtml", "") or j.get("description", "")
                jobs.append({
                    "title": j.get("title", "Untitled"),
                    "department": dept_name,
                    "location": loc_name,
                    "description": strip_html(desc_html)[:3000],  # cap per-job chars
                    "employment_type": j.get("employmentType", ""),
                })
            return jobs
    except Exception:
        pass
    return []


def fetch_greenhouse(company: str) -> list[dict]:
    """
    Fallback: Greenhouse boards JSON API.
    Returns the same normalised shape as fetch_ashby.
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            if not raw_jobs:
                return []
            jobs = []
            for j in raw_jobs:
                dept_list = j.get("departments", [])
                dept_name = dept_list[0].get("name", "Unknown") if dept_list else "Unknown"
                loc_list = j.get("offices", [])
                loc_name = loc_list[0].get("name", "") if loc_list else ""
                content_html = j.get("content", "")
                jobs.append({
                    "title": j.get("title", "Untitled"),
                    "department": dept_name,
                    "location": loc_name,
                    "description": strip_html(content_html)[:3000],
                    "employment_type": "",
                })
            return jobs
    except Exception:
        pass
    return []


# ── Job digest builder ────────────────────────────────────────────────────────

def build_digest(company: str, jobs: list[dict], source: str) -> str:
    """Serialise job list into a compact text block for Claude."""
    lines = [
        f"Company: {company}",
        f"Source: {source}",
        f"Total open roles: {len(jobs)}",
        "",
    ]
    for i, j in enumerate(jobs, 1):
        lines.append(f"--- Job {i} ---")
        lines.append(f"Title: {j['title']}")
        lines.append(f"Department: {j['department']}")
        if j.get("location"):
            lines.append(f"Location: {j['location']}")
        if j.get("employment_type"):
            lines.append(f"Type: {j['employment_type']}")
        if j.get("description"):
            lines.append(f"Description snippet:\n{j['description'][:1500]}")
        lines.append("")
    return "\n".join(lines)


# ── Claude analysis ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Product Marketing Manager (PMM) and competitive intelligence analyst.
Your job is to read a company's current open job postings and extract strategic insights that help PMMs understand:
- Where the company is investing and scaling
- What technologies and tools they're betting on
- What strategic priorities are visible in the hiring language
- What competitive signals and product directions this implies
- What PMM actions a competitor or partner should take based on this data

Your analysis must be grounded in the actual text of the job postings. Cite specific patterns,
phrases, and department concentrations as evidence. Do not speculate beyond what the postings show.
Be specific, opinionated, and actionable. Write for a senior PMM audience."""

OUTPUT_FORMAT = """
Return your analysis as a markdown document with this exact structure:

## Job Signal Report: {company}
*{job_count} open roles analysed · Source: {source} · {date}*

---

### Where they're hiring (by department)
List departments and role counts. Call out which are growing fastest based on volume.
Note any unusual concentrations or absences.

---

### Repeated keywords across postings
Pull the 10–15 most-repeated meaningful phrases, terms, or requirements across postings.
Explain what each cluster signals about company direction.

---

### Technology and tool signals
List specific technologies, platforms, frameworks, and tools mentioned.
Group by category (infrastructure, data, product, GTM, etc.).
Note what's absent but expected.

---

### Inferred strategic priorities
Based on the hiring patterns, infer 3–5 strategic bets the company is making.
Each priority should be supported by 2–3 specific signals from the postings.

---

### PMM actions
Give 4–6 concrete, specific actions a PMM at a competing or adjacent company should take
in response to these signals. Be tactical and specific — not "monitor their website"
but "reposition your [X] messaging to counter their push into [Y]."
""".strip()


def analyse_with_claude(company: str, digest: str, job_count: int, source: str) -> str:
    """Send job digest to Claude and return the markdown analysis."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_prompt = (
        f"Here are the current open job postings for **{company}**. "
        "Analyse them for PMM-relevant signals and produce the report as instructed.\n\n"
        f"{digest}\n\n"
        + OUTPUT_FORMAT.format(
            company=company.capitalize(),
            job_count=job_count,
            source=source,
            date=datetime.now().strftime("%B %d, %Y"),
        )
    )

    print(f"  Sending {job_count} jobs to Claude for analysis…", flush=True)

    # Use streaming to handle potentially long analysis output
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        # Show a progress indicator while Claude thinks
        block_types_seen = set()
        for event in stream:
            if hasattr(event, "type"):
                if event.type == "content_block_start":
                    block = getattr(event, "content_block", None)
                    if block and block.type not in block_types_seen:
                        block_types_seen.add(block.type)
                        if block.type == "thinking":
                            print("  [Claude is thinking…]", flush=True)
                        elif block.type == "text":
                            print("  [Claude is writing report…]", flush=True)

        final = stream.get_final_message()

    # Extract the text content
    for block in final.content:
        if block.type == "text":
            return block.text

    return ""


# ── Save output ───────────────────────────────────────────────────────────────

def save_report(company: str, report: str) -> Path:
    """Write report to a markdown file and return the path."""
    filename = f"{company}-job-signal-report.md"
    out_path = Path(filename)
    out_path.write_text(report, encoding="utf-8")
    return out_path


# ── Main ──────────────────────────────────────────────────────────────────────

def extract_slug(arg: str) -> str:
    """Accept a slug or a full jobs.ashbyhq.com / greenhouse.io URL."""
    arg = arg.strip()
    # Ashby: https://jobs.ashbyhq.com/<slug>
    m = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)", arg)
    if m:
        return m.group(1).lower()
    # Greenhouse: https://boards.greenhouse.io/<slug>
    m = re.search(r"boards\.greenhouse\.io/([^/?#]+)", arg)
    if m:
        return m.group(1).lower()
    return arg.lower()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyse.py <company-slug-or-url>")
        print("Example: python3 analyse.py notion")
        print("         python3 analyse.py https://jobs.ashbyhq.com/dash0")
        sys.exit(1)

    company = extract_slug(sys.argv[1])
    print(f"\nJob Signal Analyser — {company}")
    print("=" * 40)

    # 1. Try Ashby
    print("  Fetching from Ashby…", flush=True)
    jobs = fetch_ashby(company)
    source = "Ashby"

    # 2. Fallback to Greenhouse
    if not jobs:
        print("  Ashby returned no results. Trying Greenhouse…", flush=True)
        jobs = fetch_greenhouse(company)
        source = "Greenhouse"

    # 3. Neither worked
    if not jobs:
        print(f"\nCompany not found on Ashby or Greenhouse: '{company}'")
        print("Check the slug spelling and try again.")
        sys.exit(0)

    print(f"  Found {len(jobs)} open roles via {source}.", flush=True)

    # 4. Build digest and analyse
    digest = build_digest(company, jobs, source)
    report = analyse_with_claude(company, digest, len(jobs), source)

    if not report:
        print("Error: Claude returned an empty response.")
        sys.exit(1)

    # 5. Save
    out_path = save_report(company, report)
    print(f"\nReport saved → {out_path}")
    print()


if __name__ == "__main__":
    main()
