#!/usr/bin/env python3
"""
G2 Review Miner — Experiment 002
GTM AI Toolkit for Product Marketing Managers

Mines competitor G2 reviews to extract messaging intelligence.
Falls back to Capterra automatically if G2 blocks scraping with JavaScript.
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from firecrawl import FirecrawlApp

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

OUTPUT_DIR = Path(__file__).parent / "outputs"


def build_capterra_url(g2_url: str) -> str | None:
    """Extract product slug from G2 URL and build Capterra fallback URL."""
    match = re.search(r"/products/([^/]+)/reviews", g2_url)
    if match:
        slug = match.group(1)
        return f"https://www.capterra.com/p/{slug}/reviews"
    return None


def _scrape(app: FirecrawlApp, url: str) -> str:
    result = app.scrape(
        url,
        formats=["markdown"],
        only_main_content=True,
        wait_for=3000,
    )
    return getattr(result, "markdown", None) or ""


def scrape_reviews(url: str) -> tuple[str, str]:
    """Scrape reviews, falling back to Capterra if G2 is blocked.

    Returns (content, source) where source is 'g2' or 'capterra'.
    """
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    print(f"Scraping reviews from: {url}")
    content = _scrape(app, url)

    g2_blocked = len(content) < 500 or "enable js" in content.lower()

    if not g2_blocked:
        print("Source used: G2")
        print(f"Scraped {len(content):,} characters of review content")
        return content, "g2"

    # G2 returned insufficient content — switch to Capterra
    capterra_url = build_capterra_url(url)
    if not capterra_url:
        raise ValueError(
            "G2 returned insufficient content and no Capterra URL could be built from the G2 URL."
        )

    print(f"G2 returned insufficient content (likely JS-blocked). Switching to Capterra automatically.")
    print(f"Scraping reviews from: {capterra_url}")
    content = _scrape(app, capterra_url)

    if not content:
        raise ValueError("No content scraped from either G2 or Capterra. Check the product slug.")

    print("Source used: Capterra")
    print(f"Scraped {len(content):,} characters of review content")
    return content, "capterra"


def extract_product_name(url: str, content: str) -> str:
    """Extract product name from URL or scraped content."""
    # G2 URL pattern: /products/{slug}/reviews
    match = re.search(r"/products/([^/]+)/reviews", url)
    if match:
        slug = match.group(1)
        return slug.replace("-", " ").title()

    # Capterra URL pattern: /p/{slug}/reviews
    match = re.search(r"/p/([^/]+)/reviews", url)
    if match:
        slug = match.group(1)
        return slug.replace("-", " ").title()

    # Fallback: first meaningful line of content
    for line in content.split("\n")[:15]:
        stripped = line.strip().lstrip("#").strip()
        if stripped and len(stripped) < 60 and not stripped.startswith("http"):
            return stripped

    return "Unknown Product"


def analyze_reviews(content: str, product_name: str, source: str) -> str:
    """Use Claude to analyze reviews and extract messaging intelligence."""
    print(f"Analyzing reviews with Claude (claude-opus-4-6)...")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = """You are an expert Product Marketing Manager (PMM) specializing in competitive intelligence.

Your job is to analyze raw review data and surface actionable messaging intelligence that a PMM can use immediately.

Return your analysis in EXACTLY this markdown format — no extra sections, no preamble:

## Competitor: [Product Name]
### Top 5 recurring complaints
1.
2.
3.
4.
5.

### Top 5 recurring praise points
1.
2.
3.
4.
5.

### Exact customer language to use in your messaging
(direct quotes from reviews)

### Positioning gaps to exploit
1.
2.
3.

Analysis guidelines:
- Complaints: Patterns across multiple reviews only. Be specific — not "bad UX" but "users can't find X when they need to Y"
- Praise: What job-to-be-done does this product nail? Name the emotion and the outcome
- Customer language: 5–8 verbatim quotes. These are gold for ad copy, landing pages, and sales decks
- Positioning gaps: Concrete weaknesses your product can directly counter. Frame each as "They can't do X, which means you can win on Y"
- Everything must be grounded in the actual reviews — no fabrication"""

    # Trim content to fit context window while keeping max signal
    review_content = content[:60000]

    source_label = "G2" if source == "g2" else "Capterra"
    user_message = f"""Analyze these {source_label} reviews for {product_name} and return the messaging intelligence report.

--- BEGIN {source_label.upper()} REVIEWS ---
{review_content}
--- END {source_label.upper()} REVIEWS ---"""

    print("Sending to Claude... (streaming response)")

    result_text = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            result_text += text

    print()  # newline after streaming
    return result_text


def save_output(content: str, product_name: str) -> Path:
    """Save the analysis as a markdown file named after the competitor."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    slug = product_name.lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    filepath = OUTPUT_DIR / f"{slug}.md"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def mine_reviews(url: str) -> str:
    """End-to-end pipeline: scrape → analyze → save."""
    if "g2.com" not in url and "capterra.com" not in url:
        print("Warning: URL doesn't appear to be a G2 or Capterra page. Proceeding anyway.")

    # Step 1: Scrape (with automatic Capterra fallback)
    content, source = scrape_reviews(url)

    # Step 2: Identify product (use original G2 URL for slug extraction when possible)
    product_name = extract_product_name(url, content)
    print(f"Product identified: {product_name}")

    # Step 3: Analyze with Claude
    analysis = analyze_reviews(content, product_name, source)

    # Step 4: Save
    filepath = save_output(analysis, product_name)
    print(f"\nOutput saved: {filepath}")

    return analysis


def main():
    if len(sys.argv) < 2:
        print("Usage: python g2_miner.py <g2-reviews-url>")
        print("Example: python g2_miner.py https://www.g2.com/products/acme/reviews")
        sys.exit(1)
    url = sys.argv[1]

    print("\nG2 Review Miner — GTM AI Toolkit Experiment 002")
    print("=" * 52)

    try:
        mine_reviews(url)
        print("\nDone.")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
