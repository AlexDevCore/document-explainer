# Document Explainer

A small web tool that explains **official US letters** in plain language — for people
who are new to the country and the system.

Paste the text of a letter (DMV, IRS, bank, landlord, utility, school, health insurance…)
and get back:

1. **What this is** — what the letter is and who sent it, in simple words
2. **What you need to do** — concrete steps and any deadlines
3. **What happens if you ignore it** — the consequences
4. **In your language** — the summary and actions translated

> It explains what a document *says*. It is **not** legal, medical, or financial advice.

## Why

Newcomers with limited English often can't tell an important notice from junk mail, and
rely on second-hand interpretation. This turns a confusing official letter into something
you can act on in 30 seconds.

## Stack

- Python + Flask
- Anthropic Claude (`claude-sonnet-5`) for the explanation and translation

## Setup

Requires [`uv`](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync
```

Copy the env template and add your key (get one at console.anthropic.com):

```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=...
```

**No key yet?** The app still runs — it returns a clearly-marked demo response so you can
test the interface. Real explanations start working the moment a key is present.

## Run

```bash
uv run python -m src.app
```

Then open http://localhost:5000 in your browser.

## Project layout

```
src/
  app.py          Flask routes (/ and /explain)
  explainer.py    calls Claude, parses the result, demo fallback
  config.py       env loading, model name
  logger.py       logging setup
  templates/
    index.html    the single-page UI
prompts/
  explainer_system.txt   the system prompt Claude follows
tests/            pytest tests
```
