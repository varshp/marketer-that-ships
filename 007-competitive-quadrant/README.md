# 007 — Competitive Quadrant Generator

Reads competitive intelligence `.md` files, asks Claude to derive the two most differentiating axes for the competitive set, and plots a quadrant chart.

## What it does

1. Reads all `.md` files from a folder you point it at
2. Groups them by company (filename prefix before the first `-`)
3. Concatenates each company's files and sends them to Claude with a PMM analysis prompt
4. Claude derives two data-driven axes — not generic "vision vs execution" ones
5. Plots a clean quadrant chart as `quadrant.png`
6. Saves `axes-rationale.md` with axis definitions and per-company placement rationale

## Setup

```bash
pip install -r requirements.txt
```

Requires an `ANTHROPIC_API_KEY`. Copy `.env.example` to `.env` at the root of this repo and fill in your key.

## Run

**With your real data:**
```bash
python3 quadrant.py ./inputs/
```

**With the included synthetic data** (5 fake GTM-AI companies — no real data needed):
```bash
python3 quadrant.py ./synthetic/
```

## Input file format

Files must be named `{company}-{anything}.md`. Everything before the first `-` is treated as the company name. Multiple files per company are concatenated.

```
inputs/
├── salesforce-004.md
├── salesforce-006.md
├── hubspot-004.md
└── hubspot-006.md
```

## Outputs

| File | Description |
|---|---|
| `quadrant.png` | 300 dpi quadrant chart |
| `axes-rationale.md` | Axis definitions + per-company rationale |

## File structure

```
007-competitive-quadrant/
├── quadrant.py          # main script
├── requirements.txt
├── README.md
├── inputs/              # your real competitive intel files
└── synthetic/           # fake companies for demo/testing
    ├── acme-001.md
    ├── bridge-001.md
    ├── cortex-001.md
    ├── drift-001.md
    └── echo-001.md
```
