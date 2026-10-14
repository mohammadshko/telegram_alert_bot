import logging
from telegram import Update
from telegram.ext import ContextTypes
from storage import JSONStorage
from alert_processor import extract_hashtags, get_matching_users
import config

logger = logging.getLogger(__name__)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    welcome_text = (
        "Welcome to the Alert Notification Bot!\n\n"
        "I monitor the channel for alert messages containing hashtags and send you alerts you've subscribed to.\n\n"
        "Available commands:\n"
        "/subscribe <tag1> <tag2> - Subscribe to alert hashtags (e.g. /subscribe node_alerts_app disk_alert_cons1)\n"
        "/unsubscribe <tag1> <tag2> - Unsubscribe from alert hashtags\n"
        "/subscriptions - View your active subscriptions\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(welcome_text)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Command Reference:\n\n"
        "/subscribe <tag1> <tag2> ... - Subscribe to alert tags (with or without #)\n"
        "  Example: /subscribe node_alerts_app disk_alert_cons1\n\n"
        "/unsubscribe <tag1> <tag2> ... - Remove tag subscriptions\n"
        "  Example: /unsubscribe node_alerts_app\n\n"
        "/subscriptions - View your current subscribed tags\n\n"
        "/help - Show help instructions"
    )
    await update.message.reply_text(help_text)

async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    tags = context.args

    if not tags:
        await update.message.reply_text(
            "Please specify at least one tag to subscribe to.\n"
            "Example: /subscribe node_alerts_app disk_alert_cons1"
        )
        return

    updated_subs = storage.add_subscriptions(user_id, tags)
    formatted_tags = ", ".join([f"#{t}" for t in sorted(updated_subs)])
    await update.message.reply_text(
        f"Subscription updated successfully!\nYour active subscriptions: {formatted_tags}"
    )

async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    tags = context.args

    if not tags:
        await update.message.reply_text(
            "Please specify at least one tag to unsubscribe from.\n"
            "Example: /unsubscribe node_alerts_app"
        )
        return

    updated_subs = storage.remove_subscriptions(user_id, tags)
    if updated_subs:
        formatted_tags = ", ".join([f"#{t}" for t in sorted(updated_subs)])
        await update.message.reply_text(
            f"Unsubscribed specified tags.\nYour remaining subscriptions: {formatted_tags}"
        )
    else:
        await update.message.reply_text("Unsubscribed specified tags.\nYou currently have no active subscriptions.")

async def subscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    subs = storage.get_subscriptions(user_id)

    if not subs:
        await update.message.reply_text("You have no active subscriptions. Use /subscribe <tag> to subscribe.")
    else:
        formatted_tags = ", ".join([f"#{t}" for t in sorted(subs)])
        await update.message.reply_text(f"Your active subscriptions:\n{formatted_tags}")

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for channel posts received in real-time if the bot is added as an admin/member in the channel.
    Automatically updates state and routes alerts to subscribed users.
    """
    channel_post = update.channel_post
    if not channel_post or not (channel_post.text or channel_post.caption):
        return

    channel_id_str = str(config.CHANNEL_ID)
    if channel_id_str and str(channel_post.chat_id) != channel_id_str and str(channel_post.chat.username) != channel_id_str.lstrip("@"):
        return

    storage: JSONStorage = context.bot_data["storage"]

    # Record message id if newer
    if channel_post.message_id > storage.get_last_processed_message_id():
        storage.set_last_processed_message_id(channel_post.message_id)

    text = channel_post.text or channel_post.caption or ""
    tags = extract_hashtags(text)
    if not tags:
        return

    matching_users = get_matching_users(storage, tags)
    for user_id in matching_users:
        try:
            await context.bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send alert to user {user_id}: {e}")

async def check_channel_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Periodic job running every CHECK_INTERVAL seconds.
    Note: Standard Telegram Bot API doesn't allow fetching message history directly without receiving updates
    or channel posts unless messages are handled via channel updates or user account API.
    This job handles pending stored/buffered messages or channel polling checks if configured.
    """
    pass
