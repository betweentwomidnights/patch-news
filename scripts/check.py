"""Validate the news feed and its matching Markdown files."""

from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def check(condition, message):
    if not condition:
        raise ValueError(message)


def iso_day(value):
    return isinstance(value, str) and date.fromisoformat(value).isoformat() == value


def main():
    index = json.loads((ROOT / "index.json").read_text())
    days, posts = index["days"], index["posts"]
    check(index["version"] == 1, "unsupported index version")
    check(index["checkedThrough"] == max(days, default=None), "wrong checked-through date")
    posted_days = set()
    for key, day in days.items():
        check(iso_day(key), f"invalid date {key}")
        check(day["status"] in ("posted", "quiet"), f"invalid status for {key}")
        for name in ("releases", "merges"):
            check(type(day[name]) is int and day[name] >= 0, f"invalid {name} for {key}")
        if day["status"] == "posted":
            posted_days.add(key)

    check(len(posts) == len(posted_days), "wrong number of index entries")
    check({post["date"] for post in posts} == posted_days, "index dates don't match posted days")
    check({post.stem for post in (ROOT / "posts").glob("*.md")} == posted_days,
          "post files don't match posted days")
    for post in posts:
        key, title = post["date"], post["title"]
        check(0 < len(title.strip()) <= 100 and "—" not in title, f"invalid title for {key}")
        markdown = (ROOT / "posts" / f"{key}.md").read_text().strip()
        check(0 < len(markdown) < 8000 and "—" not in markdown, f"invalid Markdown for {key}")
        links = re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", markdown)
        check(links and all(link.startswith("https://github.com/") for link in links),
              f"missing or invalid source links for {key}")
    print(f"checked {len(days)} days and {len(posts)} posts")


if __name__ == "__main__":
    main()
