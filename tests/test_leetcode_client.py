from unittest.mock import Mock

import requests

from leetcode_sync.leetcode_client import LeetCodeAPIError, LeetCodeClient


def fake_response(data, status=200):
    r = Mock()
    r.status_code = status
    r.text = "body"
    r.raise_for_status.side_effect = requests.HTTPError("bad") if status >= 400 else None
    r.json.return_value = data
    return r


def test_recent_accepted_parses_rows():
    client = LeetCodeClient("session", "csrf")
    client.session.post = Mock(return_value=fake_response({
        "data": {
            "recentAcSubmissionList": [
                {"id": "99", "title": "Two Sum", "titleSlug": "two-sum", "timestamp": "1757318400"}
            ]
        }
    }))
    result = client.recent_accepted("demo", 100)
    assert result[0].submission_id == 99
    assert result[0].title_slug == "two-sum"


def test_detail_parses_metadata():
    client = LeetCodeClient("session", "csrf")
    client.session.post = Mock(return_value=fake_response({
        "data": {
            "submissionDetails": {
                "id": "99",
                "runtime": "1 ms",
                "runtimeDisplay": "1 ms",
                "runtimePercentile": 91.2,
                "memory": "10 MB",
                "memoryDisplay": "10 MB",
                "memoryPercentile": 80.1,
                "code": "print(1)",
                "timestamp": "1757318400",
                "statusDisplay": "Accepted",
                "lang": {"name": "python3", "verboseName": "Python3"},
                "question": {
                    "questionId": "1",
                    "questionFrontendId": "1",
                    "title": "Two Sum",
                    "titleSlug": "two-sum",
                    "difficulty": "Easy",
                },
            }
        }
    }))
    result = client.submission_detail(99)
    assert result.status_display == "Accepted"
    assert result.language == "python3"
    assert result.title == "Two Sum"
    assert result.runtime_percentile == 91.2


def test_graphql_errors_raise():
    client = LeetCodeClient("session", "csrf", max_retries=1)
    client.session.post = Mock(return_value=fake_response({"errors": [{"message": "Unauthorized"}], "data": {}}))
    try:
        client.recent_accepted("demo", 1)
    except LeetCodeAPIError as exc:
        assert "Unauthorized" in str(exc)
    else:
        raise AssertionError("Expected LeetCodeAPIError")
