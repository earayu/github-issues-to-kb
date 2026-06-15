from __future__ import annotations

import re
from typing import Any


def markdown_filename(issue: dict[str, Any]) -> str:
    title = re.sub(r"[^a-zA-Z0-9]+", "-", issue["title"].lower()).strip("-")
    title = title[:80] or "issue"
    return f"{issue['number']}-{title}.md"


def user_label(user: dict[str, Any] | None) -> str:
    if not user:
        return "unknown"
    login = user.get("login") or "unknown"
    url = user.get("url")
    return f"{login} ({url})" if url else login


def list_names(items: list[dict[str, Any]], key: str = "name") -> str:
    values = [item.get(key) for item in items if item.get(key)]
    return ", ".join(values) if values else "none"


def issue_to_markdown(issue: dict[str, Any]) -> str:
    labels = issue.get("labels", {}).get("nodes", [])
    assignees = issue.get("assignees", {}).get("nodes", [])
    milestone = issue.get("milestone")
    comments = issue.get("comments", {}).get("nodes", [])
    closing_prs = issue.get("closedByPullRequestsReferences", {}).get("nodes", [])

    lines: list[str] = [
        f"# Issue #{issue['number']}: {issue['title']}",
        "",
        "## Metadata",
        "",
        f"- repo: {issue.get('repo', 'unknown')}",
        f"- url: {issue['url']}",
        f"- state: {issue['state']}",
        f"- stateReason: {issue.get('stateReason') or 'none'}",
        f"- author: {user_label(issue.get('author'))}",
        f"- labels: {list_names(labels)}",
        f"- assignees: {list_names(assignees, key='login')}",
        f"- milestone: {milestone['title'] if milestone else 'none'}",
        f"- createdAt: {issue['createdAt']}",
        f"- updatedAt: {issue['updatedAt']}",
        f"- closedAt: {issue.get('closedAt') or 'none'}",
        "",
        "## Body",
        "",
        issue.get("body") or "_No body._",
        "",
    ]

    lines.extend(["## Comments", ""])
    if comments:
        for index, comment in enumerate(comments, start=1):
            lines.extend(
                [
                    f"### Comment {index} by {user_label(comment.get('author'))}",
                    "",
                    f"- url: {comment['url']}",
                    f"- createdAt: {comment['createdAt']}",
                    f"- updatedAt: {comment['updatedAt']}",
                    "",
                    comment.get("body") or "_No body._",
                    "",
                ]
            )
    else:
        lines.extend(["_No comments._", ""])

    lines.extend(["## Closing Pull Requests", ""])
    if closing_prs:
        for pull in closing_prs:
            merged = "merged" if pull.get("merged") else pull.get("state", "unknown")
            lines.append(
                f"- #{pull['number']} {pull['title']} ({merged}) {pull['url']}"
            )
        lines.append("")
    else:
        lines.extend(["_No closing pull requests found._", ""])

    return "\n".join(lines).rstrip() + "\n"

