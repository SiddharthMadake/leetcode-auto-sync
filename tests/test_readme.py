from pathlib import Path

from leetcode_sync.readme import RepoSolution, render_root_readme


def test_root_readme_statistics_and_table():
    rows = [
        RepoSolution(1, "Two Sum", "Easy", "Python", "2026-09-08", "easy/0001-two-sum/Python/solution.py"),
        RepoSolution(3, "Longest Substring", "Medium", "Python", "2026-09-08", "medium/0003-longest-substring/Python/solution.py"),
        RepoSolution(42, "Hard Thing", "Hard", "C++", "2026-09-08", "hard/0042-hard-thing/C++/solution.cpp"),
    ]
    text = render_root_readme(rows, "demo")
    assert "Easy: **1**" in text
    assert "Medium: **1**" in text
    assert "Hard: **1**" in text
    assert "Total: **3**" in text
    assert "| 1 | Two Sum | Easy | Python | 2026-09-08" in text
