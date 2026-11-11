"""Notify the logged-in Mac user when GitHub misses the daily scheduled scrape."""

import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


REPO = "infoshubhjain/Project-Helix"
API = f"https://api.github.com/repos/{REPO}"
CHICAGO = ZoneInfo("America/Chicago")
MARKER = Path.home() / "Library/Application Support/ProjectHelix/last-alert-date"


def get_json(path):
    request = urllib.request.Request(
        API + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Project-Helix-monitor"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def healthy_scheduled_scrape(today):
    runs = get_json("/actions/workflows/scraper.yml/runs?event=schedule&per_page=100")["workflow_runs"]
    for run in runs:
        run_date = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")).astimezone(CHICAGO).date()
        if run_date != today or run["conclusion"] != "success":
            continue
        jobs = get_json(f"/actions/runs/{run['id']}/jobs?per_page=100")["jobs"]
        scrape = next((job for job in jobs if job["name"] == "scrape-and-update" and job["conclusion"] == "success"), None)
        if scrape is None:
            continue
        annotations = get_json(f"/check-runs/{scrape['id']}/annotations?per_page=100")
        if not any(
            item["annotation_level"] == "warning" and item["title"] in {"Empty scraper source", "Event cap hit"}
            for item in annotations
        ):
            return True
    return False


def main():
    now = datetime.now(CHICAGO)
    if (now.hour, now.minute) < (11, 15):
        return
    today = now.date().isoformat()
    if MARKER.exists() and MARKER.read_text().strip() == today:
        return
    try:
        if healthy_scheduled_scrape(now.date()):
            return
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Could not verify GitHub scraper: {error}")
    notification = (
        'display notification "No healthy scheduled scraper run today. Check GitHub Actions." '
        'with title "Project Helix" sound name "Glass"'
    )
    subprocess.run(["/usr/bin/osascript", "-e", notification], check=True)
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(today + "\n")


if __name__ == "__main__":
    main()
