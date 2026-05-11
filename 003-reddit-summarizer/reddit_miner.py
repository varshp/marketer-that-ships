#!/usr/bin/env python3
"""
Reddit Signal Miner — fetches posts + comments from any subreddit,
sends them to Claude for PMM analysis, and saves a markdown report.

Usage: python3 reddit_miner.py <subreddit>
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

import requests
import anthropic
from dotenv import load_dotenv

# ── Config ──────────────────────────────────────────────────────────────────

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
HEADERS = {"User-Agent": "gtm-signal-miner/1.0"}

POSTS_TO_FETCH = 25        # posts pulled from subreddit listing
POSTS_TO_ANALYZE = 15      # top N posts sent to Claude
COMMENTS_PER_POST = 8      # top comments per post
REQUEST_DELAY = 0.5        # seconds between Reddit API calls (be polite)

# ── Reddit fetching ──────────────────────────────────────────────────────────

def fetch_subreddit_posts(subreddit: str, limit: int = 25) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}.json?limit={limit}&sort=hot"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [child["data"] for child in data["data"]["children"] if child["kind"] == "t3"]


def fetch_post_comments(subreddit: str, post_id: str, limit: int = 10) -> list[str]:
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={limit}&depth=1&sort=top"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        comments = []
        for child in data[1]["data"]["children"]:
            if child["kind"] != "t1":
                continue
            body = child["data"].get("body", "").strip()
            if body and body not in ("[removed]", "[deleted]"):
                comments.append(body)
        return comments[:limit]
    except Exception:
        return []


def collect_data(subreddit: str) -> list[dict]:
    """Fetch hot posts and their top comments for a subreddit."""
    posts = fetch_subreddit_posts(subreddit, POSTS_TO_FETCH)
    enriched = []
    for post in posts[:POSTS_TO_ANALYZE]:
        time.sleep(REQUEST_DELAY)
        comments = fetch_post_comments(subreddit, post["id"], COMMENTS_PER_POST)
        enriched.append({
            "title": post.get("title", ""),
            "selftext": post.get("selftext", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "comments": comments,
        })
    return enriched


# ── Content formatting ────────────────────────────────────────────────────────

def _clean(text: str, max_chars: int = 600) -> str:
    text = text.strip()
    if text in ("[removed]", "[deleted]", ""):
        return ""
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def format_posts_for_prompt(subreddit: str, posts: list[dict]) -> str:
    lines = [f"# Reddit data from r/{subreddit}\n"]
    for i, post in enumerate(posts, 1):
        title = post["title"]
        body = _clean(post.get("selftext", ""), 500)
        lines.append(f"## Post {i} — {title}")
        if body:
            lines.append(f"**Body:** {body}")
        comments = [_clean(c, 300) for c in post.get("comments", []) if _clean(c)]
        if comments:
            lines.append("**Top comments:**")
            for c in comments:
                lines.append(f"- {c}")
        lines.append("")
    return "\n".join(lines)


# ── Claude analysis ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a senior Product Marketing Manager (PMM). Your job is to extract \
actionable go-to-market signals from raw community data. Be specific, quote \
real language where possible, and avoid generic filler."""

def build_user_prompt(subreddit: str, reddit_data: str) -> str:
    return f"""\
Analyze the following Reddit posts and comments from r/{subreddit}.

Produce a signal report in **exactly** this markdown format (keep the headers verbatim):

## Reddit Signal Report: r/{subreddit}

### Top recurring complaints
List the most common pain points, frustrations, and problems — be specific.

### Top recurring praise
What users consistently love, appreciate, or recommend.

### Exact Reddit language
Verbatim phrases, slang, metaphors the community uses. These are copywriting gold.

### Questions nobody is answering well
Gaps where users are confused or not getting helpful answers.

### Emerging themes
Trends, new topics, or shifting concerns gaining traction in the community.

### PMM action items
Concrete, numbered recommendations for positioning, messaging, or product marketing.

---

{reddit_data}"""


def analyze_with_claude(subreddit: str, reddit_data: str) -> str:
    client = anthropic.Anthropic()
    prompt = build_user_prompt(subreddit, reddit_data)
    report_chunks: list[str] = []

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            report_chunks.append(text)

    return "".join(report_chunks)


# ── Output ────────────────────────────────────────────────────────────────────

def save_report(subreddit: str, report: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reddit_signal_{subreddit}_{timestamp}.md"
    Path(filename).write_text(report, encoding="utf-8")
    return filename


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 reddit_miner.py <subreddit>")
        sys.exit(1)

    subreddit = sys.argv[1].strip().lstrip("r/")

    # Load API key from project .env file
    load_dotenv(ENV_FILE)
    if not os.getenv("ANTHROPIC_API_KEY"):
        print(f"Error: ANTHROPIC_API_KEY not found in {ENV_FILE}")
        sys.exit(1)

    print(f"\nMining signals from r/{subreddit}...\n")

    # 1 — Fetch Reddit data
    print(f"Fetching posts from r/{subreddit}...")
    try:
        posts = collect_data(subreddit)
    except requests.HTTPError as e:
        print(f"Reddit API error: {e}")
        sys.exit(1)

    print(f"Fetched {len(posts)} posts with comments.\n")

    # 2 — Format for Claude
    reddit_data = format_posts_for_prompt(subreddit, posts)

    # 3 — Analyze with Claude (streaming)
    print("Analyzing with Claude...\n")
    print("=" * 70)
    report = analyze_with_claude(subreddit, reddit_data)
    print("\n" + "=" * 70 + "\n")

    # 4 — Save
    filename = save_report(subreddit, report)
    print(f"Report saved: {filename}\n")


if __name__ == "__main__":
    main()
