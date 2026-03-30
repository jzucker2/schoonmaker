# GitHub Actions examples

Copy **`requirements-ci.txt`** to the root of your repo and set **org + tag** for schoonmaker.

| File | When to use |
|------|-------------|
| **`github-actions-fdx-changes-pr.yml`** | **Pull requests** — `BASE_SHA` / `HEAD_SHA` from the PR (`env` only). |
| **`github-actions-fdx-changes-push.yml`** | **Pushes to `main`/`master`** — `before` → `after` (with a step for empty `before`). |

Use one or both. For PR review, **`pr`** is usually enough; **`push`** is for post-merge analysis.

There is no cron example in the repo: add your own if you need it.
