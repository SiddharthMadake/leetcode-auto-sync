from __future__ import annotations

import re

from .models import SolutionRecord

DIFFICULTIES = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}


def slugify_title(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "problem"


def normalized_problem_dir(record: SolutionRecord) -> str:
    difficulty = DIFFICULTIES.get(record.difficulty, record.difficulty.lower() or "unknown")
    return f"{difficulty}/{int(record.problem_id):04d}-{slugify_title(record.title_slug.replace('-', ' '))}"


def language_dir(record: SolutionRecord) -> str:
    return record.language_slug


def solution_relpath(record: SolutionRecord) -> str:
    return f"{normalized_problem_dir(record)}/{language_dir(record)}/solution.{record.extension}"


def language_readme_relpath(record: SolutionRecord) -> str:
    return f"{normalized_problem_dir(record)}/{language_dir(record)}/README.md"


def problem_readme_relpath(record: SolutionRecord) -> str:
    return f"{normalized_problem_dir(record)}/README.md"
