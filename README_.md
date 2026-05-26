# stellvertretix


https://www.epalero.ch/de/stellvertretungen/?page=0&sort=publish%2Cdesc&cantons=zurich&educationStatus=enrolled%2CenrolledWithBaseYear&levelsDetailed=levelLower%2ClevelMiddle


first try:

```
a website, a self-service portal, which presents all records returned by this query: https://www.epalero.ch/de/stellvertretungen/?page=0&sort=publish%2Cdesc&cantons=zurich&educationStatus=enrolled%2CenrolledWithBaseYear&levelsDetailed=levelLower%2ClevelMiddle

add date and time and line/entry number. structure as rows.

also, provide a way to send notifications when new entries are published; maybe by email or some push message on the mobile/slack/xmpp/element or similar.

consider all options. if feasable, consider a simple fastapi app.
```

refined:

```
Build a public substitution-job portal for 2–3 teachers in Zurich. Source data is the epalero.ch listings page. The URL for the first page is:

https://www.epalero.ch/de/stellvertretungen/?page=0&sort=publish%2Cdesc&cantons=zurich&educationStatus=enrolled%2CenrolledWithBaseYear&levelsDetailed=levelLower%2ClevelMiddle

Important: this URL renders HTML, not JSON. Before writing a scraper, check the browser's Network tab while loading that page — look for any XHR/fetch requests returning application/json (often under /api/). If a JSON endpoint exists, use that. If not, parse the HTML with BeautifulSoup. Paginate by incrementing page=N until a page returns no entries.

The frontend is a static HTML/JS site hosted on GitHub Pages. It reads a data.json committed to the repo and renders entries as a sortable table with columns for entry number, publish date/time, and all other fields extractable from the source (school, subject, date, canton, level, and any others present). No auth, no login — fully public. Table must be readable on mobile.

The backend lives in a GitHub Actions workflow running every 15 minutes. A Python script (poller.py) fetches all pages, extracts the current full set of listings, and compares against the existing data.json to find new entries. A new entry is one whose combination of school + date + subject does not appear in the existing file.

data.json is a live mirror — replace it entirely with the current fetch result each run. Do not accumulate historical entries.

If new entries are found: commit the updated data.json (triggering Pages to redeploy), then send one ntfy notification per new entry to https://ntfy.sh/<NTFY_TOPIC> via HTTP POST. The message body should include school, subject, and date for that entry. The ntfy topic name is stored as a repo secret NTFY_TOPIC. The workflow needs contents: write permission to commit back to the repo.

If the API/scrape fails, log the error and exit without committing or sending notifications. Do not overwrite data.json with partial or empty results.

Deliverables: a working GitHub repo with index.html, poller.py, .github/workflows/poll.yml, and a README explaining how to subscribe to the ntfy topic. Ready to deploy: fork → set NTFY_TOPIC secret → enable Pages → done.
```