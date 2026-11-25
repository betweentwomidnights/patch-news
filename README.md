# patch news

this is the public development log for the collabage patch. the [website](https://github.com/betweentwomidnights/the-patch-next) reads this repo at runtime.

## run the daily review

use [TASK.md](TASK.md) for a standalone ChatGPT Work scheduled task on the web. choose GPT-6.2 Sol at standard speed and schedule it for 7:17 a.m. in `America/Phoenix`. connect GitHub with read access to the repos in [repos.json](repos.json) and write access here. the task uses your ChatGPT allowance and existing GitHub connection.

start with a manual run in the Work chat that will own the schedule. point its writes at the `preview` branch and replay november 19, 2026 and november 22, 2026 using the previous day's context. compare the first day’s small visualizer change with the installable Mac preview on the second day. verify the resulting commit on GitHub before pointing the saved task at `main`.

for a local replay with an existing GitHub CLI sign-in, run:

```sh
python3 scripts/collect.py --from 2026-11-20 --through 2026-11-23
```

the collector reads repo metadata, published releases, pull requests and default-branch commits. an older PR's current body can contain edits from after the replay date. use evidence dated on or before the day you're writing about.

## feed format

- `posts/YYYY-MM-DD.md` contains one or two short paragraphs with ordinary Markdown links to GitHub. the title lives in the index. use blank lines between paragraphs.
- `index.json` has a `version` of 1, a `checkedThrough` date or null, a `days` map keyed by date, and a `posts` array of date and title pairs. a post can also include a `summary`: one plain sentence, under 160 characters, that someone who has never used gary could follow (the site shows it under the title and in the archive). a post can also include a `diagram` with a title, two to five steps, and a caption. each step has a `label`, `detail`, and public GitHub `url`. see november 23 in the index for an example.
- each recorded day has a `status` of `posted` or `quiet` and a nonnegative integer count of `releases` and `merges`. count public releases, including published prereleases, by publication time. count distinct PRs merged to default branches by merge time. the chart leaves a gap for an unchecked date.
- for each posted day there is exactly one index entry and Markdown file. quiet days have no post. `checkedThrough` is the most recent successfully checked date.

commit a new post and its index entry together. user-facing corrections can be made by editing the dated file and its title in the same commit. use `python3 scripts/check.py` to check the index and its files before pushing.
