# GitHub Actions examples

Copy **`requirements-ci.txt`** to the root of your repo and set **org + tag** for schoonmaker.

| File | When to use |
|------|-------------|
| **`github-actions-fdx-changes-pr.yml`** | **Pull requests** — sets `CI_FDX_BASE_SHA` / `CI_FDX_HEAD_SHA` from the PR, runs **`schoonmaker ci-fdx-diff`**. |
| **`github-actions-fdx-changes-push.yml`** | **Pushes to `main`/`master`** — same command; push **`before`** may be all zeros; **`ci-fdx-diff`** resolves the parent of **`after`** in Python when needed. |

Use one or both. For PR review, **`pr`** is usually enough; **`push`** is for post-merge analysis.

**Beat board in CI:** To include `<ListItems>` / `<DisplayBoards>` in the artifact JSON and in each `*-diff.json` summary, set **`CI_FDX_LIST_ITEMS`** / **`CI_FDX_DISPLAY_BOARDS`** to **`1`**, **`true`**, **`yes`**, or **`on`**, and/or pass **`--list-items`** / **`--display-boards`** on **`ci-fdx-diff`**. CLI and env are OR’d (either enables the option).

**Job summary in the GitHub UI:** The example workflows append Markdown to **`GITHUB_STEP_SUMMARY`** via **`schoonmaker ci-report-md fdx-reports`**, so the workflow run page shows tables for scene/word deltas per changed script. For pull requests, a [**sticky PR comment**](https://github.com/marocchino/sticky-pull-request-comment) or **`actions/github-script`** can post the same Markdown on the PR for visibility (needs `pull-requests: write`).

There is no cron example in the repo: add your own if you need it.
