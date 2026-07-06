#!/usr/bin/env python3
"""Refresh the auto-updated block in README.md between the HQ markers. Stdlib only.

Sources (all public, no auth): the VAS blog RSS feed, the Global Observatory data
freshness stamp, and recent public GitHub activity. Deterministic and idempotent —
safe to run any time; exits 0 with no write if nothing changed.
"""

import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

README = Path(__file__).resolve().parents[1] / "README.md"
START, END = "<!-- HQ:START -->", "<!-- HQ:END -->"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "guillearria-readme-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def latest_vas_post():
    rss = ElementTree.fromstring(fetch("https://vertical-agent-solutions.pages.dev/rss.xml"))
    item = rss.find("./channel/item")
    return item.findtext("title"), item.findtext("link")


def observatory_freshness():
    data = json.loads(fetch("https://guillearria.github.io/global-observatory/data/events.json"))
    stamp = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - stamp).days
    return "today" if days == 0 else ("yesterday" if days == 1 else f"{days} days ago")


def recent_activity():
    events = json.loads(fetch("https://api.github.com/users/guillearria/events/public"))
    repos = []
    for e in events:
        name = e.get("repo", {}).get("name", "").split("/")[-1]
        if e.get("type") == "PushEvent" and name and name not in repos:
            repos.append(name)
    return repos[:3]


def main():
    lines = [
        f"_Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} by [an automated pipeline](https://github.com/guillearria/guillearria/blob/main/scripts/update_readme.py):_",
        "",
    ]
    try:
        title, link = latest_vas_post()
        lines.append(f"- 📝 Latest published guide: [{title}]({link})")
    except Exception:
        pass
    try:
        lines.append(f"- 🌍 Global Observatory data last refreshed: **{observatory_freshness()}**")
    except Exception:
        pass
    try:
        repos = recent_activity()
        if repos:
            lines.append(f"- 🔨 Recently pushed: {', '.join(f'`{r}`' for r in repos)}")
    except Exception:
        pass

    text = README.read_text()
    block = f"{START}\n{lines[0]}\n" + "\n".join(lines[1:]) + f"\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    if new != text:
        README.write_text(new)
        print("README.md updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
