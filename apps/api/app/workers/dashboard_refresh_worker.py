from __future__ import annotations

import logging
import time

from app.services.dashboard_refresh_service import refresh_due_dashboards


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


POLL_INTERVAL_SECONDS = 60


def run_worker() -> None:
    """Run worker and return the resulting response."""
    logger.info("Dashboard refresh worker started.")

    while True:
        try:
            result = refresh_due_dashboards()
            logger.info("Dashboard refresh completed: %s", result)
        except Exception as exc:
            logger.exception("Dashboard refresh worker failed: %s", exc)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()