#!/usr/bin/env python3
"""
Competitive Quadrant Generator
Reads competitive intelligence .md files, derives 3 distinct axis pairs
via a single Claude API call, and plots individual quadrant charts.
"""

import argparse
import json
import os
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from adjustText import adjust_text as _adjust_text
    _HAS_ADJUST_TEXT = True
except ImportError:
    _HAS_ADJUST_TEXT = False

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
MODEL = "claude-opus-4-6"

COLORS = [
    "#2563EB",  # blue
    "#DC2626",  # red
    "#16A34A",  # green
    "#D97706",  # amber
    "#7C3AED",  # purple
    "#0891B2",  # cyan
    "#DB2777",  # pink
]


@dataclass
class FontSizes:
    title: int
    axis_label: int
    company: int
    annotation: int
    tick: int
    dot_size: int


FONTS_DEFAULT = FontSizes(
    title=13, axis_label=10, company=8.5,
    annotation=6.5, tick=8, dot_size=150,
)


# ---------------------------------------------------------------------------
# Input reading
# ---------------------------------------------------------------------------

def load_env():
    load_dotenv(ENV_PATH)
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        sys.exit(f"ANTHROPIC_API_KEY not found in {ENV_PATH}")
    return key


def read_inputs(folder: Path) -> dict[str, str]:
    """Group .md files by company name (prefix before first dash)."""
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for f in sorted(folder.glob("*.md")):
        company = f.stem.split("-")[0].lower()
        groups[company].append((f.stem, f.read_text(encoding="utf-8")))

    combined: dict[str, str] = {}
    for company, files in groups.items():
        parts = [f"## COMPANY: {company.upper()}"]
        for stem, content in files:
            parts.append(f"### Source: {stem}\n\n{content}")
        combined[company] = "\n\n".join(parts)
    return combined


# ---------------------------------------------------------------------------
# Claude API
# ---------------------------------------------------------------------------

def build_prompt(combined: dict[str, str]) -> str:
    all_content = "\n\n---\n\n".join(combined.values())
    return f"""{all_content}

---

You are a senior PMM analysing a competitive landscape across {len(combined)} companies. Based only on the intelligence provided, derive 3 distinct axis pairs for competitive quadrants. Each pair must reveal a genuinely different strategic dimension — not variations of the same theme. Do not use generic axes like vision vs execution or price vs quality. All axes must be grounded in specific evidence from the data.

Return only valid JSON, no preamble, no markdown:
{{
  "quadrants": [
    {{
      "title": "short descriptive title for this view",
      "x_axis": {{
        "label": "short axis label",
        "low": "what low means",
        "high": "what high means"
      }},
      "y_axis": {{
        "label": "short axis label",
        "low": "what low means",
        "high": "what high means"
      }},
      "companies": [
        {{
          "name": "Company Name",
          "x": 6.5,
          "y": 7.2,
          "rationale": "one sentence explaining placement"
        }}
      ],
      "rationale": "one to two sentences on why these axes reveal something the other quadrants don't"
    }}
  ]
}}"""


