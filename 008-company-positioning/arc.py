#!/usr/bin/env python3
"""
Company Positioning Arc Generator (experiment 008)

Reads competitive intelligence from the shared inputs folder and the
007-competitive-quadrant axes rationale, then asks Claude to produce
three outputs in a single API call.

A reflection loop scores each section against three criteria and revises
it if any score is below 7/10 (max 2 revisions). Initial and final
versions are saved; scores appear in output file frontmatter.

Outputs:
  {company}-positioning-arc.md    Full strategic memo
  {company}-competitor-brief.md   Structured competitive extract (input for 010-013)
  {company}-content-brief.md      Content creation brief (input for 010-013)

Run:
    python3 arc.py --company notion
    python3 arc.py --company stackly --inputs synthetic/inputs --quadrant synthetic/axes-rationale.md
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HERE = Path(__file__).parent
DEFAULT_INPUTS   = HERE / "../inputs"
DEFAULT_QUADRANT = HERE / "../007-competitive-quadrant/axes-rationale.md"
ENV_FILE         = Path(__file__).resolve().parent.parent / ".env"

# Delimiter Claude must use between sections — chosen to be unambiguous
SECTION_RE = re.compile(r"^%%SECTION\s+(\d+)%%\s*$", re.MULTILINE)

SECTION_NAMES = {
    1: "full strategic memo",
    2: "competitor brief",
    3: "content brief",
}

# ---------------------------------------------------------------------------
# Reflection schema
# ---------------------------------------------------------------------------

REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "claim_traceability": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
                "strategic_specificity": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
                "horizon_differentiation": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
            },
            "required": ["claim_traceability", "strategic_specificity", "horizon_differentiation"],
            "additionalProperties": False,
        },
        "revision_instructions": {"type": "string"},
    },
    "required": ["scores", "revision_instructions"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate positioning arc, competitor brief, and content brief in one call."
    )
    parser.add_argument(
        "--company",
        required=True,
        metavar="NAME",
        help="Company slug to process (matches filename prefix, e.g. 'notion')",
    )
    parser.add_argument(
        "--inputs",
        type=Path,
        default=DEFAULT_INPUTS,
        metavar="DIR",
        help=f"Folder of .md intelligence files (default: {DEFAULT_INPUTS})",
    )
    parser.add_argument(
        "--quadrant",
        type=Path,
        default=DEFAULT_QUADRANT,
        metavar="FILE",
        help=f"Competitive quadrant axes-rationale.md (default: {DEFAULT_QUADRANT})",
    )
    parser.add_argument(
        "--model",
        default="claude-opus-4-6",
        metavar="MODEL",
        help="Claude model to use (default: claude-opus-4-6)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env() -> None:
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)


def read_inputs(inputs_dir: Path, company: str) -> list[tuple[str, str]]:
    inputs_dir = inputs_dir.resolve()
    if not inputs_dir.is_dir():
        sys.exit(f"ERROR: inputs directory not found: {inputs_dir}")

    files = sorted(inputs_dir.glob(f"{company.lower()}-*.md"))
    if not files:
        sys.exit(
            f"ERROR: no files found for '{company}' in {inputs_dir}\n"
            f"       Expected files matching: {company.lower()}-*.md"
        )
    return [(f.name, f.read_text(encoding="utf-8")) for f in files]


def read_quadrant(quadrant_path: Path) -> str:
    quadrant_path = quadrant_path.resolve()
    if not quadrant_path.exists():
        sys.exit(f"ERROR: quadrant file not found: {quadrant_path}")
    return quadrant_path.read_text(encoding="utf-8")


def parse_sections(response: str) -> dict[int, str]:
    """Split response on %%SECTION N%% markers, return {section_number: content}."""
    parts = SECTION_RE.split(response)
    # parts alternates: [pre-section-text, "1", content1, "2", content2, ...]
    sections: dict[int, str] = {}
    it = iter(parts)
    next(it)  # discard anything before the first marker
    for num_str, content in zip(it, it):
        sections[int(num_str)] = content.strip()
    return sections


def build_source_context(
    inputs: list[tuple[str, str]],
    quadrant: str,
    memo: str | None = None,
) -> str:
    parts = [f"### Source: {name}\n\n{content}" for name, content in inputs]
    parts.append(f"### Competitive quadrant\n\n{quadrant}")
    if memo:
        parts.append(f"### Positioning arc memo\n\n{memo}")
    return "\n\n---\n\n".join(parts)


def build_frontmatter(scores: dict, revision_count: int, quality_flag: str | None = None) -> str:
    lines = [
        "---",
        "scores:",
    ]
    for k, v in scores.items():
        lines.append(f"  {k}: {v['score']}")
    if revision_count:
        lines.append(f"revisions: {revision_count}")
    if quality_flag:
        lines.append(f'quality_flag: "{quality_flag}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def build_prompt(company: str, inputs: list[tuple[str, str]], quadrant: str, today: str) -> str:
    source_parts = []
    for filename, content in inputs:
        source_parts.append(f"### Source file: {filename}\n\n{content}")
    source_parts.append(f"### Competitive quadrant analysis\n\n{quadrant}")
    sources_block = "\n\n---\n\n".join(source_parts)

    return f"""You are a senior PMM acting as strategic advisor to the CMO of {company}.
