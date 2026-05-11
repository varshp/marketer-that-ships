# Reddit Signal Miner

Pulls hot posts + top comments from any subreddit via Reddit's public JSON API, sends them to Claude for PMM analysis, and saves a structured markdown report.

No PRAW. No Firecrawl. No Reddit credentials needed.

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the root of this repo and fill in your key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python3 reddit_miner.py <subreddit>
```

Examples:

```bash
python3 reddit_miner.py projectmanagement
python3 reddit_miner.py SaaS
python3 reddit_miner.py devops
python3 reddit_miner.py startups
```

## Output

The report streams to stdout as Claude generates it, then saves to a timestamped file:

```
reddit_signal_projectmanagement_20260412_143021.md
```

## Report format

```
## Reddit Signal Report: r/<subreddit>

### Top recurring complaints
### Top recurring praise
### Exact Reddit language
### Questions nobody is answering well
### Emerging themes
### PMM action items
```

## How it works

1. Fetches 25 hot posts from `https://www.reddit.com/r/{subreddit}.json`
2. For the top 15 posts, fetches 8 top comments each from the comments endpoint
3. Formats posts + comments into a structured prompt
4. Streams the prompt to `claude-opus-4-6` for analysis
5. Saves the markdown report

A 0.5 s delay is added between Reddit API calls to avoid rate limiting.
