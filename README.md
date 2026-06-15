# github-issues-to-kb

Export GitHub issues into two knowledge-base-friendly formats:

- raw JSONL, one issue per line
- Markdown documents, one issue per file

The exporter uses GitHub GraphQL so it can keep issue metadata, labels,
assignees, milestones, comments, and closing pull requests together.

## Install

```bash
pipx install git+https://github.com/earayu/github-issues-to-kb.git
```

For local development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Usage

Create a GitHub token with repository read access and export a small batch:

```bash
export GITHUB_TOKEN=ghp_xxx

github-issues-to-kb export apecloud/kubeblocks \
  --limit 10 \
  --output exports/kubeblocks-sample
```

Export all issues:

```bash
github-issues-to-kb export apecloud/kubeblocks \
  --state all \
  --output exports/kubeblocks
```

Output layout:

```text
exports/kubeblocks/
├── issues.raw.jsonl
├── manifest.json
└── markdown/
    ├── 10277-parameters-list-for-each-db-type.md
    └── ...
```

## Notes

- `issues.raw.jsonl` is the durable source of truth. Keep it if you later want
  to change chunking, embeddings, or Markdown rendering.
- Markdown files are optimized for knowledge-base ingestion and human review.
- Comments are fully paginated per issue.
- Closing pull request references are included when GitHub exposes them for an
  issue.

