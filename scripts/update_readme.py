#!/usr/bin/env python3
"""Refresh the auto-updated block in README.md between the HQ markers. Stdlib only.

Source (public, no auth): the VAS blog RSS feed. Deterministic and idempotent —
safe to run any time; exits 0 with no write if nothing changed.
"""

import re
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

README = Path(__file__).resolve().parents[1] / "README.md"
START, END = "<!-- HQ:START -->", "<!-- HQ:END -->"

# Placeholder until swing-lab's X pulse goes live; then this line points at the latest post.
PULSE_LINE = "- 📈 Latest Swing Lab pulse: coming soon on X"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "guillearria-readme-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def latest_vas_post():
    rss = ElementTree.fromstring(fetch("https://vertical-agent-solutions.pages.dev/rss.xml"))
    items = rss.findall("./channel/item")
    # The feed's item order is alphabetical by slug, not chronological — sort by pubDate.
    def when(item):
        try:
            return parsedate_to_datetime(item.findtext("pubDate"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)
    latest = max(items, key=when)
    return latest.findtext("title"), latest.findtext("link")


def main():
    text = README.read_text()
    lines = [
        f"_Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} by [an automated pipeline](https://github.com/guillearria/guillearria/blob/main/scripts/update_readme.py):_",
        "",
    ]
    try:
        title, link = latest_vas_post()
        lines.append(f"- 📝 Latest published guide: [{title}]({link})")
    except Exception:
        # Feed hiccup: keep the previous guide line rather than silently dropping it.
        prev = re.search(r"^- 📝 .+$", text, flags=re.M)
        if prev:
            lines.append(prev.group(0))
    lines.append(PULSE_LINE)

    block = f"{START}\n{lines[0]}\n" + "\n".join(lines[1:]) + f"\n{END}"
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), block, text, flags=re.S)
    if new != text:
        README.write_text(new)
        print("README.md updated")
    else:
        print("no change")


if __name__ == "__main__":
    main()
