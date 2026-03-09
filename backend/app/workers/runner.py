import logging
import time

from app.core.config import get_settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.workflow_engine import WorkflowEngine

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
engine = WorkflowEngine()


def main() -> None:
    logger.info("Worker booted in %s mode", settings.app_env)
    init_db()

    while True:
        try:
            with SessionLocal() as db:
                processed = engine.process_pending_steps(db, limit=settings.worker_batch_size)
            if processed == 0:
                time.sleep(settings.worker_poll_interval_seconds)
            else:
                logger.info("Processed %s pending step(s)", processed)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Worker loop failure: %s", exc)
            time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
