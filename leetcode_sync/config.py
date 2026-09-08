from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Raised when required configuration is missing or invalid."""



def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be > 0")
    return value


@dataclass(frozen=True)
class Settings:
    leetcode_username: str
    leetcode_session: str
    leetcode_csrf_token: str
    github_token: str | None
    github_repository: str | None
    default_branch: str
    sync_lookback_limit: int
    http_timeout_seconds: int
    http_max_retries: int
    repo_root: Path

    @classmethod
    def from_env(cls) -> "Settings":
        required = {
            "LEETCODE_USERNAME": os.getenv("LEETCODE_USERNAME", "").strip(),
            "LEETCODE_SESSION": os.getenv("LEETCODE_SESSION", "").strip(),
            "LEETCODE_CSRF_TOKEN": os.getenv("LEETCODE_CSRF_TOKEN", "").strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            leetcode_username=required["LEETCODE_USERNAME"],
            leetcode_session=required["LEETCODE_SESSION"],
            leetcode_csrf_token=required["LEETCODE_CSRF_TOKEN"],
            github_token=os.getenv("GITHUB_TOKEN", "").strip() or None,
            github_repository=os.getenv("GITHUB_REPOSITORY", "").strip() or None,
            default_branch=os.getenv("DEFAULT_BRANCH", "main").strip() or "main",
            sync_lookback_limit=_positive_int("SYNC_LOOKBACK_LIMIT", 100),
            http_timeout_seconds=_positive_int("HTTP_TIMEOUT_SECONDS", 30),
            http_max_retries=_positive_int("HTTP_MAX_RETRIES", 4),
            repo_root=Path(os.getenv("REPO_ROOT", ".")).resolve(),
        )
