# 002 — G2 Review Miner

**GTM AI Toolkit · Experiment 002**

Mines competitor G2 reviews and extracts structured messaging intelligence for Product Marketing Managers.

## What it does

1. Takes a G2 product reviews URL
2. Scrapes all visible reviews via Firecrawl (handles JS rendering)
3. Sends the review corpus to Claude Opus 4.6 for analysis
4. Returns a PMM-ready markdown report saved to `outputs/`

## Output format

```markdown
## Competitor: [Product Name]
### Top 5 recurring complaints
### Top 5 recurring praise points
### Exact customer language to use in your messaging
### Positioning gaps to exploit
```

See `sample-output.md` for a realistic example.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the root of this repo and fill in your keys:

```
ANTHROPIC_API_KEY=...
FIRECRAWL_API_KEY=...
```

## Usage

```bash
# Analyze a competitor
python g2_miner.py https://www.g2.com/products/notion/reviews

# Default (runs Notion as a test)
python g2_miner.py
```

Output is saved to `outputs/<competitor-name>.md`.

## How it works

**Scraping:** Firecrawl renders the G2 page (including JS-loaded reviews) and returns clean markdown, stripping nav, ads, and boilerplate.

**Analysis:** Claude Opus 4.6 with adaptive thinking processes up to 60K characters of review content. The model is prompted to act as a PMM analyst — identifying complaint patterns, praise themes, verbatim quotes for copy, and exploitable positioning gaps.

**Output:** Saved as `outputs/<slug>.md` so you can version-control competitor intelligence over time.

## Tech stack

- Python 3.10+
- [Firecrawl](https://firecrawl.dev) for JS-rendered scraping
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) with Claude Opus 4.6
- `python-dotenv` for API key management
