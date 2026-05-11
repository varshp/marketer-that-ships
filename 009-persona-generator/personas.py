import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import anthropic

INPUTS_DIR = Path(__file__).parent.parent / "inputs"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

PROMPT_TEMPLATE = """You are a senior PMM building evidence-based buyer personas for {company}.

Do not invent personas from general knowledge.
Derive every attribute from the source materials:
- Review data reveals who is buying and why
- Job postings reveal who they are selling to
- 10-K / 20-F reveals how they describe buyers
- Competitor page reveals who they target

For each persona generate:

PERSONA NAME: (a real job title, not a cute name)

EVIDENCE BASE:
Which source files informed this persona and what specific signals revealed them

WHO THEY ARE:
- Job title and seniority
- Company size and type
- Day to day reality in 2-3 sentences
- What they read, follow, care about

WHAT THEY ARE TRYING TO DO:
- Primary job to be done
- Secondary jobs to be done
- What success looks like to them

WHY THEY BUY:
- Trigger event that starts the search
- What they are moving away from
- What they are moving toward
- How they justify it internally

WHY THEY DON'T BUY:
- Top objection
- What makes them stall
- Who else is in the room blocking the deal

EXACT LANGUAGE THEY USE:
- 3-5 direct quotes or phrases from source data
- How they describe the problem in their own words
- How they describe the ideal solution

WHERE TO REACH THEM:
- Channels they trust
- Content formats that work
- Communities they participate in

HORIZON RELEVANCE:
- Which positioning horizon (H1/H2/H3) speaks to this persona most directly and why

Generate 2-3 personas. Only include a persona if there is sufficient evidence in the source
materials to populate at least 70% of the fields. Do not pad with assumptions.

Flag any field populated from inference rather than direct evidence with (inferred).

After all personas, add:

SEGMENT PRIORITY RECOMMENDATION:
Which persona represents the highest-value segment to prioritise right now and why.
Base this only on evidence in the source materials — growth signals, strategic investment,
GTM motion, and competitive window. Do not use general market knowledge.

---

SOURCE MATERIALS:

{source_materials}"""

# ---------------------------------------------------------------------------
# Reflection schema
# ---------------------------------------------------------------------------

REFLECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "object",
            "properties": {
                "evidence_grounding": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
                "objection_specificity": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
                "segment_priority": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
            },
            "required": ["evidence_grounding", "objection_specificity", "segment_priority"],
            "additionalProperties": False,
        },
        "revision_instructions": {"type": "string"},
    },
    "required": ["scores", "revision_instructions"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_env():
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"Error: ANTHROPIC_API_KEY not found in {ENV_FILE} or environment", file=sys.stderr)
        sys.exit(1)
    return api_key


def read_input_files(company: str) -> dict[str, str]:
    pattern = f"{company}-*.md"
    files = sorted(INPUTS_DIR.glob(pattern))
    if not files:
        print(f"Error: No files matching '{pattern}' in {INPUTS_DIR}", file=sys.stderr)
        sys.exit(1)
    return {f.name: f.read_text() for f in files}


