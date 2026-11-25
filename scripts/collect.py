"""Collect public GitHub activity using the current gh sign-in."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
import subprocess
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

PHOENIX = ZoneInfo("America/Phoenix")
ROOT = Path(__file__).resolve().parent.parent


def api(path, **query):
    endpoint = path + ("?" + urlencode(query) if query else "")
    output = subprocess.check_output(["gh", "api", endpoint], text=True)
    return json.loads(output)


def pages(path, **query):
    for page in range(1, 101):
        rows = api(path, per_page=100, page=page, **query)
        if not isinstance(rows, list):
            raise ValueError(f"expected a list from {path}")
        yield from rows
        if len(rows) < 100:
            return
    raise ValueError(f"pagination limit reached for {path}")


def milestone(kind, row, stamp, title, body=""):
    return {
        "kind": kind,
        "time": stamp,
        "title": title,
        "url": row["html_url"],
        "evidence": (body or "").strip()[:1200],
    }


def collect(repo, start, stop):
    path = f"repos/{repo}"
    info = api(path)
    if info["visibility"] != "public":
        raise ValueError(f"{repo} is not a public repository")
    default_branch = info["default_branch"]
    results = []

    def in_window(value):
        return value and start <= value < stop

    for release in pages(f"{path}/releases"):
        if not release["draft"] and in_window(release["published_at"]):
            kind = "prerelease" if release["prerelease"] else "release"
            results.append(milestone(kind, release, release["published_at"],
                                     release["name"] or release["tag_name"], release["body"]))

    merge_shas = set()
    for pr in pages(f"{path}/pulls", state="all", sort="updated", direction="desc"):
        if pr["updated_at"] < start:
            break
        if pr["base"]["ref"] != default_branch:
            continue
        if in_window(pr["merged_at"]):
            merge_shas.add(pr["merge_commit_sha"])
            results.append(milestone("merged", pr, pr["merged_at"], pr["title"], pr["body"]))
        if in_window(pr["created_at"]) and pr["created_at"] != pr["merged_at"]:
            results.append(milestone("pr opened", pr, pr["created_at"], pr["title"], pr["body"]))
        if (in_window(pr["updated_at"]) and pr["updated_at"] != pr["created_at"]
                and (pr["closed_at"] is None or pr["updated_at"] < pr["closed_at"])):
            results.append(milestone("pr activity", pr, pr["updated_at"], pr["title"], pr["body"]))
        if pr["closed_at"] is None or pr["closed_at"] >= start:
            for comment in pages(f"{path}/issues/{pr['number']}/comments", since=start):
                if (in_window(comment["created_at"]) and comment["author_association"]
                        in ("OWNER", "MEMBER", "COLLABORATOR")):
                    results.append(milestone("pr comment", comment, comment["created_at"],
                                             pr["title"], comment["body"]))

    for commit in pages(f"{path}/commits", sha=default_branch, since=start, until=stop):
        stamp = commit["commit"]["committer"]["date"]
        if not in_window(stamp) or commit["sha"] in merge_shas or len(commit["parents"]) > 1:
            continue
        associated_prs = api(f"{path}/commits/{commit['sha']}/pulls")
        if any(pr["merged_at"] and pr["base"]["ref"] == default_branch for pr in associated_prs):
            continue
        title, _, body = commit["commit"]["message"].partition("\n")
        results.append(milestone("commit", commit, stamp, title, body))

    return repo, results


def utc_midnight(day):
    return datetime.combine(day, time.min, PHOENIX).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    yesterday = datetime.now(PHOENIX).date() - timedelta(days=1)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="first", type=date.fromisoformat, default=yesterday)
    parser.add_argument("--through", type=date.fromisoformat, default=yesterday)
    args = parser.parse_args()
    if not args.first <= args.through <= yesterday:
        parser.error("use a range of completed Phoenix dates")

    start, stop = utc_midnight(args.first), utc_midnight(args.through + timedelta(days=1))
    repos = json.loads((ROOT / "repos.json").read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:
        activity = dict(pool.map(lambda repo: collect(repo, start, stop), repos))
    print(json.dumps({"from": str(args.first), "through": str(args.through), "repos": activity}, indent=2))


if __name__ == "__main__":
    main()
