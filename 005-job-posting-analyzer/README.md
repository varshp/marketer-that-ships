# Job Posting Analyser

Turns a company's public job board into a PMM intelligence report in ~30 seconds.

Pulls job data from **Ashby** (no auth required). Falls back to **Greenhouse** if Ashby returns nothing. Sends everything to **Claude** for structured PMM analysis.

---

## What it produces

```
## Job Signal Report: Notion
### Where they're hiring (by department)
### Repeated keywords across postings
### Technology and tool signals
### Inferred strategic priorities
### PMM actions
```

Saved as `<company>-job-signal-report.md` in the current directory.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy .env.example to .env at the repo root and add ANTHROPIC_API_KEY
```

---

## Run

```bash
python3 analyse.py <company-slug>
```

The slug is the short identifier used in the company's Ashby or Greenhouse URL.

**Examples:**

| Company   | Slug        | Job board URL                         |
|-----------|-------------|---------------------------------------|
| Notion    | `notion`    | jobs.ashbyhq.com/notion               |
| Linear    | `linear`    | linear.ashbyhq.com                    |
| Vercel    | `vercel`    | vercel.com/careers (Greenhouse)        |
| Stripe    | `stripe`    | stripe.com/jobs (Greenhouse)           |
| Figma     | `figma`     | jobs.ashbyhq.com/figma                |

```bash
python3 analyse.py notion
python3 analyse.py linear
python3 analyse.py figma
```

---

## How it works

1. **Ashby** — `GET https://api.ashbyhq.com/posting-api/job-board/{slug}` (public, no auth)
2. **Greenhouse fallback** — `GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true`
3. Jobs are extracted: title, department, location, description
4. A digest is sent to `claude-opus-4-6` with adaptive thinking enabled
5. Claude returns a structured markdown report
6. Report saved as `{slug}-job-signal-report.md`

---

## Notes

- No credentials needed for job data — both APIs are public
- Job descriptions are capped at 1,500 chars each to stay within token limits
- Analysis uses Claude Opus 4.6 with adaptive thinking for deeper inference
- Large job boards (100+ roles) may take 30–60 seconds
