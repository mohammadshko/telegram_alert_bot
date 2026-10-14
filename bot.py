import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from storage import JSONStorage
from alert_processor import extract_hashtags, get_matching_users
import config

logger = logging.getLogger(__name__)

# Default list of common/available alert tags that users can toggle via inline buttons
AVAILABLE_TAGS = [
    "node_alerts_app",
    "node_alerts_fetcher",
    "disk_alert_cons1",
    "disk_alert_cons2",
]

def build_subscription_keyboard(user_id: int, storage: JSONStorage) -> InlineKeyboardMarkup:
    """
    Builds an InlineKeyboardMarkup displaying all available subscription tags.
    Each button shows whether the user is currently subscribed (✅) or not (❌).
    Also includes any custom tags the user has manually subscribed to.
    """
    user_subs = storage.get_subscriptions(user_id)

    # Combine standard available tags and any custom tags user subscribed to
    all_tags = sorted(list(set(AVAILABLE_TAGS) | user_subs))

    keyboard = []
    for tag in all_tags:
        is_subscribed = tag in user_subs
        status_symbol = "✅" if is_subscribed else "❌"
        button_text = f"{status_symbol} #{tag}"
        # Telegram callback_data limit is 64 bytes
        callback_data = f"toggle_sub:{tag}"[:64]
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    return InlineKeyboardMarkup(keyboard)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    welcome_text = (
        "Welcome to the Alert Notification Bot!\n\n"
        "I monitor the channel for alert messages containing hashtags and send you alerts you've subscribed to.\n\n"
        "Click the buttons below to toggle your alert subscriptions, or use commands:\n"
        "/subscribe <tag> - Subscribe to custom tags\n"
        "/unsubscribe <tag> - Unsubscribe from tags\n"
        "/subscriptions - View & manage subscriptions with buttons\n"
        "/help - Show help message"
    )
    reply_markup = build_subscription_keyboard(user_id, storage)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Command & Button Reference:\n\n"
        "• Click buttons under /subscriptions or /start to toggle subscriptions on/off.\n"
        "• /subscribe <tag1> <tag2> - Subscribe to alert tags (with or without #)\n"
        "  Example: /subscribe node_alerts_app disk_alert_cons1\n"
        "• /unsubscribe <tag1> <tag2> - Remove tag subscriptions\n"
        "  Example: /unsubscribe node_alerts_app\n"
        "• /subscriptions - Manage your active subscriptions using interactive buttons"
    )
    await update.message.reply_text(help_text)

async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    tags = context.args

    if not tags:
        reply_markup = build_subscription_keyboard(user_id, storage)
        await update.message.reply_text(
            "Select the alert topics you want to subscribe to:",
            reply_markup=reply_markup,
        )
        return

    updated_subs = storage.add_subscriptions(user_id, tags)
    reply_markup = build_subscription_keyboard(user_id, storage)
    await update.message.reply_text(
        "Subscription updated successfully!",
        reply_markup=reply_markup,
    )

async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    tags = context.args

    if not tags:
        reply_markup = build_subscription_keyboard(user_id, storage)
        await update.message.reply_text(
            "Select the alert topics to toggle/unsubscribe:",
            reply_markup=reply_markup,
        )
        return

    updated_subs = storage.remove_subscriptions(user_id, tags)
    reply_markup = build_subscription_keyboard(user_id, storage)
    await update.message.reply_text(
        "Unsubscribed specified tags.",
        reply_markup=reply_markup,
    )

async def subscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    storage: JSONStorage = context.bot_data["storage"]
    reply_markup = build_subscription_keyboard(user_id, storage)
    await update.message.reply_text(
        "Your Subscriptions (click to toggle):",
        reply_markup=reply_markup,
    )

async def subscription_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    # Extract user ID reliably from effective_user or query.from_user
    user = update.effective_user or query.from_user
    user_id = user.id if user else None
    if not user_id:
        try:
            await query.answer(text="User not identified.")
        except Exception:
            pass
        return

    storage: JSONStorage = context.bot_data["storage"]
    data = query.data or ""

    try:
        if data.startswith("toggle_sub:"):
            tag = data.split("toggle_sub:", 1)[1]
            user_subs = storage.get_subscriptions(user_id)

            if tag in user_subs:
                storage.remove_subscriptions(user_id, [tag])
                toast_text = f"Unsubscribed from #{tag}"
            else:
                storage.add_subscriptions(user_id, [tag])
                toast_text = f"Subscribed to #{tag}"

            # Always answer callback query to remove loading spinner in Telegram client
            try:
                await query.answer(text=toast_text)
            except Exception as e:
                logger.warning(f"Failed to send query answer: {e}")

            reply_markup = build_subscription_keyboard(user_id, storage)
            try:
                await query.edit_message_reply_markup(reply_markup=reply_markup)
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error updating inline keyboard markup: {e}")
        else:
            try:
                await query.answer()
            except Exception:
                pass
    except Exception as exc:
        logger.exception(f"Unhandled error in subscription_callback_handler: {exc}")
        try:
            await query.answer(text="Error processing button click. Please try again.")
        except Exception:
            pass

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
    """
    pass