def call_claude(api_key: str, prompt: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Plotting — single quadrant
# ---------------------------------------------------------------------------

def _wrap_desc(text: str, width: int = 55) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _draw_quadrant(ax, quadrant: dict, fonts: FontSizes = FONTS_DEFAULT):
    """Draw one quadrant onto an existing Axes object."""
    ax.set_facecolor("white")

    ax.axvline(5, color="#E5E7EB", linewidth=1.0, zorder=1)
    ax.axhline(5, color="#E5E7EB", linewidth=1.0, zorder=1)

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_xticks(range(0, 11, 2))
    ax.set_yticks(range(0, 11, 2))
    ax.tick_params(colors="#9CA3AF", labelsize=fonts.tick)
    for spine in ax.spines.values():
        spine.set_edgecolor("#E5E7EB")

    x_axis = quadrant["x_axis"]
    y_axis = quadrant["y_axis"]

    # Directional descriptors placed OUTSIDE the axes spines (clip_on=False).
    # (0,0) = bottom-left spine corner; (1,1) = top-right spine corner.
    # Values outside [0,1] land outside the data area.
    desc_kw = dict(
        color="#9CA3AF", style="italic", fontsize=fonts.annotation,
        transform=ax.transAxes, clip_on=False, linespacing=1.3,
    )
    # y-axis: high well above the top spine (above the title), low below x-label.
    # y=1.22 in axes-fraction places the descriptor above the title at pad=10.
    ax.text(0.01, 1.22, f"↑ {_wrap_desc(y_axis['high'], 55)}",
            ha="left", va="bottom", **desc_kw)
    ax.text(0.01, -0.24, f"↓ {_wrap_desc(y_axis['low'], 55)}",
            ha="left", va="top", **desc_kw)
    # x-axis: low bottom-left, high bottom-right (below tick labels + x-label)
    ax.text(0.0, -0.12, f"← {_wrap_desc(x_axis['low'], 38)}",
            ha="left", va="top", **desc_kw)
    ax.text(1.0, -0.12, f"{_wrap_desc(x_axis['high'], 38)} →",
            ha="right", va="top", **desc_kw)

    ax.set_xlabel(x_axis["label"], fontsize=fonts.axis_label,
                  fontweight="bold", color="#111827", labelpad=8)
    ax.set_ylabel(y_axis["label"], fontsize=fonts.axis_label,
                  fontweight="bold", color="#111827", labelpad=8)

    # Company dots — collect label Text objects for adjustText de-collision
    xs = [co["x"] for co in quadrant["companies"]]
    ys = [co["y"] for co in quadrant["companies"]]
    label_texts = []
    for i, co in enumerate(quadrant["companies"]):
        color = COLORS[i % len(COLORS)]
        ax.scatter(co["x"], co["y"], s=fonts.dot_size, color=color, zorder=5,
                   edgecolors="white", linewidths=1.5)
        t = ax.text(
            co["x"] + 0.18, co["y"] + 0.30, co["name"],
            fontsize=fonts.company, fontweight="semibold", color=color,
            ha="left", va="bottom", zorder=6,
        )
        label_texts.append(t)

    if _HAS_ADJUST_TEXT and label_texts:
        try:
            _adjust_text(
                label_texts, x=xs, y=ys, ax=ax,
                expand=(1.5, 1.5),
                force_text=(0.4, 0.4),
                force_static=(0.3, 0.3),
                arrowstyle="-", color="#9CA3AF", linewidth=0.5,
            )
        except Exception:
            pass  # leave labels at initial offset if adjustText call fails

    wrapped_title = "\n".join(textwrap.wrap(quadrant["title"], width=48))
    ax.set_title(wrapped_title, fontsize=fonts.title,
                 fontweight="bold", color="#111827", pad=10)


def plot_individual(quadrant: dict, output_path: Path):
    fig, ax = plt.subplots(figsize=(11, 9), facecolor="white")
    _draw_quadrant(ax, quadrant, fonts=FONTS_DEFAULT)
    # Explicit margins give descriptors room; bbox_inches="tight" captures
    # everything outside the axes box that has clip_on=False.
    fig.subplots_adjust(left=0.12, right=0.88, top=0.80, bottom=0.30)
    fig.savefig(output_path, dpi=300, bbox_inches="tight",
                pad_inches=0.3, facecolor="white")
    plt.close(fig)
    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------------
# Markdown rationale
# ---------------------------------------------------------------------------

def write_rationale(quadrants: list[dict], output_path: Path):
    lines = ["# Competitive Quadrant — Axes Rationale", ""]

    for i, q in enumerate(quadrants, 1):
        x, y = q["x_axis"], q["y_axis"]
        lines += [
            f"## Quadrant {i}: {q['title']}",
            "",
            f"### X-axis: {x['label']}",
            f"- **Low:** {x['low']}",
            f"- **High:** {x['high']}",
            "",
            f"### Y-axis: {y['label']}",
            f"- **Low:** {y['low']}",
            f"- **High:** {y['high']}",
            "",
            f"**Why this view:** {q['rationale']}",
            "",
            "### Company Placements",
            "",
        ]
        for co in q["companies"]:
            lines.append(f"**{co['name']}** (x={co['x']}, y={co['y']})")
            lines.append(co["rationale"])
            lines.append("")
        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description="Competitive quadrant generator")
    parser.add_argument(
        "--inputs",
        type=Path,
        default=here / "../inputs",
        metavar="DIR",
        help="Folder of .md intelligence files (default: ../inputs)",
    )
    args = parser.parse_args()

    inputs_dir = args.inputs.resolve()
    if not inputs_dir.is_dir():
        sys.exit(f"Not a directory: {inputs_dir}")

    api_key = load_env()

    print("Reading input files...")
    combined = read_inputs(inputs_dir)
    if not combined:
        sys.exit("No .md files found in inputs/")
    print(f"  Companies: {', '.join(combined.keys())}")

    print("Calling Claude API (single call, 3 quadrants)...")
    prompt = build_prompt(combined)
    data = call_claude(api_key, prompt)
    quadrants = data["quadrants"]

    if len(quadrants) != 3:
        sys.exit(f"Expected 3 quadrants from Claude, got {len(quadrants)}")

    output_dir = here

    print("Plotting...")
    for i, q in enumerate(quadrants, 1):
        plot_individual(q, output_dir / f"quadrant-{i}.png")

    write_rationale(quadrants, output_dir / "axes-rationale.md")

    print("\nDone.")


if __name__ == "__main__":
    main()
