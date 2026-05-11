#!/usr/bin/env python3
"""
Experiment 010: Written Asset Generator

Claude reads source materials and autonomously decides which written assets to
generate for each buyer persona. A reflection loop scores each asset against
three criteria and revises it if any score is below 7/10 (max 2 revisions).

Usage:
    python3 assets.py --company notion
    python3 assets.py --company stackly

Inputs  (../inputs/):
    {company}-positioning-brief.md
    {company}-content-brief.md
    {company}-personas.md

Outputs (output/{company}/):
    {company}-content-plan.md
    {company}-{persona-slug}-{asset-type-slug}.md  (one file per asset)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

INPUTS_DIR = Path(__file__).parent.parent / "inputs"
OUTPUT_DIR = Path(__file__).parent / "output"
MODEL = "claude-opus-4-7"

# ── JSON schemas for structured outputs ──────────────────────────────────────

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "personas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "persona_id":      {"type": "string"},
                    "persona_name":    {"type": "string"},
                    "persona_summary": {"type": "string"},
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "asset_id":   {"type": "string"},
                                "asset_type": {"type": "string"},
                                "title":      {"type": "string"},
                                "rationale":  {"type": "string"},
                            },
                            "required": ["asset_id", "asset_type", "title", "rationale"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["persona_id", "persona_name", "persona_summary", "assets"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["personas"],
    "additionalProperties": False,
}

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
                "objection_addressed": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
                "cta_specificity": {
                    "type": "object",
                    "properties": {
                        "score":    {"type": "integer"},
                        "feedback": {"type": "string"},
                    },
                    "required": ["score", "feedback"],
                    "additionalProperties": False,
                },
            },
            "required": ["claim_traceability", "objection_addressed", "cta_specificity"],
            "additionalProperties": False,
        },
        "revision_instructions": {"type": "string"},
    },
    "required": ["scores", "revision_instructions"],
    "additionalProperties": False,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_source_materials(company: str) -> tuple[str, str, str]:
    positioning    = (INPUTS_DIR / f"{company}-positioning-brief.md").read_text()
    content_brief  = (INPUTS_DIR / f"{company}-content-brief.md").read_text()
    personas       = (INPUTS_DIR / f"{company}-personas.md").read_text()
    return positioning, content_brief, personas


def build_system(company: str, positioning: str, content_brief: str, personas: str) -> list[dict]:
    """
    Single cached system prompt shared across all API calls for a run.
    Cache TTL 1h because a full run over many assets can exceed 5 min.
    """
    return [{
        "type": "text",
        "text": (
            f"You are a B2B content expert working on assets for {company.title()}.\n\n"
            f"POSITIONING BRIEF:\n{positioning}\n\n"
            f"CONTENT BRIEF:\n{content_brief}\n\n"
            f"BUYER PERSONAS:\n{personas}"
        ),
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }]


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len].rstrip("-")


# ── API calls ─────────────────────────────────────────────────────────────────

def plan_assets(client: anthropic.Anthropic, company: str, system: list[dict]) -> dict:
    """Claude autonomously decides which assets to generate per persona."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{
            "role": "user",
            "content": (
                "Based on the source materials, decide which written assets to generate for each persona.\n\n"
                "Guidelines:\n"
                "- Choose 2–3 assets per persona\n"
                "- Match format to where the persona is reachable (their documented channels)\n"
                "- Ground every choice in the persona's buying trigger, top objection, and exact language\n"
                "- Vary formats across personas so the asset mix is diverse\n\n"
                "Asset type examples (not exhaustive): one-pager, executive brief, cold email, "
                "email sequence, battle card, blog post, LinkedIn post, case study outline, "
                "FAQ sheet, ROI narrative, comparison guide."
            ),
        }],
        output_config={"format": {"type": "json_schema", "schema": PLAN_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def generate_asset(
    client: anthropic.Anthropic,
    system: list[dict],
    persona: dict,
    asset: dict,
) -> str:
    """Stream-generate a complete written asset."""

    prompt = (
        f"Write the following asset. Make it complete and ready to publish — no placeholders.\n\n"
        f"TARGET PERSONA: {persona['persona_name']}\n"
        f"{persona['persona_summary']}\n\n"
        f"ASSET TYPE: {asset['asset_type']}\n"
        f"TITLE: {asset['title']}\n"
        f"WHY THIS ASSET: {asset['rationale']}\n\n"
        "Rules:\n"
        "- Every claim must trace back to the source materials\n"
        "- Use the persona's own documented language where possible\n"
        "- Address their top objection directly and specifically\n"
        "- End with a CTA tied to their documented buying trigger, not a generic one\n"
        "- Write as if publishing tomorrow"
    )

    full_text = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            full_text += chunk
    print()
    return full_text


def reflect_on_asset(
    client: anthropic.Anthropic,
    system: list[dict],
    persona: dict,
    asset: dict,
    content: str,
) -> dict:
    """Score the asset against three criteria. Returns structured scores + feedback."""

    prompt = (
        f"Score this asset as a rigorous quality reviewer.\n\n"
        f"PERSONA: {persona['persona_name']}\n"
        f"ASSET TYPE: {asset['asset_type']}\n"
        f"TITLE: {asset['title']}\n\n"
        f"ASSET:\n{content}\n\n"
        "Score each criterion 1–10 using the source materials as the reference:\n\n"
        "1. CLAIM TRACEABILITY — Is every claim grounded in the source docs? "
        "Deduct for invented stats, unverified proof points, or claims not in the materials.\n\n"
        "2. OBJECTION ADDRESSED — Does this directly and specifically address the persona's "
        "documented top objection? Vague acknowledgement scores low.\n\n"
        "3. CTA SPECIFICITY — Is the call-to-action tied to this persona's documented buying "
        "trigger, or is it generic? Generic CTAs (e.g. 'book a demo') score low unless "
        "the trigger matches."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": REFLECTION_SCHEMA}},
    )

    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def revise_asset(
    client: anthropic.Anthropic,
    system: list[dict],
    persona: dict,
    asset: dict,
    content: str,
    reflection: dict,
) -> str:
    """Stream-generate a revised version addressing reflection feedback."""

    scores = reflection["scores"]

    score_lines = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v['score']}/10\n  Issue: {v['feedback']}"
        for k, v in scores.items()
    )

    prompt = (
        f"Revise this asset to fix every flagged issue below. Return only the revised asset.\n\n"
        f"PERSONA: {persona['persona_name']}\n"
        f"ASSET TYPE: {asset['asset_type']}\n"
        f"TITLE: {asset['title']}\n\n"
        f"ORIGINAL:\n{content}\n\n"
        f"REVIEW SCORES:\n{score_lines}\n\n"
        f"REVISION INSTRUCTIONS: {reflection['revision_instructions']}"
    )

    full_text = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
            full_text += chunk
    print()
    return full_text


