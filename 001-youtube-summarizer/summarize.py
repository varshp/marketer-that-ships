#!/usr/bin/env python3
"""
YouTube Video Summarizer — GTM AI Toolkit, Experiment 001

Takes a YouTube URL, extracts the transcript, and uses Claude to generate
a structured summary for B2B marketers: TL;DR, key takeaways, and one action.

Usage:
    python3 summarize.py https://www.youtube.com/watch?v=XXXXXX
    python3 summarize.py  (will prompt for URL)
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OUTPUT_DIR = Path(__file__).parent / "outputs"


# ── YouTube helpers ───────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str:
    """Extract the 11-character video ID from any common YouTube URL format."""
    pattern = r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(
            f"Could not find a YouTube video ID in: {url}\n"
            "Accepted formats: youtube.com/watch?v=ID  |  youtu.be/ID"
        )
    return match.group(1)


def get_video_title(url: str) -> str:
    """Fetch the video title via YouTube's public oEmbed endpoint (no API key needed)."""
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("title", "Untitled Video")
    except Exception:
        return "Untitled Video"


def get_transcript(video_id: str) -> str:
    """Download and concatenate the video transcript into a single string.

    Tries English first, then falls back to any available language.
    """
    api = YouTubeTranscriptApi()
    try:
        # Try English first; fall back to any available language
        try:
            fetched = api.fetch(video_id, languages=["en"])
        except (NoTranscriptFound, CouldNotRetrieveTranscript):
            transcript_list = api.list(video_id)
            transcript = next(iter(transcript_list))
            fetched = transcript.fetch()
    except TranscriptsDisabled:
        raise RuntimeError("Transcripts are disabled for this video.")
    except (NoTranscriptFound, CouldNotRetrieveTranscript):
        raise RuntimeError(
            "No transcript found. The video may not have captions enabled."
        )
    return " ".join(snippet.text for snippet in fetched.snippets)


# ── Claude summarization ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a senior B2B marketing strategist. When given a YouTube video transcript,
you extract the most relevant insights and turn them into a concise, actionable
summary that a busy marketer can read in under two minutes.

Always respond with exactly the five labeled lines below — nothing else:

TL;DR: <one sentence capturing the core message>
Key Takeaway 1: <first key insight>
Key Takeaway 2: <second key insight>
Key Takeaway 3: <third key insight>
Action for B2B Marketers: <one specific, practical recommendation>"""


def summarize_with_claude(transcript: str, title: str) -> str:
    """Send the transcript to Claude Opus and return the raw structured response."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"ANTHROPIC_API_KEY is not set.\n"
            f"Add it to: {ENV_PATH}\n"
            f"Example line:  ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)

    user_message = (
        f"Video title: {title}\n\n"
        f"Transcript:\n{transcript}"
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        final = stream.get_final_message()

    return final.content[0].text


# ── Parsing & formatting ──────────────────────────────────────────────────────

def parse_response(text: str) -> dict:
    """Parse Claude's five-line structured response into a dict."""
    result = {"tldr": "", "takeaways": [], "action": ""}
    labels = {
        "TL;DR:": "tldr",
        "Key Takeaway 1:": "t1",
        "Key Takeaway 2:": "t2",
        "Key Takeaway 3:": "t3",
        "Action for B2B Marketers:": "action",
    }
    for line in text.strip().splitlines():
        line = line.strip()
        for label, key in labels.items():
            if line.startswith(label):
                value = line[len(label):].strip()
                if key == "tldr":
                    result["tldr"] = value
                elif key in ("t1", "t2", "t3"):
                    result["takeaways"].append(value)
                elif key == "action":
                    result["action"] = value
    return result


def format_markdown(title: str, url: str, parsed: dict) -> str:
    """Render the parsed summary as clean markdown."""
    takeaways = "\n".join(
        f"{i + 1}. {t}" for i, t in enumerate(parsed["takeaways"])
    )
    return (
        f"## Video: {title}\n\n"
        f"**TL;DR:** {parsed['tldr']}\n\n"
        f"**Key takeaways:**\n{takeaways}\n\n"
        f"**Action for B2B marketers:**\n{parsed['action']}\n"
    )


# ── Output ────────────────────────────────────────────────────────────────────

def save_output(content: str, video_id: str) -> Path:
    """Save the markdown summary to outputs/<video_id>-<timestamp>.md."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTPUT_DIR / f"{video_id}-{timestamp}.md"
    path.write_text(content, encoding="utf-8")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    # Accept URL from command line or interactive prompt
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("Paste a YouTube URL: ").strip()

    if not url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    print(f"\nProcessing: {url}\n")

    # Step 1: video ID
    try:
        video_id = extract_video_id(url)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    # Step 2: title
    print("Fetching video title ...")
    title = get_video_title(url)
    print(f"  -> {title}")

    # Step 3: transcript
    print("Extracting transcript ...")
    try:
        transcript = get_transcript(video_id)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    print(f"  -> {len(transcript.split()):,} words extracted")

    # Step 4: Claude summary
    print("Summarizing with Claude Opus ...")
    try:
        raw_response = summarize_with_claude(transcript, title)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    # Step 5: format & save
    parsed = parse_response(raw_response)
    markdown = format_markdown(title, url, parsed)
    output_path = save_output(markdown, video_id)

    # Print to terminal
    separator = "-" * 60
    print(f"\n{separator}\n")
    print(markdown)
    print(separator)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
