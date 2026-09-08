from leetcode_sync.models import SolutionRecord, SubmissionDetail
from leetcode_sync.sync import _keep_newest_by_problem_language, build_record, make_commit_message


def detail(status="Accepted", language="python3"):
    return SubmissionDetail(
        submission_id=2,
        status_display=status,
        language=language,
        language_verbose=language,
        code="class Solution: pass",
        runtime="1 ms",
        memory="10 MB",
        runtime_percentile=95.0,
        memory_percentile=90.0,
        timestamp=2,
        question_id="1",
        frontend_id="1",
        title="Two Sum",
        title_slug="two-sum",
        difficulty="Easy",
    )


def test_only_accepted_is_archived():
    assert build_record(detail("Wrong Answer")) is None


def test_accepted_record_is_built():
    result = build_record(detail())
    assert result is not None
    assert result.extension == "py"
    assert result.language_slug == "python"
    assert result.problem_id == "1"


def test_commit_message_generation():
    record = build_record(detail())
    assert record is not None
    assert make_commit_message(record) == "Solve Two Sum [Easy]"


def test_duplicate_problem_language_keeps_newest():
    older = build_record(detail())
    newer_detail = detail()
    newer_detail = SubmissionDetail(**{**newer_detail.__dict__, "submission_id": 3, "timestamp": 4})
    newer = build_record(newer_detail)
    assert older is not None and newer is not None
    rows = _keep_newest_by_problem_language([older, newer])
    assert len(rows) == 1
    assert rows[0].submission_id == 3