Today's date is {today}.

You have been provided with:
- Customer voice data (G2 reviews)
- Current positioning inferred from their website
- Strategic intent inferred from job postings
- Competitive quadrant analysis showing where {company} sits vs competitors

Produce all three sections below. Separate them with exactly these markers on their own lines:

%%SECTION 1%%
%%SECTION 2%%
%%SECTION 3%%

Do not include any text before %%SECTION 1%%.

---

%%SECTION 1%%

Write a three-horizon positioning arc strategic memo.

CURRENT STATE
- Inferred positioning from website
- Gap between claimed and perceived positioning (what they say vs what customers say)
- Biggest competitive vulnerability right now

HORIZON 1 (0-6 months): Defend and sharpen
- Core positioning claim
- Proof points available today
- What to stop saying immediately
- What to start saying immediately

HORIZON 2 (6-12 months): Anticipate and move
- Core positioning claim
- What must ship to support this
- Which competitor move to anticipate
- Whitespace to start claiming now

HORIZON 3 (12-18 months): Own the category
- Core positioning claim
- The single bet that has to be true
- Risk if this positioning fails
- Fallback position if it does

Use exact language from source materials. Be specific. No generic advice.

---

%%SECTION 2%%

Extract a competitor brief from the memo above.
Return structured markdown with field names in ALL_CAPS followed by a colon.
Bullet lists: dash prefix, two-space indent. Rules: one-sentence fields are one sentence only.
Max 3 bullets per list. Use exact language from the memo. No preamble or closing notes.

