# Stellvertretix

A public portal for substitution-teaching vacancies in Zürich, sourced from [epalero.ch](https://www.epalero.ch). Updates every 15 minutes via GitHub Actions and sends push notifications via [ntfy](https://ntfy.sh) when new listings appear.

## How it works

1. **GitHub Actions** runs `poller.py` every 15 minutes.
2. The poller fetches all current vacancies from the epalero.ch JSON API (no login required).
3. It compares the result against the existing `data.json` to detect new entries.
4. If new entries exist: `data.json` is replaced with the latest data, committed, and a push notification is sent per new entry.
5. **GitHub Pages** serves `index.html`, which reads `data.json` and renders a sortable table.

## Deploy

1. **Fork** this repo.
2. Go to **Settings → Secrets and variables → Actions** and add a repository secret:
   - `NTFY_TOPIC` — the ntfy topic name to publish to (e.g. `my-secret-topic-abc123`). Leave it unset to disable notifications.
3. Go to **Settings → Pages** and set the source to **GitHub Actions** (or _Deploy from branch_ → `main` → `/ (root)`).
4. Enable the workflow: **Actions → Poll epalero.ch → Enable workflow**.
5. Optionally trigger the first run manually via **Actions → Poll epalero.ch → Run workflow**.

The portal will be live at `https://<your-username>.github.io/<repo-name>/`.

## Subscribe to notifications

Notifications are sent via [ntfy.sh](https://ntfy.sh) — free, no account needed for subscribers.

### Mobile app (recommended)

1. Install the ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)).
2. Add a subscription for the topic name set in `NTFY_TOPIC`.

### Web / curl

```
> curl -d "Backup successful 😀" ntfy.sh/test
{"id":"qXgPytc8hJ8q","time":1779811117,"expires":1779854317,"event":"message","topic":"test","message":"Backup successful 😀"}
```

Or visit `https://ntfy.sh/testy_is_the_besty` in a browser.

**Keep your topic name private** — anyone who knows it can subscribe (or publish).

## Notification format

Each new listing triggers one notification:

```
Title:  Neue Stellvertretung: Primarschule Muster
Body:   Primarschule Muster, Zürich
        Fächer: Deutsch, Mathematik, NMG
        01.06.2025 – 30.06.2025, 14 Lekt./Wo.
```

## API source

Data comes from:

```
https://backend.epalero.ch/api/v1/vacancies?
```

```
GET https://backend.epalero.ch/api/v1/vacancies
    ?sort=publish,desc
    &cantons=zurich
    &educationStatus=enrolled,enrolledWithBaseYear
    &levelsDetailed=levelLower,levelMiddle
```

This endpoint is public (no authentication). The poller falls back gracefully on errors and never overwrites `data.json` with empty or partial results.

## Local development

```bash
pip install -r requirements.txt
python poller.py            # dry run — reads/writes data.json locally
python -m http.server 8080  # serve index.html on http://localhost:8080
```
