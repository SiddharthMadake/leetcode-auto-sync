from __future__ import annotations

import logging
from collections import OrderedDict
from pathlib import Path

from .file_writer import write_solution
from .git_ops import changed_paths, commit_and_push, ensure_repo
from .languages import normalize_language
from .leetcode_client import LeetCodeAPIError, LeetCodeClient
from .models import SolutionRecord
from .paths import language_readme_relpath, problem_readme_relpath, solution_relpath
from .readme import update_root_readme

LOGGER = logging.getLogger(__name__)


def make_commit_message(record: SolutionRecord) -> str:
    return f"Solve {record.title} [{record.difficulty}]"


def build_record(detail) -> SolutionRecord | None:
    if detail.status_display.strip().lower() != "accepted":
        LOGGER.info("Skipping submission %s because status is %r", detail.submission_id, detail.status_display)
        return None
    if not detail.code.strip():
        raise LeetCodeAPIError(f"Submission {detail.submission_id} is accepted but has no source code")
    spec = normalize_language(detail.language)
    if spec is None:
        LOGGER.warning("Unsupported LeetCode language %r on submission %s; skipping", detail.language, detail.submission_id)
        return None
    problem_id = detail.frontend_id or detail.question_id
    if not problem_id.isdigit():
        raise LeetCodeAPIError(f"Submission {detail.submission_id} has no numeric problem ID")
    if not detail.title_slug:
        raise LeetCodeAPIError(f"Submission {detail.submission_id} has no problem slug")
    return SolutionRecord(
        submission_id=detail.submission_id,
        problem_id=problem_id,
        title=detail.title or detail.title_slug,
        title_slug=detail.title_slug,
        difficulty=detail.difficulty or "Unknown",
        language=spec.display_name,
        language_slug=spec.slug,
        extension=spec.extension,
        code=detail.code,
        timestamp=detail.timestamp,
        leetcode_url=f"https://leetcode.com/problems/{detail.title_slug}/",
        runtime=detail.runtime,
        memory=detail.memory,
        runtime_percentile=detail.runtime_percentile,
        memory_percentile=detail.memory_percentile,
    )


def _keep_newest_by_problem_language(records: list[SolutionRecord]) -> list[SolutionRecord]:
    newest: dict[tuple[str, str], SolutionRecord] = {}
    for record in records:
        key = (record.title_slug, record.language_slug)
        previous = newest.get(key)
        if previous is None or record.timestamp >= previous.timestamp:
            newest[key] = record
    return list(newest.values())


def sync(settings) -> dict[str, object]:
    repo_root: Path = settings.repo_root
    ensure_repo(repo_root, settings.default_branch)
    client = LeetCodeClient(
        settings.leetcode_session,
        settings.leetcode_csrf_token,
        timeout_seconds=settings.http_timeout_seconds,
        max_retries=settings.http_max_retries,
    )

    accepted = client.recent_accepted(settings.leetcode_username, settings.sync_lookback_limit)
    LOGGER.info("LeetCode returned %s recent accepted submissions", len(accepted))

    candidates: list[SolutionRecord] = []
    for submission in accepted:
        try:
            detail = client.submission_detail(submission.submission_id)
            record = build_record(detail)
            if record is None:
                continue
            target = repo_root / solution_relpath(record)
            if target.exists():
                LOGGER.debug("Already archived: %s", target.relative_to(repo_root).as_posix())
                continue
            candidates.append(record)
        except LeetCodeAPIError as exc:
            # A single expired/detail failure must not prevent unrelated new solves from syncing.
            LOGGER.error(
                "Failed to process submission %s (%s): %s",
                submission.submission_id,
                submission.title,
                exc,
            )

    candidates = _keep_newest_by_problem_language(candidates)
    candidates.sort(key=lambda r: (r.timestamp, int(r.problem_id), r.language))
    if not candidates:
        LOGGER.info("No new accepted solutions found")
        return {"new_records": [], "commit": "", "commits": []}

    commits: list[str] = []
    committed_records: list[SolutionRecord] = []
    for record in candidates:
        generated = write_solution(repo_root, record)
        root_readme = update_root_readme(repo_root, settings.leetcode_username)
        generated.append(root_readme)
        paths = sorted(changed_paths(repo_root, generated))
        if not paths:
            LOGGER.info("%s was already present after generation; skipping commit", record.title)
            continue
        commit_message = make_commit_message(record)
        sha = commit_and_push(repo_root, settings.default_branch, paths, commit_message)
        commits.append(sha)
        committed_records.append(record)
        LOGGER.info("Pushed commit %s for %s [%s]", sha, record.title, record.language)

    return {
        "new_records": committed_records,
        "commit": commits[-1] if commits else "",
        "commits": commits,
    }
