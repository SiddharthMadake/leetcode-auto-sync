from leetcode_sync.file_writer import write_solution
from leetcode_sync.models import SolutionRecord


def make_record(language="Python", language_slug="python", extension="py", submission_id=7):
    return SolutionRecord(
        submission_id=submission_id,
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
        runtime_percentile=99.0,
        memory_percentile=88.0,
    )


def test_solution_and_metadata_are_created(tmp_path):
    paths = write_solution(tmp_path, make_record())
    assert len(paths) == 3
    assert (tmp_path / "easy/0001-two-sum/python/solution.py").exists()
    readme = (tmp_path / "easy/0001-two-sum/python/README.md").read_text()
    assert "Two Sum" in readme
    assert "1 ms" in readme


def test_second_language_is_aggregated(tmp_path):
    write_solution(tmp_path, make_record())
    write_solution(tmp_path, make_record("C++", "cpp", "cpp", 8))
    problem_readme = (tmp_path / "easy/0001-two-sum/README.md").read_text()
    assert "Python" in problem_readme
    assert "C++" in problem_readme
    assert "python/solution.py" in problem_readme
    assert "cpp/solution.cpp" in problem_readme
