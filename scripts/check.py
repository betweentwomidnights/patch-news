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


def validate_diagram(diagram, key):
    def valid_text(value, limit):
        return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and "—" not in value

    check(isinstance(diagram, dict), f"invalid diagram for {key}")
    check(valid_text(diagram.get("title"), 80), f"invalid diagram title for {key}")
    check(valid_text(diagram.get("caption"), 220), f"invalid diagram caption for {key}")
    steps = diagram.get("steps")
    check(isinstance(steps, list) and 2 <= len(steps) <= 5, f"invalid diagram steps for {key}")
    for step in steps:
        check(isinstance(step, dict), f"invalid diagram step for {key}")
        check(valid_text(step.get("label"), 60), f"invalid diagram label for {key}")
        check(valid_text(step.get("detail"), 150), f"invalid diagram detail for {key}")
        url = step.get("url")
        check(valid_text(url, 500) and re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+(?:/[^\s]*)?", url),
              f"invalid diagram link for {key}")


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
        if "summary" in post:
            summary = post["summary"]
            check(isinstance(summary, str) and 0 < len(summary.strip()) <= 160 and "—" not in summary,
                  f"invalid summary for {key}")
        if "diagram" in post:
            validate_diagram(post["diagram"], key)
        markdown = (ROOT / "posts" / f"{key}.md").read_text().strip()
        check(0 < len(markdown) < 8000 and "—" not in markdown, f"invalid Markdown for {key}")
        links = re.findall(r"\[[^\]\n]+\]\(([^)]+)\)", markdown)
        check(links and all(link.startswith("https://github.com/") for link in links),
              f"missing or invalid source links for {key}")
    print(f"checked {len(days)} days and {len(posts)} posts")


if __name__ == "__main__":
    main()
