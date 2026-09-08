from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command fails."""


def run_git(repo_root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed ({proc.returncode}):\n{proc.stdout.strip()}")
    return proc.stdout.strip()


def ensure_repo(repo_root: Path, branch: str) -> None:
    if not (repo_root / ".git").exists():
        raise GitError(f"{repo_root} is not a git repository")
    current = run_git(repo_root, "branch", "--show-current")
    if current != branch:
        raise GitError(f"Expected branch '{branch}', found '{current or '(detached)'}'")


def configured_origin(repo_root: Path) -> str:
    return run_git(repo_root, "remote", "get-url", "origin")


def changed_paths(repo_root: Path, candidates: list[Path]) -> list[str]:
    rels = [p.relative_to(repo_root).as_posix() for p in candidates]
    changed: list[str] = []
    for rel in rels:
        status = run_git(repo_root, "status", "--porcelain", "--", rel, check=False)
        if status:
            changed.append(rel)
    return changed


def commit_and_push(repo_root: Path, branch: str, paths: list[str], message: str) -> str:
    if not paths:
        return ""
    run_git(repo_root, "add", "--", *paths)
    staged = run_git(repo_root, "diff", "--cached", "--name-only")
    staged_paths = [line for line in staged.splitlines() if line]
    wanted = sorted(paths)
    if sorted(staged_paths) != wanted:
        raise GitError(
            "Refusing to commit unexpected files. "
            f"Expected {wanted}, staged {sorted(staged_paths)}"
        )
    run_git(repo_root, "config", "user.name", "leetcode-sync[bot]")
    run_git(repo_root, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run_git(repo_root, "commit", "-m", message)
    sha = run_git(repo_root, "rev-parse", "HEAD")
    run_git(repo_root, "push", "origin", branch)
    return sha
