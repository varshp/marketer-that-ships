# 009 — Persona Generator

Reads intelligence files for a single company and generates 2-3 evidence-based buyer personas grounded in source data.

## What it does

`personas.py` reads all `{company}-*.md` files from the shared `../inputs/` folder and sends them to Claude with a structured prompt that forces every persona attribute to be traced back to a specific source file and signal. Fields populated from inference (not direct evidence) are flagged with `(inferred)`.

Personas cover:
- Who they are (title, company size, day-to-day reality)
- What they're trying to do (jobs to be done)
- Why they buy and why they don't
- Exact language from source data
- Where to reach them
- Which positioning horizon speaks to them

## Setup

```bash
pip install -r requirements.txt
```

API key is loaded from the `.env` file at the root of this repo (falls back to `ANTHROPIC_API_KEY` env var). Copy `.env.example` to `.env` and fill in your key.

## Usage

```bash
python3 personas.py --company notion
python3 personas.py --company hubspot
python3 personas.py --company asana
```

Output is saved as `{company}-personas.md` in this directory.

## Input files

Input files live in `../inputs/` and follow the naming pattern `{company}-{experiment}.md`:

| Suffix | Source |
|--------|--------|
| `-002` | G2 / review site synthesis |
| `-004` | Competitor page decoder |
| `-005` | Job posting analyzer |
| `-006` | 10-K / 20-F annual report analysis |

The script reads all matching files for the requested company.

## Running with synthetic data (no real inputs needed)

The `synthetic/inputs/` folder contains fake data for a fictional company called **Stackly** — a mid-market project management tool. You can run the full pipeline without any real company data:

```bash
# Copy synthetic inputs to the shared inputs folder
cp synthetic/inputs/stackly-*.md ../inputs/

# Generate personas
python3 personas.py --company stackly
```

Or point the script at a custom inputs directory by modifying `INPUTS_DIR` in `personas.py`.

## Model

Uses `claude-opus-4-7` with adaptive thinking and streaming. Personas stream to the terminal as they generate.
