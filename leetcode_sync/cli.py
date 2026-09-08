from __future__ import annotations

import logging
import sys

from dotenv import load_dotenv

from .config import ConfigurationError, Settings
from .sync import sync


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


def main() -> int:
    load_dotenv()
    configure_logging()
    try:
        settings = Settings.from_env()
        result = sync(settings)
        records = result.get("new_records", [])
        print(f"Sync complete: {len(records)} new accepted solution(s).")
        if result.get("commit"):
            print(f"Commit: {result['commit']}")
        return 0
    except (ConfigurationError, Exception) as exc:
        logging.getLogger(__name__).exception("Sync failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
