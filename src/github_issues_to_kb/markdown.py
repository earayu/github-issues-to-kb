from __future__ import annotations

import re
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})(\s+.+)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


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


def normalize_headings(markdown: str, offset: int = 2) -> str:
    """Demote user-authored headings without touching fenced code blocks."""
    lines: list[str] = []
    in_fence = False

    for line in markdown.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            lines.append(line)
            continue

        if not in_fence:
            match = HEADING_RE.match(line)
            if match:
                hashes, rest = match.groups()
                line = f"{'#' * min(6, len(hashes) + offset)}{rest}"

        lines.append(line)

    return "\n".join(lines)


def target_label(target: dict[str, Any] | None) -> str:
    if not target:
        return "unknown"

    typename = target.get("__typename")
    if typename == "PullRequest":
        merged = ", merged" if target.get("merged") else ""
        return f"PR #{target.get('number')} {target.get('title')} ({target.get('state')}{merged}) {target.get('url')}"
    if typename == "Issue":
        return f"Issue #{target.get('number')} {target.get('title')} ({target.get('state')}) {target.get('url')}"
    if typename == "Commit":
        oid = target.get("oid", "")
        short_oid = oid[:12] if oid else "unknown"
        return f"Commit {short_oid} {target.get('url')}"

    return str(target)


def timeline_event_summary(event: dict[str, Any]) -> str:
    actor = user_label(event.get("actor"))
    kind = event.get("__typename", "TimelineEvent")
    created = event.get("createdAt", "unknown-time")

    if kind == "AssignedEvent":
        return f"{created}: {actor} assigned {user_label(event.get('assignee'))}"
    if kind == "UnassignedEvent":
        return f"{created}: {actor} unassigned {user_label(event.get('assignee'))}"
    if kind == "LabeledEvent":
        return f"{created}: {actor} added label `{event.get('label', {}).get('name', 'unknown')}`"
    if kind == "UnlabeledEvent":
        return f"{created}: {actor} removed label `{event.get('label', {}).get('name', 'unknown')}`"
    if kind == "MilestonedEvent":
        return f"{created}: {actor} added milestone `{event.get('milestoneTitle', 'unknown')}`"
    if kind == "DemilestonedEvent":
        return f"{created}: {actor} removed milestone `{event.get('milestoneTitle', 'unknown')}`"
    if kind == "ClosedEvent":
        return f"{created}: {actor} closed this issue via {target_label(event.get('closer'))}"
    if kind == "ReopenedEvent":
        return f"{created}: {actor} reopened this issue"
    if kind == "ReferencedEvent":
        return f"{created}: {actor} referenced this issue from {target_label(event.get('commit'))}"
    if kind == "CrossReferencedEvent":
        return f"{created}: {actor} cross-referenced this issue from {target_label(event.get('source'))}"
    if kind == "RenamedTitleEvent":
        return (
            f"{created}: {actor} renamed title from `{event.get('previousTitle', '')}` "
            f"to `{event.get('currentTitle', '')}`"
        )
    if kind == "MarkedAsDuplicateEvent":
        return f"{created}: {actor} marked this issue as duplicate of {target_label(event.get('canonical'))}"
    if kind == "UnmarkedAsDuplicateEvent":
        return f"{created}: {actor} unmarked duplicate relationship with {target_label(event.get('canonical'))}"

    return f"{created}: {actor} {kind}"


def issue_to_markdown(issue: dict[str, Any]) -> str:
    labels = issue.get("labels", {}).get("nodes", [])
    assignees = issue.get("assignees", {}).get("nodes", [])
    milestone = issue.get("milestone")
    comments = issue.get("comments", {}).get("nodes", [])
    closing_prs = issue.get("closedByPullRequestsReferences", {}).get("nodes", [])
    timeline_events = issue.get("timelineItems", {}).get("nodes", [])

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
        normalize_headings(issue.get("body") or "_No body._"),
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
                    normalize_headings(comment.get("body") or "_No body._"),
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

    lines.extend(["## Timeline Events", ""])
    if timeline_events:
        for event in timeline_events:
            lines.append(f"- {timeline_event_summary(event)}")
        lines.append("")
    else:
        lines.extend(["_No timeline events found._", ""])

    return "\n".join(lines).rstrip() + "\n"
