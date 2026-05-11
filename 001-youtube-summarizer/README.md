# YouTube Video Summarizer

**GTM AI Toolkit — Experiment 001**

Paste a YouTube URL. Get a B2B-ready summary in seconds.

The script extracts the video transcript, sends it to Claude, and returns:
- A one-sentence TL;DR
- 3 key takeaways
- 1 recommended action for a B2B marketer

Output is saved as a markdown file in `outputs/`.

---

## Setup

**1. Add your Anthropic API key**

Copy `.env.example` to `.env` at the root of this repo and fill in your key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## How to run

Pass the URL as an argument:

```bash
python summarize.py https://www.youtube.com/watch?v=aircAruvnKk
```

Or run without arguments and paste the URL when prompted:

```bash
python summarize.py
```

---

## What the output looks like

```
## Video: But what is a neural network? | Chapter 1, Deep learning

**TL;DR:** Neural networks learn to recognize patterns by adjusting numerical
weights across layers of interconnected nodes, similar to how the brain works.

**Key takeaways:**
1. A neural network is a series of layers where each node holds a number
   (its "activation") calculated from the previous layer's outputs.
2. Learning happens by tuning thousands of weights and biases using
   labeled training data, not by hand-coding rules.
3. Even simple networks can solve complex tasks like digit recognition,
   making them a practical starting point for ML adoption.

**Action for B2B marketers:**
Run a 2-week proof of concept using publicly available labeled data
(e.g., customer support tickets) to show stakeholders how a basic neural
network can automate classification — before committing to a full build.
```

The full markdown file is saved to `outputs/<video_id>-<timestamp>.md`.

---

## Notes

- The video must have captions/subtitles enabled on YouTube.
- Auto-generated captions work fine.
- There is no hard length limit — Claude Opus handles transcripts up to ~150,000 words.
- Each run costs roughly $0.01–$0.05 in API credits depending on video length.
