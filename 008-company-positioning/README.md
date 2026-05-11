# 008 — Company Positioning Arc Generator

Reads competitive intelligence files and generates a three-horizon positioning arc for a company using Claude.

## What it does

`arc.py` takes a company name, finds all matching intelligence files in the shared `../inputs/` folder, pulls the competitive quadrant rationale from experiment 007, and asks Claude to act as a senior PMM advisor to the company's CMO. The output is a structured positioning arc covering:

- **Current state** — inferred positioning, the gap between claimed and perceived, biggest vulnerability
- **Horizon 1 (0–6 months)** — defend and sharpen: what to stop/start saying, available proof points
- **Horizon 2 (6–12 months)** — anticipate and move: what to ship, which competitor to watch, whitespace to claim
- **Horizon 3 (12–18 months)** — own the category: the single bet, the risk, the fallback

The script reads exact language from source materials and produces specific, actionable output — not generic strategy advice.

## Setup

```bash
cd experiments/008-company-positioning
pip install -r requirements.txt
```

`ANTHROPIC_API_KEY` is loaded from the `.env` file at the root of this repo. Copy `.env.example` to `.env` and fill in your key. You can also export it directly:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
# Real company (requires ../inputs/notion-*.md files)
python3 arc.py --company notion

# Fictional Stackly company (self-contained, no real data needed)
python3 arc.py --company stackly \
  --inputs synthetic/inputs \
  --quadrant synthetic/axes-rationale.md
```

Output is written to `{company}-positioning-arc.md` in this folder.

## Input file naming

Intelligence files follow the pattern:

```
{company}-{experiment}.md
```

Where the experiment suffix indicates the source:
- `-002` — G2 review synthesis
- `-004` — Competitor page decoder
- `-005` — Job posting analysis
- `-006` — 10-K / earnings analysis

The script picks up all matching files automatically. Add more files and they are included in the next run.

## Options

```
--company NAME      Company slug (required). Matches filename prefix.
--inputs DIR        Folder of .md intelligence files. Default: ../inputs
--quadrant FILE     Path to axes-rationale.md. Default: ../007-competitive-quadrant/axes-rationale.md
--model MODEL       Claude model. Default: claude-opus-4-6
```

## Synthetic data

The `synthetic/` folder contains fictional input files for a made-up company called **Stackly** — a mid-market project management tool. Use these to try the script without any real company data:

```
synthetic/
  inputs/
    stackly-002.md   G2 review synthesis
    stackly-004.md   Competitor page decoder
    stackly-005.md   Job posting analysis
  axes-rationale.md  Competitive quadrant rationale
```

Run it:

```bash
python3 arc.py --company stackly \
  --inputs synthetic/inputs \
  --quadrant synthetic/axes-rationale.md
```

Output: `stackly-positioning-arc.md`

## Pipeline

This experiment is part of a series:

| Experiment | What it produces |
|---|---|
| 002 — G2 Review Miner | Customer voice: complaints, praise, exact language |
| 004 — Competitor Page Decoder | Inferred positioning from website |
| 005 — Job Posting Analyzer | Strategic intent from hiring signals |
| 006 — 10-K / Earnings Analyzer | Financial framing and risk signals |
| 007 — Competitive Quadrant | Visual positioning vs. competitors |
| **008 — Positioning Arc** | **Three-horizon strategic arc (this experiment)** |
