#!/usr/bin/env python3
"""
Polls epalero.ch for new substitution job listings in Zurich,
updates data.json, and sends ntfy notifications for new entries.
"""
import json
import os
import sys
from datetime import datetime, timezone

import requests

API_BASE = "https://backend.epalero.ch/api/v1/vacancies"
API_PARAMS = {
    "sort": "publish,desc",
    "cantons": "zurich",
    "educationStatus": "enrolled,enrolledWithBaseYear",
    "levelsDetailed": "levelLower,levelMiddle",
}
DATA_FILE = "data.json"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")

SUBJECT_LABELS: dict[str, str] = {
    "german": "Deutsch",
    "mathematics": "Mathematik",
    "natureHumanSociety": "NMG",
    "fineArts": "BG",
    "music": "Musik",
    "sports": "Sport",
    "textileAndTechnicalDesign": "TTG",
    "mediaAndComputerScience": "MI",
    "english": "Englisch",
    "french": "Französisch",
    "religionsCulturesEthics": "ERG",
    "germanAsSecondLanguage": "DaZ",
    "naturalSciences": "Naturwissenschaften",
    "geography": "Geographie",
    "history": "Geschichte",
    "sciences": "WAH",
    "economics": "Wirtschaft",
    "swimming": "Schwimmen",
    "kindergartenClasses": "Kindergarten",
    "ifIssIsr": "IF/ISS/ISR",
    "natureAndTechnology": "Natur & Technik",
    "drama": "Theater",
}


def fetch_all_vacancies() -> list[dict]:
    seen_ids: set[str] = set()
    results: list[dict] = []

    for page in range(200):
        resp = requests.get(API_BASE, params={**API_PARAMS, "page": page}, timeout=30)
        resp.raise_for_status()
        entries: list[dict] = resp.json()

        if not entries:
            break

        new_on_page = [e for e in entries if e["id"] not in seen_ids]
        if not new_on_page:
            break  # pagination loop detected — stop

        for e in new_on_page:
            seen_ids.add(e["id"])
            results.append(e)

        if len(entries) < len(new_on_page):
            break  # partial page = last page

    return results


def load_existing() -> list[dict]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def entry_key(e: dict) -> tuple[str, int, str]:
    school = e["school"]["schoolName"]
    start = e["startTimestamp"]
    subjects = ",".join(sorted(e.get("subjects") or []))
    return (school, start, subjects)


def find_new_entries(existing: list[dict], fetched: list[dict]) -> list[dict]:
    existing_keys = {entry_key(e) for e in existing}
    return [e for e in fetched if entry_key(e) not in existing_keys]


def fmt_date(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.strftime("%d.%m.%Y")


def send_notification(entry: dict) -> None:
    if not NTFY_TOPIC:
        return

    school = entry["school"]["schoolName"]
    city = entry["school"]["address"]["city"]
    raw_subjects = entry.get("subjects") or []
    subjects = ", ".join(SUBJECT_LABELS.get(s) or s for s in raw_subjects)
    start = fmt_date(entry["startTimestamp"])
    end = fmt_date(entry["endTimestamp"])
    pensum = entry.get("pensum", "?")

    message = f"{school}, {city}\nFächer: {subjects}\n{start} – {end}, {pensum} Lekt./Wo."
    title = f"Neue Stellvertretung: {school}"

    vacancy_url = f"https://www.epalero.ch/de/stellvertretungen/{entry['id']}"
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "default",
            "Click": vacancy_url,
            "Actions": f"view, Open Vacancy, {vacancy_url}, clear=true",
        },
        timeout=15,
    )


def main() -> None:
    print("Fetching vacancies from epalero.ch …", flush=True)
    try:
        fetched = fetch_all_vacancies()
    except Exception as exc:
        print(f"ERROR: API fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not fetched:
        print("ERROR: API returned no entries — aborting to avoid wiping data.json", file=sys.stderr)
        sys.exit(1)

    print(f"Fetched {len(fetched)} entries")

    existing = load_existing()
    new_entries = find_new_entries(existing, fetched)

    if not new_entries:
        print("No new entries. data.json unchanged.")
        return

    print(f"Found {len(new_entries)} new entries — updating data.json")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(fetched, f, ensure_ascii=False, indent=2)

    for entry in new_entries:
        school = entry["school"]["schoolName"]
        try:
            send_notification(entry)
            print(f"  Notified: {school}")
        except Exception as exc:
            print(f"  WARNING: notification failed for {school}: {exc}")

    # Signal to the workflow that data.json was updated
    print("UPDATED")


if __name__ == "__main__":
    main()
