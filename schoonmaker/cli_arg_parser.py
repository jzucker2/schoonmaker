from __future__ import annotations

from argparse import ArgumentParser, Namespace

DEFAULT_SAMPLE_FILE_PATH = "samples/final_draft_12_sample.fdx"


class CLIArgParser(object):
    def __init__(self):
        self.parser = ArgumentParser(
            prog="schoonmaker",
            description=(
                "Parse FDX; export JSON AST or Fountain; diff parse JSON "
                "or CI reports; Markdown for GitHub Actions; patch release "
                "helpers (next-semver, ci-select-pr, ci-label-pr, "
                "ci-release-notes)."
            ),
        )
        subparsers = self.parser.add_subparsers(dest="command", required=True)

        run_parser = subparsers.add_parser(
            "run", help="Parse FDX and print a short summary"
        )
        run_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to input FDX file",
        )
        run_parser.set_defaults(command="run")

        parse_parser = subparsers.add_parser(
            "parse", help="Convert FDX to JSON AST"
        )
        parse_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to .fdx file",
        )
        parse_parser.add_argument(
            "-o", "--output", type=str, help="Path to output JSON file"
        )
        parse_parser.add_argument(
            "--metadata",
            action="store_true",
            help="Add computed metadata (scene/character/line counts) to JSON",
        )
        parse_parser.add_argument(
            "--checksum",
            action="store_true",
            help="Add SHA-256 checksums for sections to JSON output",
        )
        parse_parser.add_argument(
            "--file-info",
            action="store_true",
            dest="file_info",
            help="Include source file path, size, and timestamps in JSON",
        )
        parse_parser.add_argument(
            "--list-items",
            action="store_true",
            dest="list_items",
            help=(
                "Include Final Draft <ListItems> (beat/outline board) in "
                "JSON; excluded from --metadata script totals"
            ),
        )
        parse_parser.add_argument(
            "--display-boards",
            action="store_true",
            dest="display_boards",
            help=(
                "Include Final Draft <DisplayBoards> (Story Map / Beat "
                "layout) in JSON; excluded from --metadata script totals"
            ),
        )
        parse_parser.set_defaults(command="parse")

        fountain_parser = subparsers.add_parser(
            "fountain", help="Convert FDX to Fountain"
        )
        fountain_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to .fdx file",
        )
        fountain_parser.add_argument(
            "-o", "--output", type=str, help="Path to output Fountain file"
        )
        fountain_parser.set_defaults(command="fountain")

        diff_parser = subparsers.add_parser(
            "diff",
            help="Compare two parse JSON files (before/after)",
        )
        diff_parser.add_argument(
            "--before",
            "-b",
            type=str,
            required=True,
            metavar="PATH",
            help="Earlier parse JSON baseline (-b for --before)",
        )
        diff_parser.add_argument(
            "--after",
            "-a",
            type=str,
            required=True,
            metavar="PATH",
            help="Later parse JSON (-a for --after)",
        )
        diff_parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Write diff report JSON to this path (default: stdout)",
        )
        diff_parser.set_defaults(command="diff")

        ci_parser = subparsers.add_parser(
            "ci-fdx-diff",
            help="Diff changed .fdx files between two git commits (CI)",
        )
        ci_parser.add_argument(
            "-o",
            "--output",
            type=str,
            required=True,
            help="Output directory for reports",
        )
        ci_parser.add_argument(
            "--base-sha",
            type=str,
            default="",
            dest="base_sha",
            help="Base commit (or CI_FDX_BASE_SHA)",
        )
        ci_parser.add_argument(
            "--head-sha",
            type=str,
            default="",
            dest="head_sha",
            help="Head commit (or CI_FDX_HEAD_SHA)",
        )
        ci_parser.add_argument(
            "--repo",
            type=str,
            default="",
            help="Git repository root (default: current directory)",
        )
        ci_parser.add_argument(
            "--list-items",
            action="store_true",
            dest="list_items",
            help=(
                "Parse with --list-items (or set CI_FDX_LIST_ITEMS=1); "
                "diff reports include list_items when non-empty"
            ),
        )
        ci_parser.add_argument(
            "--display-boards",
            action="store_true",
            dest="display_boards",
            help=(
                "Parse with --display-boards (or CI_FDX_DISPLAY_BOARDS=1); "
                "diff includes display_boards when non-empty"
            ),
        )
        ci_parser.set_defaults(command="ci-fdx-diff")

        report_md_parser = subparsers.add_parser(
            "ci-report-md",
            help=(
                "Emit Markdown from ci-fdx-diff *-diff.json (GitHub Summary)"
            ),
        )
        report_md_parser.add_argument(
            "reports_dir",
            nargs="?",
            default=".",
            help="Directory with *-diff.json and optional path-index.tsv",
        )
        report_md_parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Write Markdown here (default: stdout)",
        )
        report_md_parser.set_defaults(command="ci-report-md")

        release_notes_parser = subparsers.add_parser(
            "ci-release-notes",
            help=("Compose release / PR Markdown from ci-fdx-diff reports"),
        )
        release_notes_parser.add_argument(
            "reports_dir",
            nargs="?",
            default=".",
            help="Directory with *-diff.json (default: .)",
        )
        release_notes_parser.add_argument(
            "--version",
            type=str,
            required=True,
            help="Release version string (e.g. v1.2.4)",
        )
        release_notes_parser.add_argument(
            "--pr",
            type=int,
            dest="pr_number",
            help="Merged pull request number",
        )
        release_notes_parser.add_argument(
            "--pr-title",
            type=str,
            dest="pr_title",
            help="Pull request title for the header",
        )
        release_notes_parser.add_argument(
            "--pr-url",
            type=str,
            dest="pr_url",
            help="Pull request URL for the header link",
        )
        release_notes_parser.add_argument(
            "--intro",
            type=str,
            help="Optional intro paragraph under the release heading",
        )
        release_notes_parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Write Markdown here (default: stdout)",
        )
        release_notes_parser.set_defaults(command="ci-release-notes")

        select_pr_parser = subparsers.add_parser(
            "ci-select-pr",
            help=("Read gh pr list JSON from stdin; require exactly one PR"),
        )
        select_pr_parser.add_argument(
            "--label",
            type=str,
            default="",
            help="Label name for error messages (filter via gh)",
        )
        select_pr_parser.add_argument(
            "--allow-empty",
            action="store_true",
            dest="allow_empty",
            help="Exit 0 when no PRs (for CI skip); still fail if many",
        )
        select_pr_parser.add_argument(
            "--actions-output",
            action="store_true",
            dest="actions_output",
            help="Append skip/pr fields to $GITHUB_OUTPUT",
        )
        select_pr_parser.add_argument(
            "--json-out",
            type=str,
            default="",
            dest="json_out",
            help="Write selected PR JSON to this path",
        )
        select_pr_parser.set_defaults(command="ci-select-pr")

        daily_parser = subparsers.add_parser(
            "ci-daily-release",
            help=(
                "Merge one labeled PR, cut patch GitHub Release, FDX report"
            ),
        )
        daily_parser.add_argument(
            "--label",
            type=str,
            default="",
            help=(
                "PR label to ship (default: release-ready or RELEASE_LABEL)"
            ),
        )
        daily_parser.add_argument(
            "--default-branch",
            type=str,
            default="",
            dest="default_branch",
            help=(
                "Branch to merge into (default: master or DEFAULT_BRANCH; "
                "use main if that is your default)"
            ),
        )
        daily_parser.add_argument(
            "--reports-dir",
            type=str,
            default="fdx-reports",
            dest="reports_dir",
            help="Output directory for ci-fdx-diff (default: fdx-reports)",
        )
        daily_parser.add_argument(
            "--notes-file",
            type=str,
            default="RELEASE_NOTES.md",
            dest="notes_file",
            help="Release notes Markdown path (default: RELEASE_NOTES.md)",
        )
        daily_parser.add_argument(
            "--merge-method",
            type=str,
            default="squash",
            dest="merge_method",
            choices=("squash", "merge", "rebase"),
            help="gh pr merge style (default: squash)",
        )
        daily_parser.add_argument(
            "--repo",
            type=str,
            default="",
            help="Git repository root (default: current directory)",
        )
        daily_parser.add_argument(
            "--no-actions-output",
            action="store_true",
            dest="no_actions_output",
            help="Do not write skip/tag fields to $GITHUB_OUTPUT",
        )
        daily_parser.add_argument(
            "--no-step-summary",
            action="store_true",
            dest="no_step_summary",
            help="Do not append to $GITHUB_STEP_SUMMARY",
        )
        daily_parser.set_defaults(command="ci-daily-release")

        label_pr_parser = subparsers.add_parser(
            "ci-label-pr",
            help=(
                "Add release label to a PR when head branch matches a prefix"
            ),
        )
        label_pr_parser.add_argument(
            "--pr",
            type=str,
            default="",
            dest="pr_number",
            help="Pull request number (or env PR_NUMBER)",
        )
        label_pr_parser.add_argument(
            "--head-ref",
            type=str,
            default="",
            dest="head_ref",
            help=("PR head branch name (or PR_HEAD_REF / GITHUB_HEAD_REF)"),
        )
        label_pr_parser.add_argument(
            "--label",
            type=str,
            default="",
            help=("Label to add (default: release-ready or RELEASE_LABEL)"),
        )
        label_pr_parser.add_argument(
            "--branch-prefix",
            type=str,
            default="",
            dest="branch_prefix",
            help=(
                "Head branch prefix to match (default: writing/ or "
                "PR_BRANCH_PREFIX); uses startswith"
            ),
        )
        label_pr_parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Decide and report without calling gh",
        )
        label_pr_parser.add_argument(
            "--no-actions-output",
            action="store_true",
            dest="no_actions_output",
            help="Do not write labeled= to $GITHUB_OUTPUT",
        )
        label_pr_parser.set_defaults(command="ci-label-pr")

        next_semver_parser = subparsers.add_parser(
            "next-semver",
            help="Print next patch semver (or latest tag)",
        )
        next_semver_parser.add_argument(
            "version",
            nargs="?",
            default=None,
            help="Version to bump (e.g. 1.2.3 or v1.2.3)",
        )
        next_semver_parser.add_argument(
            "--from-tags",
            action="store_true",
            dest="from_tags",
            help="Bump after latest semver git tag",
        )
        next_semver_parser.add_argument(
            "--latest-tag",
            action="store_true",
            dest="latest_tag",
            help="Print latest semver git tag (no bump)",
        )
        next_semver_parser.add_argument(
            "--default",
            type=str,
            default="v0.0.0",
            help="Baseline when --from-tags finds no tags (default v0.0.0)",
        )
        next_semver_parser.add_argument(
            "--repo",
            type=str,
            default="",
            help="Git repository root (default: current directory)",
        )
        next_semver_parser.set_defaults(command="next-semver")

    def _parse_args(self) -> Namespace:
        return self.parser.parse_args()

    def get_args(self) -> Namespace:
        return self._parse_args()

    @classmethod
    def get_cli_args(cls) -> Namespace:
        parser = cls()
        return parser.get_args()
