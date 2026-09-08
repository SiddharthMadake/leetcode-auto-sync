from leetcode_sync.models import SolutionRecord
from leetcode_sync.paths import problem_readme_relpath, solution_relpath


def record(language="Python", language_slug="python", extension="py"):
    return SolutionRecord(
        submission_id=123,
        problem_id="1",
        title="Two Sum",
        title_slug="two-sum",
        difficulty="Easy",
        language=language,
        language_slug=language_slug,
        extension=extension,
        code="class Solution: pass",
        timestamp=1757318400,
        leetcode_url="https://leetcode.com/problems/two-sum/",
        runtime="1 ms",
        memory="15 MB",
        runtime_percentile=90.0,
        memory_percentile=80.0,
    )


def test_problem_first_layout():
    assert solution_relpath(record()) == "easy/0001-two-sum/python/solution.py"
    assert problem_readme_relpath(record()) == "easy/0001-two-sum/README.md"


def test_second_language_keeps_same_problem_folder():
    assert solution_relpath(record("C++", "cpp", "cpp")) == "easy/0001-two-sum/cpp/solution.cpp"
