# 10-K Analyser

Pulls the most recent 10-K filing for any publicly traded US company from SEC EDGAR and runs it through Claude for PMM competitive intelligence.

No API keys needed for EDGAR — it's a public endpoint. You need an Anthropic API key for Claude.

## What it produces

```
## 10-K Signal Report: CRM

### How they describe their market and customers
### Where they're investing vs pulling back
### Risk factors a competitor PMM should know
### Competitors they name and how they frame them
### Narrative shifts from prior year
### PMM actions
```

Saved as a markdown file: `crm-10k-20250414.md`

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the root of this repo and fill in your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

```bash
python3 analyse.py CRM      # Salesforce
python3 analyse.py MSFT     # Microsoft
python3 analyse.py NOW      # ServiceNow
python3 analyse.py ORCL     # Oracle
python3 analyse.py HUBS     # HubSpot
```

The script prints streaming output to the terminal and saves the full report as a markdown file in the current directory.

## How it works

1. **CIK lookup** — fetches `https://www.sec.gov/files/company_tickers.json` and finds the company's EDGAR CIK number
2. **Filings index** — calls `https://data.sec.gov/submissions/CIK{cik}.json` to find the most recent 10-K accession number
3. **Document fetch** — downloads the primary filing document from `https://www.sec.gov/Archives/edgar/data/...`
4. **HTML stripping** — cleans the filing to plain text (most 10-Ks are filed as HTML)
5. **Claude analysis** — sends up to 200,000 characters to `claude-opus-4-6` with a PMM analysis prompt
6. **Output** — streams the report to the terminal and saves it as a markdown file

SEC EDGAR requires a `User-Agent` header identifying the requester — this is set to `gtm-signal-miner hello@varshaa.dev` per their guidelines.

## Notes

- 10-K documents can be very large (500+ pages). The script caps input at 200,000 characters, which covers the narrative sections most useful for PMM analysis (business description, strategy, risk factors, MD&A).
- Prompt caching is enabled — if you run the same ticker twice, the second call is significantly cheaper.
- Output files are named `{ticker}-10k-{date}.md` in the working directory.

## Sample output

See `sample-output.md` for a realistic example using Salesforce (CRM).
