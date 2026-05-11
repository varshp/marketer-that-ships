# Competitor Page Decoder

Fetch any competitor URL, strip the chrome, and get a PMM-ready strategic briefing from Claude — streamed live to your terminal and saved as a markdown file.

## How it works

1. Fetches the page with `requests` (browser-like User-Agent)
2. Strips nav, footer, cookie banners, and other noise with BeautifulSoup
3. Sends the cleaned text to Claude (`claude-opus-4-6`) for analysis
4. Streams the response to your terminal in real time
5. Saves the output as a timestamped `.md` file

## Setup

```bash
# Install dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env` at the root of this repo and add your `ANTHROPIC_API_KEY`.

## Usage

```bash
python3 decode.py https://www.notion.com
python3 decode.py https://www.linear.app
python3 decode.py https://www.figma.com
```

## Output

Each run saves a file like `output-www-notion-com-20240414-153022.md` in the current directory.

The report includes:

- **Their core pitch** — one-sentence summary of their claim
- **Who they're targeting** — buyer persona and pain points
- **Top 3 positioning bets** — competitive claims and why they matter
- **What they're not saying** — omissions and hidden weaknesses
- **PMM actions** — concrete next steps for your team