def build_source_materials(source_files: dict[str, str]) -> str:
    return "\n\n".join(
        f"### FILE: {name}\n\n{content}" for name, content in source_files.items()
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_personas(company: str, source_files: dict[str, str], api_key: str) -> str:
    source_materials = build_source_materials(source_files)

    prompt = PROMPT_TEMPLATE.format(
        company=company.capitalize(),
        source_materials=source_materials,
    )

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Generating personas for {company} from {len(source_files)} source file(s)...")
    print(f"Files: {', '.join(source_files.keys())}")
    print("Streaming response from Claude...")

    output_parts = []
    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system="You are a senior product marketing manager. Be precise, evidence-driven, and direct. Use only what the data shows.",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            output_parts.append(text)

    print()
    return "".join(output_parts)


# ---------------------------------------------------------------------------
# Reflection loop
# ---------------------------------------------------------------------------

def reflect_personas(client: anthropic.Anthropic, content: str, source_materials: str) -> dict:
    """Score persona output against three criteria. Returns structured scores + feedback."""

    prompt = (
        "Score this buyer persona document as a rigorous quality reviewer.\n\n"
        f"PERSONA DOCUMENT:\n{content}\n\n"
        "Score each criterion 1–10 using the source materials as the reference:\n\n"
        "1. EVIDENCE GROUNDING — Is every field populated from source material? "
        "Deduct for fields that rely on general B2B assumptions not grounded in the data.\n\n"
        "2. OBJECTION SPECIFICITY — Are the objections in WHY THEY DON'T BUY specific to "
        "this company's actual product gaps and competitive position? "
        "Generic SaaS objections (e.g. 'concerns about ROI', 'change management') score low.\n\n"
        "3. SEGMENT PRIORITY — Is the SEGMENT PRIORITY RECOMMENDATION present, does it name "
        "a specific persona, and is it justified with concrete evidence from the source materials "
        "(growth signals, strategic investment, GTM motion, competitive window)?\n\n"
        f"SOURCE MATERIALS:\n{source_materials}"
    )

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1500,
        system="You are a senior product marketing manager. Be precise, evidence-driven, and direct.",
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": REFLECTION_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def revise_personas(
    client: anthropic.Anthropic,
    content: str,
    reflection: dict,
    source_materials: str,
) -> str:
    """Stream-generate a revised persona document addressing reflection feedback."""

    scores = reflection["scores"]
    score_lines = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v['score']}/10\n  Issue: {v['feedback']}"
        for k, v in scores.items()
    )

    prompt = (
        "Revise this buyer persona document to fix every flagged issue. "
        "Return only the revised persona document.\n\n"
        f"ORIGINAL:\n{content}\n\n"
        f"REVIEW SCORES:\n{score_lines}\n\n"
        f"REVISION INSTRUCTIONS: {reflection['revision_instructions']}\n\n"
        f"SOURCE MATERIALS:\n{source_materials}"
    )

    output_parts = []
    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=8000,
        system="You are a senior product marketing manager. Be precise, evidence-driven, and direct. Use only what the data shows.",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            output_parts.append(text)

    print()
    return "".join(output_parts)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

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


def save_output(company: str, content: str, scores: dict, revision_count: int, quality_flag: str | None) -> Path:
    output_path = Path(__file__).parent / f"{company}-personas.md"
    header = f"# {company.capitalize()} Buyer Personas\n\n*Generated by personas.py from source intelligence files.*\n\n---\n\n"
    frontmatter = build_frontmatter(scores, revision_count, quality_flag)
    output_path.write_text(frontmatter + header + content)
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate evidence-based buyer personas from intelligence files.")
    parser.add_argument("--company", required=True, help="Company name (e.g. notion, hubspot)")
    args = parser.parse_args()

    company = args.company.lower()
    api_key = load_env()
    source_files = read_input_files(company)
    source_materials = build_source_materials(source_files)

    # ── 1. Generate ───────────────────────────────────────────────────────────
    personas = generate_personas(company, source_files, api_key)
    initial_content = personas

    client = anthropic.Anthropic(api_key=api_key)

    # ── 2. Reflect + revise loop (max 2 revisions) ────────────────────────────
    final_reflection: dict | None = None
    revision_count = 0
    quality_flag: str | None = None

    while revision_count < 2:
        print(f"\n  Reflecting on personas (pass {revision_count + 1})...")
        reflection = reflect_personas(client, personas, source_materials)
        final_reflection = reflection
        scores = reflection["scores"]
        low = [k for k, v in scores.items() if v["score"] < 7]

        score_str = "  |  ".join(
            f"{k.replace('_', ' ').title()}: {v['score']}/10"
            for k, v in scores.items()
        )
        print(f"  Scores: {score_str}")

        if not low:
            print("  ✓ All criteria ≥ 7 — approved")
            break

        print(f"  Below 7: {', '.join(low)}")
        print("\nRevising personas...\n")
        personas = revise_personas(client, personas, reflection, source_materials)
        revision_count += 1

    # Final reflection pass after max revisions
    if revision_count == 2:
        print("\n  Reflecting on personas (final pass after max revisions)...")
        final_reflection = reflect_personas(client, personas, source_materials)
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
        initial_path = Path(__file__).parent / f"{company}-personas-initial.md"
        initial_path.write_text(initial_content)
        print(f"\nSaved initial version: {initial_path}")

    # ── 3. Save final output ──────────────────────────────────────────────────
    final_scores = final_reflection["scores"] if final_reflection else {}
    output_path = save_output(company, personas, final_scores, revision_count, quality_flag)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
