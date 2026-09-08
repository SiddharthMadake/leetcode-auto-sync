from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .models import SolutionRecord
from .paths import language_readme_relpath, problem_readme_relpath, solution_relpath


def fmt_utc(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _read_language_metadata(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("<!-- ") and ": " in line and line.endswith(" -->"):
            body = line[5:-4]
            key, value = body.split(": ", 1)
            result[key] = value
    required = {"problem_id", "title", "difficulty", "language", "language_slug", "date", "submission_id", "runtime", "memory"}
    return result if required.issubset(result) else None


def _render_problem_readme(problem_dir: Path) -> str:
    language_readmes = []
    for path in sorted(problem_dir.glob("*/README.md")):
        meta = _read_language_metadata(path)
        if meta:
            language_readmes.append((meta, path.parent / ("solution." + _extension_for_solution(path.parent))))
    if not language_readmes:
        return ""
    first = language_readmes[0][0]
    lines = [
        f"# {first['problem_id']}. {first['title']}",
        "",
        f"**Difficulty:** {first['difficulty']}  ",
        f"**LeetCode:** [{first['title']}](https://leetcode.com/problems/{first['title_slug']}/)",
        "",
        "## Solutions",
        "",
        "| Language | Accepted | Runtime | Memory | Solution | Submission |",
        "|---|---|---|---|---|---|",
    ]
    for meta, solution_path in language_readmes:
        rel_solution = solution_path.relative_to(problem_dir).as_posix()
        lines.append(
            f"| {meta['language']} | {meta['date']} | {meta['runtime']} | {meta['memory']} | [{meta['language']}]({rel_solution}) | [#{meta['submission_id']}](https://leetcode.com/submissions/detail/{meta['submission_id']}/) |"
        )
    lines.extend(["", "Source code in this directory is copied from the accepted LeetCode submission without semantic rewriting.", ""])
    return "\n".join(lines)


def _extension_for_solution(lang_dir: Path) -> str:
    matches = sorted(lang_dir.glob("solution.*"))
    return matches[0].suffix.lstrip(".") if matches else "txt"


def write_solution(repo_root: Path, record: SolutionRecord) -> list[Path]:
    solution_path = repo_root / solution_relpath(record)
    language_readme = repo_root / language_readme_relpath(record)
    problem_readme = repo_root / problem_readme_relpath(record)
    solution_path.parent.mkdir(parents=True, exist_ok=True)

    solution_path.write_text(record.code.rstrip() + "\n", encoding="utf-8")

    runtime = record.runtime or "Not available"
    memory = record.memory or "Not available"
    metadata_comments = "\n".join([
        f"<!-- problem_id: {record.problem_id} -->",
        f"<!-- title: {record.title} -->",
        f"<!-- title_slug: {record.title_slug} -->",
        f"<!-- difficulty: {record.difficulty} -->",
        f"<!-- language: {record.language} -->",
        f"<!-- language_slug: {record.language_slug} -->",
        f"<!-- date: {datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime('%Y-%m-%d')} -->",
        f"<!-- submission_id: {record.submission_id} -->",
        f"<!-- runtime: {runtime} -->",
        f"<!-- memory: {memory} -->",
    ])
    percentile_lines = []
    if record.runtime_percentile is not None:
        percentile_lines.append(f"- Runtime percentile: {record.runtime_percentile:g}%")
    if record.memory_percentile is not None:
        percentile_lines.append(f"- Memory percentile: {record.memory_percentile:g}%")
    language_readme.write_text(
        f"# {record.problem_id}. {record.title} — {record.language}\n\n"
        f"{metadata_comments}\n\n"
        f"**Difficulty:** {record.difficulty}  \n"
        f"**Accepted submission:** {fmt_utc(record.timestamp)}  \n"
        f"**LeetCode:** [{record.title_slug}]({record.leetcode_url})  \n"
        f"**Submission:** [#{record.submission_id}](https://leetcode.com/submissions/detail/{record.submission_id}/)\n\n"
        "## Performance\n\n"
        f"- Runtime: {runtime}\n"
        f"- Memory: {memory}\n"
        f"{''.join(line + chr(10) for line in percentile_lines)}\n"
        f"[Open solution](solution.{record.extension})\n",
        encoding="utf-8",
    )

    problem_readme.write_text(_render_problem_readme(problem_readme.parent), encoding="utf-8")
    return [solution_path, language_readme, problem_readme]
