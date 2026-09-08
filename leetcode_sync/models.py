from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptedSubmission:
    submission_id: int
    title: str
    title_slug: str
    timestamp: int


@dataclass(frozen=True)
class SubmissionDetail:
    submission_id: int
    status_display: str
    language: str
    language_verbose: str
    code: str
    runtime: str | None
    memory: str | None
    runtime_percentile: float | None
    memory_percentile: float | None
    timestamp: int
    question_id: str
    frontend_id: str
    title: str
    title_slug: str
    difficulty: str


@dataclass(frozen=True)
class SolutionRecord:
    submission_id: int
    problem_id: str
    title: str
    title_slug: str
    difficulty: str
    language: str
    language_slug: str
    extension: str
    code: str
    timestamp: int
    leetcode_url: str
    runtime: str | None
    memory: str | None
    runtime_percentile: float | None
    memory_percentile: float | None
