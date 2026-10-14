# Telegram Alert Bot

A Telegram bot that monitors an alert channel for messages containing specific hashtags (e.g., `#node_alerts_app`, `#disk_alert_cons1`) and forwards matching alerts to subscribed users.

## Features

- **Hashtag Filtering**: Automatically parses incoming channel posts for hashtags.
- **Interactive Button Subscriptions**: Users can easily toggle subscription preferences using interactive inline message buttons (e.g. `✅ #node_alerts_app` / `❌ #disk_alert_cons1`).
- **User Subscription Preferences**: Support for custom subscriptions via commands or interactive buttons.
- **Persistent Storage**: Maintains user subscriptions and system processing state across restarts using JSON storage.
- **Configurable Polling/Interval**: Configurable update interval and target channel ID.

## Requirements

- Python 3.10+
- `python-telegram-bot` >= 20.0

## Setup & Configuration

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Set the following environment variables (or configure them in `config.py`):

   - `BOT_TOKEN`: Telegram bot token from [@BotFather](https://t.me/BotFather).
   - `CHANNEL_ID`: Channel ID or username (e.g., `@my_alerts_channel` or `-100123456789`).
   - `CHECK_INTERVAL`: (Optional) Check/poll interval in seconds (default: `60`).
   - `DATA_DIR`: (Optional) Path to storage directory (default: `data`).

3. **Telegram Channel Setup**:
   - Add your bot as an Administrator (or member with post read access) in your Telegram channel so it receives channel posts.

## Usage

Run the bot with:

```bash
python main.py
```

### Bot Commands & Interactive Buttons

Users can interact with the bot in private messages:

- `/start` - Start the bot and manage subscriptions via interactive inline buttons.
- `/subscriptions` - Display interactive inline buttons to view and toggle alert topic subscriptions on/off.
- `/subscribe <tag1> <tag2>` - Subscribe to specific alert hashtags (or view button menu if no tags provided).
- `/unsubscribe <tag1> <tag2>` - Unsubscribe from specific alert hashtags.
- `/help` - View usage and command guide.

## Testing

Run unit tests using `pytest`:

```bash
python -m pytest
```
