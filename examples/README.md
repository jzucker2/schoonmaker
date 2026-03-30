# GitHub Actions examples

Copy **`requirements-ci.txt`** to the root of your repo and set **org + tag** for schoonmaker.

| File | When to use |
|------|-------------|
| **`github-actions-fdx-changes-pr.yml`** | **Pull requests** — sets `CI_FDX_BASE_SHA` / `CI_FDX_HEAD_SHA` from the PR, runs **`schoonmaker ci-fdx-diff`**. |
| **`github-actions-fdx-changes-push.yml`** | **Pushes to `main`/`master`** — same command; push **`before`** may be all zeros; **`ci-fdx-diff`** resolves the parent of **`after`** in Python when needed. |

Use one or both. For PR review, **`pr`** is usually enough; **`push`** is for post-merge analysis.

There is no cron example in the repo: add your own if you need it.
