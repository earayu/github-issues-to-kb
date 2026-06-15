from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


GRAPHQL_ENDPOINT = "https://api.github.com/graphql"


ISSUES_QUERY = """
query IssuesForKb(
  $owner: String!
  $name: String!
  $first: Int!
  $after: String
  $states: [IssueState!]
) {
  repository(owner: $owner, name: $name) {
    issues(first: $first, after: $after, states: $states, orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        number
        title
        state
        stateReason
        body
        url
        createdAt
        updatedAt
        closedAt
        author {
          login
          url
        }
        labels(first: 50) {
          nodes {
            name
            color
            description
          }
        }
        assignees(first: 20) {
          nodes {
            login
            url
          }
        }
        milestone {
          title
          state
          dueOn
          url
        }
        comments(first: 100) {
          totalCount
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            author {
              login
              url
            }
            body
            url
            createdAt
            updatedAt
          }
        }
        closedByPullRequestsReferences(first: 20) {
          nodes {
            number
            title
            url
            state
            merged
            mergedAt
            author {
              login
              url
            }
          }
        }
        timelineItems(
          first: 100
          itemTypes: [
            ASSIGNED_EVENT
            CLOSED_EVENT
            CROSS_REFERENCED_EVENT
            DEMILESTONED_EVENT
            LABELED_EVENT
            MARKED_AS_DUPLICATE_EVENT
            MILESTONED_EVENT
            REFERENCED_EVENT
            RENAMED_TITLE_EVENT
            REOPENED_EVENT
            UNASSIGNED_EVENT
            UNLABELED_EVENT
            UNMARKED_AS_DUPLICATE_EVENT
          ]
        ) {
          totalCount
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            __typename
            ... on AssignedEvent {
              createdAt
              actor {
                login
                url
              }
              assignee {
                __typename
                ... on User {
                  login
                  url
                }
                ... on Bot {
                  login
                  url
                }
                ... on Mannequin {
                  login
                  url
                }
              }
            }
            ... on ClosedEvent {
              createdAt
              actor {
                login
                url
              }
              closer {
                __typename
                ... on Commit {
                  oid
                  url
                }
                ... on PullRequest {
                  number
                  title
                  url
                  state
                  merged
                }
              }
            }
            ... on CrossReferencedEvent {
              createdAt
              actor {
                login
                url
              }
              source {
                __typename
                ... on Issue {
                  number
                  title
                  url
                  state
                }
                ... on PullRequest {
                  number
                  title
                  url
                  state
                  merged
                }
              }
            }
            ... on DemilestonedEvent {
              createdAt
              actor {
                login
                url
              }
              milestoneTitle
            }
            ... on LabeledEvent {
              createdAt
              actor {
                login
                url
              }
              label {
                name
                color
                description
              }
            }
            ... on MarkedAsDuplicateEvent {
              createdAt
              actor {
                login
                url
              }
              canonical {
                __typename
                ... on Issue {
                  number
                  title
                  url
                  state
                }
                ... on PullRequest {
                  number
                  title
                  url
                  state
                  merged
                }
              }
            }
            ... on MilestonedEvent {
              createdAt
              actor {
                login
                url
              }
              milestoneTitle
            }
            ... on ReferencedEvent {
              createdAt
              actor {
                login
                url
              }
              commit {
                oid
                url
              }
            }
            ... on RenamedTitleEvent {
              createdAt
              actor {
                login
                url
              }
              currentTitle
              previousTitle
            }
            ... on ReopenedEvent {
              createdAt
              actor {
                login
                url
              }
            }
            ... on UnassignedEvent {
              createdAt
              actor {
                login
                url
              }
              assignee {
                __typename
                ... on User {
                  login
                  url
                }
                ... on Bot {
                  login
                  url
                }
                ... on Mannequin {
                  login
                  url
                }
              }
            }
            ... on UnlabeledEvent {
              createdAt
              actor {
                login
                url
              }
              label {
                name
                color
                description
              }
            }
            ... on UnmarkedAsDuplicateEvent {
              createdAt
              actor {
                login
                url
              }
              canonical {
                __typename
                ... on Issue {
                  number
                  title
                  url
                  state
                }
                ... on PullRequest {
                  number
                  title
                  url
                  state
                  merged
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


COMMENTS_QUERY = """
query IssueCommentsForKb(
  $owner: String!
  $name: String!
  $number: Int!
  $after: String
) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      comments(first: 100, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          author {
            login
            url
          }
          body
          url
          createdAt
          updatedAt
        }
      }
    }
  }
}
"""


TIMELINE_QUERY = """
query IssueTimelineForKb(
  $owner: String!
  $name: String!
  $number: Int!
  $after: String
) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      timelineItems(
        first: 100
        after: $after
        itemTypes: [
          ASSIGNED_EVENT
          CLOSED_EVENT
          CROSS_REFERENCED_EVENT
          DEMILESTONED_EVENT
          LABELED_EVENT
          MARKED_AS_DUPLICATE_EVENT
          MILESTONED_EVENT
          REFERENCED_EVENT
          RENAMED_TITLE_EVENT
          REOPENED_EVENT
          UNASSIGNED_EVENT
          UNLABELED_EVENT
          UNMARKED_AS_DUPLICATE_EVENT
        ]
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          __typename
          ... on AssignedEvent {
            createdAt
            actor {
              login
              url
            }
            assignee {
              __typename
              ... on User {
                login
                url
              }
              ... on Bot {
                login
                url
              }
              ... on Mannequin {
                login
                url
              }
            }
          }
          ... on ClosedEvent {
            createdAt
            actor {
              login
              url
            }
            closer {
              __typename
              ... on Commit {
                oid
                url
              }
              ... on PullRequest {
                number
                title
                url
                state
                merged
              }
            }
          }
          ... on CrossReferencedEvent {
            createdAt
            actor {
              login
              url
            }
            source {
              __typename
              ... on Issue {
                number
                title
                url
                state
              }
              ... on PullRequest {
                number
                title
                url
                state
                merged
              }
            }
          }
          ... on DemilestonedEvent {
            createdAt
            actor {
              login
              url
            }
            milestoneTitle
          }
          ... on LabeledEvent {
            createdAt
            actor {
              login
              url
            }
            label {
              name
              color
              description
            }
          }
          ... on MarkedAsDuplicateEvent {
            createdAt
            actor {
              login
              url
            }
            canonical {
              __typename
              ... on Issue {
                number
                title
                url
                state
              }
              ... on PullRequest {
                number
                title
                url
                state
                merged
              }
            }
          }
          ... on MilestonedEvent {
            createdAt
            actor {
              login
              url
            }
            milestoneTitle
          }
          ... on ReferencedEvent {
            createdAt
            actor {
              login
              url
            }
            commit {
              oid
              url
            }
          }
          ... on RenamedTitleEvent {
            createdAt
            actor {
              login
              url
            }
            currentTitle
            previousTitle
          }
          ... on ReopenedEvent {
            createdAt
            actor {
              login
              url
            }
          }
          ... on UnassignedEvent {
            createdAt
            actor {
              login
              url
            }
            assignee {
              __typename
              ... on User {
                login
                url
              }
              ... on Bot {
                login
                url
              }
              ... on Mannequin {
                login
                url
              }
            }
          }
          ... on UnlabeledEvent {
            createdAt
            actor {
              login
              url
            }
            label {
              name
              color
              description
            }
          }
          ... on UnmarkedAsDuplicateEvent {
            createdAt
            actor {
              login
              url
            }
            canonical {
              __typename
              ... on Issue {
                number
                title
                url
                state
              }
              ... on PullRequest {
                number
                title
                url
                state
                merged
              }
            }
          }
        }
      }
    }
  }
}
"""


def parse_repo(repo: str) -> tuple[str, str]:
    parts = repo.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Repository must be in owner/name form.")
    return parts[0], parts[1]


def state_to_graphql(state: str) -> list[str] | None:
    if state == "all":
        return None
    if state == "open":
        return ["OPEN"]
    if state == "closed":
        return ["CLOSED"]
    raise ValueError(f"Unsupported issue state: {state}")


@dataclass
class GitHubIssueExporter:
    token: str
    endpoint: str = GRAPHQL_ENDPOINT

    def graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github+json",
                "User-Agent": "github-issues-to-kb",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub GraphQL HTTP {exc.code}: {body}") from exc

        if "errors" in data:
            raise RuntimeError(f"GitHub GraphQL errors: {data['errors']}")
        return data["data"]

    def iter_issues(
        self,
        owner: str,
        name: str,
        state: str = "all",
        limit: int | None = None,
        page_size: int = 50,
    ) -> Iterator[dict[str, Any]]:
        exported = 0
        after: str | None = None
        states = state_to_graphql(state)

        while True:
            if limit is not None and exported >= limit:
                return

            first = min(page_size, limit - exported) if limit is not None else page_size
            data = self.graphql(
                ISSUES_QUERY,
                {
                    "owner": owner,
                    "name": name,
                    "first": first,
                    "after": after,
                    "states": states,
                },
            )
            issues = data["repository"]["issues"]

            for issue in issues["nodes"]:
                issue["repo"] = f"{owner}/{name}"
                issue["comments"]["nodes"] = self._complete_comments(owner, name, issue)
                issue["timelineItems"]["nodes"] = self._complete_timeline(owner, name, issue)
                yield issue
                exported += 1
                if limit is not None and exported >= limit:
                    return

            page_info = issues["pageInfo"]
            if not page_info["hasNextPage"]:
                return
            after = page_info["endCursor"]

    def _complete_comments(self, owner: str, name: str, issue: dict[str, Any]) -> list[dict[str, Any]]:
        comments = list(issue["comments"]["nodes"])
        page_info = issue["comments"]["pageInfo"]
        after = page_info["endCursor"]

        while page_info["hasNextPage"]:
            data = self.graphql(
                COMMENTS_QUERY,
                {
                    "owner": owner,
                    "name": name,
                    "number": issue["number"],
                    "after": after,
                },
            )
            page = data["repository"]["issue"]["comments"]
            comments.extend(page["nodes"])
            page_info = page["pageInfo"]
            after = page_info["endCursor"]

        return comments

    def _complete_timeline(self, owner: str, name: str, issue: dict[str, Any]) -> list[dict[str, Any]]:
        events = list(issue["timelineItems"]["nodes"])
        page_info = issue["timelineItems"]["pageInfo"]
        after = page_info["endCursor"]

        while page_info["hasNextPage"]:
            data = self.graphql(
                TIMELINE_QUERY,
                {
                    "owner": owner,
                    "name": name,
                    "number": issue["number"],
                    "after": after,
                },
            )
            page = data["repository"]["issue"]["timelineItems"]
            events.extend(page["nodes"])
            page_info = page["pageInfo"]
            after = page_info["endCursor"]

        return events
