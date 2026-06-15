from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .exporter import GitHubIssueExporter, parse_repo
from .markdown import issue_to_markdown, markdown_filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="github-issues-to-kb",
        description="Export GitHub issues into raw JSONL and Markdown.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export issues from a repository.")
    export.add_argument("repo", help="Repository in owner/name form, for example apecloud/kubeblocks.")
    export.add_argument("--output", "-o", default="exports/issues", help="Output directory.")
    export.add_argument("--limit", type=int, default=None, help="Maximum number of issues to export.")
    export.add_argument("--page-size", type=int, default=50, help="GraphQL issue page size.")
    export.add_argument(
        "--state",
        choices=["all", "open", "closed"],
        default="all",
        help="Issue state filter.",
    )
    export.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable containing a GitHub token.",
    )

    return parser


def run_export(args: argparse.Namespace) -> int:
    token = os.environ.get(args.token_env)
    if not token:
        print(f"Missing GitHub token: set {args.token_env}", file=sys.stderr)
        return 2

    owner, name = parse_repo(args.repo)
    out_dir = Path(args.output)
    markdown_dir = out_dir / "markdown"
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown_dir.mkdir(parents=True, exist_ok=True)

    exporter = GitHubIssueExporter(token=token)
    raw_path = out_dir / "issues.raw.jsonl"
    count = 0

    with raw_path.open("w", encoding="utf-8") as raw_file:
        for issue in exporter.iter_issues(
            owner=owner,
            name=name,
            state=args.state,
            limit=args.limit,
            page_size=args.page_size,
        ):
            raw_file.write(json.dumps(issue, ensure_ascii=False, separators=(",", ":")) + "\n")
            md_path = markdown_dir / markdown_filename(issue)
            md_path.write_text(issue_to_markdown(issue), encoding="utf-8")
            count += 1

    manifest = {
        "repo": f"{owner}/{name}",
        "issue_count": count,
        "state": args.state,
        "limit": args.limit,
        "raw_jsonl": str(raw_path),
        "markdown_dir": str(markdown_dir),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Exported {count} issues to {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export":
        return run_export(args)

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

