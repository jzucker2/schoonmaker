# GitHub Actions examples

Copy **`requirements-ci.txt`** to the root of your repo and set **org + tag** for schoonmaker.

| File | When to use |
|------|-------------|
| **`github-actions-fdx-changes-pr.yml`** | **Pull requests** — sets `CI_FDX_BASE_SHA` / `CI_FDX_HEAD_SHA` from the PR, runs **`schoonmaker ci-fdx-diff`**. |
| **`github-actions-fdx-changes-push.yml`** | **Pushes to `main`/`master`** — same command; push **`before`** may be all zeros; **`ci-fdx-diff`** resolves the parent of **`after`** in Python when needed. |
| **`github-actions-fdx-daily-release.yml`** | **Daily cron + manual** — after `pip install`, runs **`schoonmaker ci-daily-release`** (no extra scripts to copy). |

Use the PR and/or push workflows for review and post-merge analysis. Add the daily release workflow when you want a scheduled “ship the labeled PR” path.

**Daily release setup**

1. Copy **`github-actions-fdx-daily-release.yml`** → **`.github/workflows/`**
2. Copy **`requirements-ci.txt`** to the repo root and pin a schoonmaker tag that includes **`ci-daily-release`**
3. Create the **`release-ready`** label (or change `RELEASE_LABEL` in the workflow)

**Configurable defaults** (also documented in the workflow YAML header)

| Setting | Default | Notes |
|---------|---------|--------|
| `DEFAULT_BRANCH` | `master` | Set to `main` if that is your default branch |
| `RELEASE_LABEL` | `release-ready` | Exactly one open PR with this label targeting the default branch; zero → skip; many → fail |
| `schedule.cron` | `0 9 * * *` | **UTC only.** 09:00 UTC ≈ 02:00 America/Los_Angeles (PST). For 02:00 UTC use `0 2 * * *` |
| Merge method | squash | Override with `schoonmaker ci-daily-release --merge-method merge` |
| First tag | `v0.0.1` | When no semver tags exist (`v0.0.0` + patch) |

Permissions: **`contents: write`**, **`pull-requests: write`**. If branch protection blocks `GITHUB_TOKEN`, set secret **`RELEASE_TOKEN`** (PAT).

**Beat board in CI:** To include `<ListItems>` / `<DisplayBoards>` in the artifact JSON and in each `*-diff.json` summary, set **`CI_FDX_LIST_ITEMS`** / **`CI_FDX_DISPLAY_BOARDS`** to **`1`**, **`true`**, **`yes`**, or **`on`**, and/or pass **`--list-items`** / **`--display-boards`** on **`ci-fdx-diff`**. CLI and env are OR’d (either enables the option).

**Job summary in the GitHub UI:** The example workflows append Markdown to **`GITHUB_STEP_SUMMARY`** via **`schoonmaker ci-report-md fdx-reports`**, so the workflow run page shows tables for scene/word deltas per changed script. For pull requests, a [**sticky PR comment**](https://github.com/marocchino/sticky-pull-request-comment) or **`actions/github-script`** can post the same Markdown on the PR for visibility (needs `pull-requests: write`). **`ci-daily-release`** posts the release notes body as a PR comment automatically.
