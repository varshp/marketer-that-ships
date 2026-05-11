# Marketer that Ships

You've been told to use AI. Now what?

Most marketers have already tried ChatGPT for first drafts. The harder question is what comes next.

This repo is my answer: ten public GTM AI experiments that move from one-off prompts to repeatable systems.

Each experiment is a runnable Python script that solves a real product marketing problem using public data, the Claude API, and a small set of standard libraries.

Demo companies are public. No customer data. No internal documents.

## What this is

Most AI adoption in marketing stops at the copilot layer.

Ask for a draft. Rewrite the draft. Make it sound more like us. Repeat.

This repo is about the next layer: treating AI as infrastructure.

Inputs go in. Signal gets extracted. Prompts get chained. Outputs become structured enough to reuse, evaluate, and automate.

The goal is not to generate prettier copy.

The goal is to build marketing systems that can pull signal from the outside world, turn it into strategic judgment, and eventually produce assets from a repeatable workflow.

## The path

The ten experiments move through four stages:

**Signal.** Pull structured information from the wild. YouTube transcripts. G2 reviews. Reddit threads. Competitor pages. Job postings. 10-K filings.

**Synthesis.** Combine signals into something you can defend. The competitive positioning quadrant takes the inputs above and turns them into a strategic view.

**Pipeline.** Chain steps together so one output becomes the input for the next. Positioning arcs and personas start to become workflows, not documents.

**Agentic.** Give the system a goal, guardrails, scoring criteria, and revision loops. The asset generator is the first step toward AI that does more than respond.

## Setup

Clone the repo:

```bash
git clone https://github.com/varshp/marketer-that-ships.git
cd marketer-that-ships
```

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Open `.env` and fill in:

- `ANTHROPIC_API_KEY` — required for every experiment. Get one at console.anthropic.com.
- `FIRECRAWL_API_KEY` — only required for 002-g2-review-miner. Get one at firecrawl.dev.

Each experiment is a standalone folder. To run one, change into it, create a virtual environment, install dependencies, run.

```bash
cd 001-youtube-summarizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 summarize.py "https://www.youtube.com/watch?v=..."
```

Every experiment has its own README with the exact command to run it.

## The ten experiments

| # | Name | Stage | What it does |
|---|------|-------|--------------|
| 001 | YouTube summarizer | Signal | Pulls a transcript from any YouTube video and summarizes it into structured marketing insight. |
| 002 | G2 and Capterra review miner | Signal | Scrapes G2 reviews for any product and extracts pain themes, feature requests, and competitive mentions. |
| 003 | Reddit signal summarizer | Signal | Reads any subreddit and surfaces what real users are saying about a category or product. |
| 004 | Competitor page decoder | Signal | Takes a competitor URL and returns their positioning, ICP, and messaging architecture. |
| 005 | Job posting analyzer | Signal | Reads a competitor's open roles and infers their roadmap, priorities, and where they are investing. |
| 006 | 10-K earnings analyzer | Signal | Parses public 10-K filings and extracts the strategic narrative the company is telling investors. |
| 007 | Competitive positioning quadrant | Synthesis | Takes signal from 001-006 and produces a defensible 2x2 placing competitors against two axes. |
| 008 | Company positioning arc | Pipeline | Generates a positioning narrative for any company from public inputs alone. |
| 009 | Persona generator | Pipeline | Builds detailed ICP personas from positioning, reviews, and job postings. |
| 010 | Asset generator | Agentic | Takes personas and positioning and produces on-brand marketing assets with scoring and revision loops. |

## How to read this repo

There are three ways to use it.

**As a portfolio.** Each experiment is a worked example of a real GTM problem. Read the code. Read the prompts. Adapt them.

**As a curriculum.** Run the experiments in order. By 007 you will see why the earlier ones matter. By 010 you will have built a basic pipeline that moves from signal to output.

**As a fork point.** Take any experiment, point it at your own company, swap the inputs, change the prompts. The code is the easy part. The thinking is the work.

## Context

This repo is the working artifact behind my Product Marketing Alliance keynote in Amsterdam on May 28, 2026, and the public build series running through April and May.

For the deeper cohort, later experiments, and writeups, go to [varshaa.dev](https://varshaa.dev).

## License

MIT. Use the code. Fork it. Modify it. Build something with it.

Built by [Varshaa Pallaath](https://varshaa.dev) in Amsterdam.
