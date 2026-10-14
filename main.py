import logging
import sys
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from storage import JSONStorage
from bot import (
    start_handler,
    help_handler,
    subscribe_handler,
    unsubscribe_handler,
    subscriptions_handler,
    channel_post_handler,
    check_channel_alerts_job,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in environment or config. Exiting.")
        sys.exit(1)

    storage = JSONStorage(data_dir=config.DATA_DIR)

    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # Store shared objects in bot_data
    application.bot_data["storage"] = storage

    # Register command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("subscribe", subscribe_handler))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_handler))
    application.add_handler(CommandHandler("subscriptions", subscriptions_handler))

    # Register channel post handler (for channel updates)
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))

    # Register periodic job queue task
    if application.job_queue:
        application.job_queue.run_repeating(
            check_channel_alerts_job,
            interval=config.CHECK_INTERVAL,
            first=10,
        )

    logger.info("Starting Telegram alert bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
