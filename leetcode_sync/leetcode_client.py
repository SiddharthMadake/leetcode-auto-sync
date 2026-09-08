from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests

from .models import AcceptedSubmission, SubmissionDetail

LOGGER = logging.getLogger(__name__)
GRAPHQL_URL = "https://leetcode.com/graphql/"

RECENT_ACCEPTED_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

SUBMISSION_DETAILS_QUERY = """
query submissionDetails($submissionId: Int!) {
  submissionDetails(submissionId: $submissionId) {
    id
    runtime
    runtimeDisplay
    runtimePercentile
    memory
    memoryDisplay
    memoryPercentile
    code
    timestamp
    statusDisplay
    lang {
      name
      verboseName
    }
    question {
      questionId
      questionFrontendId
      title
      titleSlug
      difficulty
    }
  }
}
"""


class LeetCodeAPIError(RuntimeError):
    """Raised for transport, GraphQL, or schema errors."""


class LeetCodeClient:
    def __init__(
        self,
        session_cookie: str,
        csrf_token: str,
        *,
        timeout_seconds: int = 30,
        max_retries: int = 4,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.cookies.update(
            {
                "LEETCODE_SESSION": session_cookie,
                "csrftoken": csrf_token,
            }
        )
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://leetcode.com",
            "Referer": "https://leetcode.com/",
            "User-Agent": "leetcode-github-sync/1.0 (+https://github.com/)",
            "x-csrftoken": csrf_token,
        }

    def _graphql(self, query: str, operation_name: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query,
        }
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    GRAPHQL_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise LeetCodeAPIError(
                        f"LeetCode HTTP {response.status_code}: {response.text[:500]}"
                    )
                response.raise_for_status()
                try:
                    data = response.json()
                except json.JSONDecodeError as exc:
                    raise LeetCodeAPIError("LeetCode returned non-JSON response") from exc
                errors = data.get("errors") or []
                if errors:
                    messages = "; ".join(str(e.get("message", e)) for e in errors)
                    raise LeetCodeAPIError(f"LeetCode GraphQL error: {messages}")
                if "data" not in data:
                    raise LeetCodeAPIError("LeetCode response missing data")
                return data["data"]
            except (requests.RequestException, LeetCodeAPIError) as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    break
                delay = min(2 ** (attempt - 1), 8)
                LOGGER.warning("LeetCode request failed (attempt %s/%s): %s; retrying in %ss", attempt, self.max_retries, exc, delay)
                time.sleep(delay)
        raise LeetCodeAPIError(f"LeetCode request failed after {self.max_retries} attempts: {last_error}") from last_error

    def recent_accepted(self, username: str, limit: int = 100) -> list[AcceptedSubmission]:
        data = self._graphql(
            RECENT_ACCEPTED_QUERY,
            "recentAcSubmissions",
            {"username": username, "limit": limit},
        )
        rows = data.get("recentAcSubmissionList")
        if rows is None:
            raise LeetCodeAPIError("LeetCode schema changed: recentAcSubmissionList missing")
        result: list[AcceptedSubmission] = []
        for row in rows:
            try:
                result.append(
                    AcceptedSubmission(
                        submission_id=int(row["id"]),
                        title=str(row["title"]),
                        title_slug=str(row["titleSlug"]),
                        timestamp=int(row["timestamp"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                LOGGER.warning("Skipping malformed accepted submission row: %r", row)
                continue
        return result

    def submission_detail(self, submission_id: int) -> SubmissionDetail:
        data = self._graphql(
            SUBMISSION_DETAILS_QUERY,
            "submissionDetails",
            {"submissionId": submission_id},
        )
        row = data.get("submissionDetails")
        if not row:
            raise LeetCodeAPIError(
                f"Submission {submission_id} detail unavailable (expired, unauthorized, or schema changed)"
            )
        question = row.get("question") or {}
        lang = row.get("lang") or {}
        try:
            return SubmissionDetail(
                submission_id=int(row["id"]),
                status_display=str(row.get("statusDisplay", "")),
                language=str(lang.get("name", "")),
                language_verbose=str(lang.get("verboseName", "")),
                code=str(row.get("code") or ""),
                runtime=row.get("runtimeDisplay") or row.get("runtime"),
                memory=row.get("memoryDisplay") or row.get("memory"),
                runtime_percentile=_float_or_none(row.get("runtimePercentile")),
                memory_percentile=_float_or_none(row.get("memoryPercentile")),
                timestamp=int(row.get("timestamp") or 0),
                question_id=str(question.get("questionId", "")),
                frontend_id=str(question.get("questionFrontendId", "")),
                title=str(question.get("title", "")),
                title_slug=str(question.get("titleSlug", "")),
                difficulty=str(question.get("difficulty", "")),
            )
        except (TypeError, ValueError) as exc:
            raise LeetCodeAPIError(f"Malformed details for submission {submission_id}: {row!r}") from exc


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
