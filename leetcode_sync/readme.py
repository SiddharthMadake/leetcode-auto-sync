from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoSolution:
    problem_id: int
    title: str
    difficulty: str
    language: str
    date: str
    solution_path: str


def _parse_language_readme(path: Path, repo_root: Path) -> RepoSolution | None:
    text = path.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("<!-- ") and ": " in line and line.endswith(" -->"):
            key, value = line[5:-4].split(": ", 1)
            meta[key] = value
    try:
        return RepoSolution(
            problem_id=int(meta["problem_id"]),
            title=meta["title"],
            difficulty=meta["difficulty"],
            language=meta["language"],
            date=meta["date"],
            solution_path=path.parent.joinpath("solution." + _extension(path.parent)).relative_to(repo_root).as_posix(),
        )
    except (KeyError, ValueError):
        return None


def _extension(lang_dir: Path) -> str:
    matches = sorted(lang_dir.glob("solution.*"))
    return matches[0].suffix.lstrip(".") if matches else "txt"


def collect_solutions(repo_root: Path) -> list[RepoSolution]:
    rows: list[RepoSolution] = []
    for difficulty in ("easy", "medium", "hard", "unknown"):
        for path in repo_root.glob(f"{difficulty}/*/*/README.md"):
            row = _parse_language_readme(path, repo_root)
            if row:
                rows.append(row)
    return sorted(rows, key=lambda r: (r.problem_id, r.language))


def render_root_readme(rows: list[RepoSolution], username: str) -> str:
    counts = {"Easy": 0, "Medium": 0, "Hard": 0, "Unknown": 0}
    for row in rows:
        counts[row.difficulty] = counts.get(row.difficulty, 0) + 1
    total = len(rows)
    lines = [
        "# LeetCode Solutions",
        "",
        f"Automated archive of accepted LeetCode submissions for **{username}**.",
        "",
        "## LeetCode Progress",
        "",
        f"- Easy: **{counts.get('Easy', 0)}**",
        f"- Medium: **{counts.get('Medium', 0)}**",
        f"- Hard: **{counts.get('Hard', 0)}**",
        f"- Total: **{total}**",
        "",
        "## Solutions",
        "",
        "| # | Problem | Difficulty | Language | Date | Solution |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.problem_id} | {row.title} | {row.difficulty} | {row.language} | {row.date} | [{row.language}]({row.solution_path}) |"
        )
    lines.extend([
        "",
        "## Automation",
        "",
        "This repository is synchronized daily by GitHub Actions. The workflow detects recent accepted submissions, retrieves the submitted source and metadata, adds missing language-specific solutions, updates this README, and creates focused Git commits.",
        "",
        "See [SETUP.md](SETUP.md) for setup, authentication, testing, and maintenance notes.",
        "",
    ])
    return "\n".join(lines)


def update_root_readme(repo_root: Path, username: str) -> Path:
    path = repo_root / "README.md"
    path.write_text(render_root_readme(collect_solutions(repo_root), username), encoding="utf-8")
    return path
