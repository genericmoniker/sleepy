import logging
import time

import schedule

import fitbit_data
import log
from config import Config
from database import Database

logger = logging.getLogger(__name__)


def main() -> None:
    log.setup()
    logger.info("===== startup =====")
    config = Config()

    # Update data immediately and schedule daily updates.
    update_data(config)
    schedule.every().day.at(config.update_data_time).do(update_data, config)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("===== shutdown =====")
            break


def update_data(config: Config) -> None:
    with Database(config) as db:
        fitbit_data.update(config, db)
    # TODO: Update from other sources.
    logger.info("Data update complete.")


if __name__ == "__main__":
    main()