COMPANY: (title-cased company name)
DATE: (today's date as YYYY-MM-DD)
CURRENT_POSITIONING: (one sentence)
POSITIONING_GAP: (one sentence)
H1_CLAIM: (one sentence)
H1_PROOF_POINTS:
  - (bullet)
  - (bullet)
  - (bullet)
H1_STOP_SAYING:
  - (bullet)
  - (bullet)
  - (bullet)
H1_START_SAYING:
  - (bullet)
  - (bullet)
  - (bullet)
H2_CLAIM: (one sentence)
H2_KEY_MOVE: (one sentence)
H2_WHITESPACE: (one sentence)
H3_CLAIM: (one sentence)
H3_BET: (one sentence)
H3_FALLBACK: (one sentence)
PRIMARY_AUDIENCE: (one sentence)
KEY_MESSAGES:
  - (bullet)
  - (bullet)
  - (bullet)
PROOF_POINTS:
  - (bullet)
  - (bullet)
  - (bullet)
COMPETITIVE_VULNERABILITY: (one sentence)

---

%%SECTION 3%%

Extract a content brief from the memo above.
Same format rules as Section 2.

COMPANY: (title-cased company name)
DATE: (today's date as YYYY-MM-DD)
AUDIENCE: (one sentence — who the content is for)
HERO_MESSAGE: (one sentence — the single message all content must reinforce)
SUPPORTING_MESSAGES:
  - (bullet)
  - (bullet)
  - (bullet)
PROOF_POINTS:
  - (bullet — use exact customer language where available)
  - (bullet)
  - (bullet)
TONE: (one sentence — the voice and register content should use)
WHAT_TO_AVOID:
  - (bullet)
  - (bullet)
  - (bullet)
H1_CAMPAIGN_ANGLE: (one sentence — the content angle for the 0-6 month horizon)
H2_CAMPAIGN_ANGLE: (one sentence — the content angle for the 6-12 month horizon)
H3_CAMPAIGN_ANGLE: (one sentence — the content angle for the 12-18 month horizon)

---

Source materials:

{sources_block}"""


# ---------------------------------------------------------------------------
# Reflection loop helpers
# ---------------------------------------------------------------------------

def reflect_section(
    client: anthropic.Anthropic,
    model: str,
    section_name: str,
    content: str,
    source_context: str,
) -> dict:
    """Score a section against three criteria. Returns structured scores + feedback."""

    prompt = (
        f"Score this {section_name} as a rigorous quality reviewer.\n\n"
        f"SECTION CONTENT:\n{content}\n\n"
        "Score each criterion 1–10 using the source materials as the reference:\n\n"
        "1. CLAIM TRACEABILITY — Is every claim grounded in the source materials? "
        "Deduct for generic advice, invented proof points, or claims not supported by the data.\n\n"
        "2. STRATEGIC SPECIFICITY — Are recommendations specific to this company, or could "
        "they apply to any B2B SaaS company? Vague advice scores low.\n\n"
        "3. HORIZON DIFFERENTIATION — Are H1, H2, H3 genuinely distinct strategic moves, "
        "or are they variations of the same message rephrased? "
        "Each horizon must name a meaningfully different positioning claim.\n\n"
        f"SOURCE MATERIALS:\n{source_context}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": REFLECTION_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def revise_section(
    client: anthropic.Anthropic,
    model: str,
    section_name: str,
    content: str,
    reflection: dict,
    source_context: str,
) -> str:
    """Generate a revised version of the section addressing reflection feedback."""

    scores = reflection["scores"]
    score_lines = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v['score']}/10\n  Issue: {v['feedback']}"
        for k, v in scores.items()
    )

    prompt = (
        f"Revise this {section_name} to fix every flagged issue. Return only the revised content.\n\n"
        f"ORIGINAL:\n{content}\n\n"
        f"REVIEW SCORES:\n{score_lines}\n\n"
        f"REVISION INSTRUCTIONS: {reflection['revision_instructions']}\n\n"
        f"SOURCE MATERIALS:\n{source_context}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


def run_reflection_loop(
    client: anthropic.Anthropic,
    model: str,
    section_num: int,
    content: str,
    source_context: str,
    out_path: Path,
) -> tuple[str, dict, int, str | None]:
    """
    Run reflect → revise loop for one section. Max 2 revisions.
    Saves initial version if any revision happens.
    Returns (final_content, final_scores, revision_count, quality_flag).
    """
    section_name = SECTION_NAMES[section_num]
    final_reflection: dict | None = None
    revision_count = 0
    initial_content = content

    while revision_count < 2:
        print(f"\n  Reflecting on {section_name} (pass {revision_count + 1})...")
        reflection = reflect_section(client, model, section_name, content, source_context)
        final_reflection = reflection
        scores = reflection["scores"]
        low = [k for k, v in scores.items() if v["score"] < 7]

        score_str = "  |  ".join(
            f"{k.replace('_', ' ').title()}: {v['score']}/10"
            for k, v in scores.items()
        )
        print(f"  Scores: {score_str}")

        if not low:
            print(f"  ✓ All criteria ≥ 7 — approved")
            break

        print(f"  Below 7: {', '.join(low)}")
        print(f"  Revising {section_name}...")
        content = revise_section(client, model, section_name, content, reflection, source_context)
        revision_count += 1

    # If we hit max revisions, do a final reflection pass on the revised content
    quality_flag: str | None = None
    if revision_count == 2:
        print(f"\n  Reflecting on {section_name} (final pass after max revisions)...")
        final_reflection = reflect_section(client, model, section_name, content, source_context)
        final_scores = final_reflection["scores"]
        still_low = [k for k, v in final_scores.items() if v["score"] < 7]
        score_str = "  |  ".join(
            f"{k.replace('_', ' ').title()}: {v['score']}/10"
            for k, v in final_scores.items()
        )
        print(f"  Scores: {score_str}")
        if still_low:
            quality_flag = f"below-threshold after max revisions: {', '.join(still_low)}"
            print(f"  ⚠ Saved with quality flag — {quality_flag}")
        else:
            print("  ✓ Approved after final pass")

    # Save initial version if content changed
    if revision_count > 0:
        initial_path = out_path.with_name(out_path.stem + "-initial.md")
        initial_path.write_text(initial_content, encoding="utf-8")
        print(f"  Saved initial: {initial_path.name}")

    return content, final_reflection["scores"] if final_reflection else {}, revision_count, quality_flag


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args    = parse_args()
    company = args.company.lower()
    today   = date.today().isoformat()

    load_env()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit(
            "ERROR: ANTHROPIC_API_KEY not set.\n"
            f"       Add it to {ENV_FILE} or export it before running."
        )

    inputs   = read_inputs(args.inputs, company)
    quadrant = read_quadrant(args.quadrant)

    print(f"Company:  {company}")
    print(f"Inputs:   {args.inputs.resolve()}")
    print(f"Files:    {[name for name, _ in inputs]}")
    print(f"Quadrant: {args.quadrant.resolve()}")
    print(f"Model:    {args.model}")
    print()
    print("Calling Claude API (generating all three sections)...")

    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_prompt(company, inputs, quadrant, today)

    message = client.messages.create(
        model=args.model,
        max_tokens=10000,
        messages=[{"role": "user", "content": prompt}],
    )

    response = message.content[0].text
    sections = parse_sections(response)

    missing = [n for n in (1, 2, 3) if n not in sections]
    if missing:
        (HERE / f"{company}-raw-response.txt").write_text(response, encoding="utf-8")
        sys.exit(
            f"ERROR: response is missing section(s) {missing}.\n"
            f"Raw response saved to {HERE / f'{company}-raw-response.txt'}"
        )

    output_paths = {
        1: HERE / f"{company}-positioning-arc.md",
        2: HERE / f"{company}-competitor-brief.md",
        3: HERE / f"{company}-content-brief.md",
    }

    print(f"\nTokens (generation):  in={message.usage.input_tokens:,}  out={message.usage.output_tokens:,}")

    # ── Reflection loop for each section ────────────────────────────────────

    # Build source context (used for sections 2 & 3 after section 1 is finalized)
    base_source_context = build_source_context(inputs, quadrant)

    final_sections: dict[int, str] = {}

    for num in (1, 2, 3):
        print(f"\n{'─'*60}")
        print(f"  SECTION {num}: {SECTION_NAMES[num].upper()}")
        print(f"{'─'*60}")

        # Sections 2 and 3 are extracted from the memo; include the final memo as context
        if num > 1:
            source_ctx = build_source_context(inputs, quadrant, memo=final_sections[1])
        else:
            source_ctx = base_source_context

        final_content, scores, revision_count, quality_flag = run_reflection_loop(
            client=client,
            model=args.model,
            section_num=num,
            content=sections[num],
            source_context=source_ctx,
            out_path=output_paths[num],
        )

        final_sections[num] = final_content

        # Build frontmatter and write final file
        frontmatter = build_frontmatter(scores, revision_count, quality_flag)
        output_paths[num].write_text(frontmatter + final_content, encoding="utf-8")
        print(f"  Written → {output_paths[num].name}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
