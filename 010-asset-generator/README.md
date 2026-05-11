# 010 — Written Asset Generator

Claude reads source material (positioning brief, content brief, buyer personas) and autonomously decides which written assets to create for each persona. No asset types are pre-specified — Claude derives them from what it reads.

## How it works

```
inputs/{company}-positioning-brief.md  ─┐
inputs/{company}-content-brief.md      ─┤─► [1] Plan: Claude decides asset types per persona
inputs/{company}-personas.md           ─┘

[2] Generate: stream each asset

[3] Reflect: score against 3 criteria
    1. Is every claim traceable to source material?   (0–10)
    2. Does it address the persona's top objection?   (0–10)
    3. Is the CTA specific to this persona's trigger? (0–10)

[4] Revise if any score < 7 — max 2 revisions

[5] Write output/{company}/
    {company}-content-plan.md
    {company}-{persona}-{asset-type}.md   (one per asset)
```

All three source files are loaded once into a cached system prompt (1h TTL) and reused across every API call in the run.

## Usage

```bash
pip install -r requirements.txt
python3 assets.py --company notion
python3 assets.py --company stackly
```

API key is loaded from the `.env` file at the root of this repo (`ANTHROPIC_API_KEY`). Copy `.env.example` to `.env` and fill in your key.

## Output structure

```
output/notion/
  notion-content-plan.md              ← summary of all assets + scores
  notion-director-of-it-cio-one-pager.md
  notion-director-of-it-cio-email-sequence.md
  notion-enterprise-ops-productivity-battle-card.md
  ...
```

Each asset file has a YAML frontmatter block with company, persona, asset type, title, and final reflection scores.

## Synthetic example

`synthetic/stackly/` contains a pre-run example for the fictional company Stackly, showing what the generator produces end-to-end.

## Model

`claude-opus-4-7` throughout.

- Planning: adaptive thinking + structured JSON output (schema-enforced)
- Generation + Revision: streaming, no explicit thinking
- Reflection: structured JSON output (schema-enforced scoring)
