# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Stellvertretix polls the [epalero.ch](https://www.epalero.ch) public API every 5 minutes (07:00–19:00 UTC via GitHub Actions) for substitute-teaching vacancies in Zürich. When new listings appear, it overwrites `data.json`, commits it, and fires push notifications via [ntfy.sh](https://ntfy.sh). `index.html` is a static frontend served by GitHub Pages that reads `data.json` directly.

## Local development

```bash
pip install -r requirements.txt
python poller.py              # runs against live API, reads/writes data.json locally
python -m http.server 8080    # serve index.html at http://localhost:8080
```

`NTFY_TOPIC` env var controls notifications — unset means notifications are skipped silently.

## Architecture

The project has three parts, each a single file:

- **[poller.py](poller.py)** — Python script: fetches all paginated vacancy pages from `backend.epalero.ch/api/v1/vacancies`, deduplicates by `(school, startTimestamp, subjects)` key, writes `data.json` only when new entries are found, prints `UPDATED` to stdout as a signal to the workflow, sends one ntfy notification per new entry.
- **[data.json](data.json)** — The live dataset; committed by the GitHub Actions bot on each poll that yields new data.
- **[index.html](index.html)** — Vanilla JS frontend; fetches `data.json` at load time, renders a sortable table, marks entries published within the last 24 h as "new" (green highlight). No build step.

## GitHub Actions workflow

[.github/workflows/poll.yml](.github/workflows/poll.yml) — runs on `*/5 7-19 * * *`. It detects whether `poller.py` printed `UPDATED` and only commits + pushes `data.json` if so. Requires the `NTFY_TOPIC` repository secret (optional).

## Key API details

- Endpoint: `GET https://backend.epalero.ch/api/v1/vacancies` — public, no auth.
- Pagination: page-based; poller stops on empty page, partial page, or duplicate-ID page.
- Vacancy deep link format: `https://www.epalero.ch/de/stellvertretungen/{id}` (closed vacancies redirect to `/de`).
- The `subjects` and `levelsDetailed` fields use English enum keys; both `poller.py` and `index.html` maintain identical German label maps — keep them in sync when adding new subjects.