# ── Content plan ──────────────────────────────────────────────────────────────

def build_content_plan(company: str, results: list[dict]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    total_assets  = sum(len(p["assets"]) for p in results)
    revised_count = sum(1 for p in results for a in p["assets"] if a.get("revision_count", 0) > 0)
    flagged_count = sum(1 for p in results for a in p["assets"] if a.get("quality_flag"))

    lines = [
        f"# {company.title()} — Content Plan",
        "",
        f"*Generated {today} by assets.py*",
        "",
        f"**{len(results)} personas · {total_assets} assets · {revised_count} revised"
        + (f" · {flagged_count} flagged**" if flagged_count else "**"),
        "",
        "---",
        "",
    ]

    for pr in results:
        lines += [f"## {pr['persona_name']}", "", f"*{pr['persona_summary']}*", ""]

        for a in pr["assets"]:
            scores = a.get("scores") or {}
            rev    = a.get("revision_count", 0)
            flag   = a.get("quality_flag")

            lines += [
                f"### [{a['asset_type'].title()}] {a['title']}",
                "",
                f"**File:** `{a['filename']}`  ",
            ]

            if flag:
                lines.append(f"**⚠ Quality flag:** {flag}  ")
            elif rev:
                lines.append(f"**Revised:** {rev}×  ")

            lines.append(f"**Why:** {a['rationale']}")
            lines.append("")

            if scores:
                def fmt(k: str) -> str:
                    v = scores[k]
                    note = v["feedback"][:110].rstrip()
                    if len(v["feedback"]) > 110:
                        note += "…"
                    return f"| {k.replace('_',' ').title()} | {v['score']}/10 | {note} |"

                lines += [
                    "| Criterion | Score | Notes |",
                    "|-----------|------:|-------|",
                    fmt("claim_traceability"),
                    fmt("objection_addressed"),
                    fmt("cta_specificity"),
                    "",
                ]

            lines += ["---", ""]

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate persona-targeted written assets.")
    parser.add_argument("--company", required=True, help="Company slug (e.g., notion, stackly)")
    args = parser.parse_args()

    company = args.company.lower()
    out_dir = OUTPUT_DIR / company
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  ASSET GENERATOR — {company.upper()}")
    print(f"{'='*60}\n")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Load source materials
    print("Loading source materials...")
    try:
        positioning, content_brief, personas = load_source_materials(company)
    except FileNotFoundError as e:
        print(f"\nERROR: Missing input file — {e}", file=sys.stderr)
        sys.exit(1)

    # Build a single cached system prompt reused across all API calls
    system = build_system(company, positioning, content_brief, personas)

    # ── 1. Plan ───────────────────────────────────────────────────────────────
    print("\n[1/3] Planning assets per persona...\n")
    plan = plan_assets(client, company, system)

    for p in plan["personas"]:
        print(f"  {p['persona_name']}")
        for a in p["assets"]:
            print(f"    • [{a['asset_type']}] {a['title']}")

    # ── 2. Generate + reflect + revise ────────────────────────────────────────
    print("\n[2/3] Generating assets...\n")
    results: list[dict] = []

    for persona in plan["personas"]:
        persona_result: dict = {
            "persona_name":    persona["persona_name"],
            "persona_summary": persona["persona_summary"],
            "assets":          [],
        }

        for asset in persona["assets"]:
            print(f"\n{'─'*60}")
            print(f"  PERSONA : {persona['persona_name']}")
            print(f"  ASSET   : [{asset['asset_type']}] {asset['title']}")
            print(f"{'─'*60}\n")

            # Generate
            print("Generating...\n")
            content = generate_asset(client, system, persona, asset)

            # Reflection loop — max 2 revisions
            final_reflection: dict | None = None
            quality_flag: str | None = None
            revision_count = 0

            while revision_count < 2:
                print(f"\n  Reflecting (pass {revision_count + 1})...")
                reflection    = reflect_on_asset(client, system, persona, asset, content)
                final_reflection = reflection
                scores        = reflection["scores"]
                low_criteria  = [k for k, v in scores.items() if v["score"] < 7]

                score_str = " | ".join(
                    f"{k.replace('_',' ').split()[0].title()} {v['score']}/10"
                    for k, v in scores.items()
                )
                print(f"  Scores : {score_str}")

                if not low_criteria:
                    print("  ✓ All criteria ≥ 7 — approved")
                    break

                print(f"  Below 7: {', '.join(low_criteria)}")
                print(f"\nRevising...\n")
                content = revise_asset(client, system, persona, asset, content, reflection)
                revision_count += 1

            # After the 2nd revision the loop exits without a final reflection — do one
            # now so scores in the file describe the content that was actually saved.
            if revision_count == 2:
                print("\n  Reflecting (final pass after max revisions)...")
                final_reflection = reflect_on_asset(client, system, persona, asset, content)
                final_scores     = final_reflection["scores"]
                still_low        = [k for k, v in final_scores.items() if v["score"] < 7]
                score_str        = " | ".join(
                    f"{k.replace('_',' ').split()[0].title()} {v['score']}/10"
                    for k, v in final_scores.items()
                )
                print(f"  Scores : {score_str}")
                if still_low:
                    quality_flag = f"below-threshold after max revisions: {', '.join(still_low)}"
                    print(f"  ⚠ Saved with quality flag — {quality_flag}")
                else:
                    print("  ✓ Approved after final pass")

            # Save asset file
            persona_slug = slugify(persona["persona_name"], 24)
            type_slug    = slugify(asset["asset_type"], 20)
            fname        = f"{company}-{persona_slug}-{type_slug}.md"

            frontmatter_lines = [
                "---",
                f"company: {company}",
                f"persona: {persona['persona_name']}",
                f"asset_type: {asset['asset_type']}",
                f"title: {asset['title']}",
            ]
            if final_reflection:
                frontmatter_lines.append("scores:")
                for k, v in final_reflection["scores"].items():
                    frontmatter_lines.append(f"  {k}: {v['score']}")
            if quality_flag:
                frontmatter_lines.append(f"quality_flag: \"{quality_flag}\"")
            frontmatter_lines.append("---")

            (out_dir / fname).write_text("\n".join(frontmatter_lines) + "\n\n" + content)
            print(f"\n  Saved: output/{company}/{fname}")

            persona_result["assets"].append({
                "asset_type":     asset["asset_type"],
                "title":          asset["title"],
                "rationale":      asset["rationale"],
                "filename":       fname,
                "scores":         final_reflection["scores"] if final_reflection else None,
                "revision_count": revision_count,
                "quality_flag":   quality_flag,
            })

        results.append(persona_result)

    # ── 3. Content plan ───────────────────────────────────────────────────────
    print("\n[3/3] Writing content plan...")
    plan_md = build_content_plan(company, results)
    plan_path = out_dir / f"{company}-content-plan.md"
    plan_path.write_text(plan_md)
    print(f"  Saved: output/{company}/{company}-content-plan.md")

    print(f"\n{'='*60}")
    print(f"  Done. {sum(len(p['assets']) for p in results)} assets in output/{company}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
