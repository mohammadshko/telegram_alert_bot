import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram.error import BadRequest
from bot import build_subscription_keyboard, subscription_callback_handler
from storage import JSONStorage

def test_build_subscription_keyboard(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path / "data"))
    user_id = 100

    # Check default keyboard (no subscriptions)
    keyboard = build_subscription_keyboard(user_id, storage)
    button_texts = [btn[0].text for btn in keyboard.inline_keyboard]
    assert "❌ #node_alerts_app" in button_texts
    assert "❌ #disk_alert_cons1" in button_texts

    # Add subscription and re-check
    storage.add_subscriptions(user_id, ["node_alerts_app"])
    keyboard2 = build_subscription_keyboard(user_id, storage)
    button_texts2 = [btn[0].text for btn in keyboard2.inline_keyboard]
    assert "✅ #node_alerts_app" in button_texts2
    assert "❌ #disk_alert_cons1" in button_texts2

def test_build_subscription_keyboard_callback_data_length_limit(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path / "data"))
    user_id = 100
    long_tag = "a" * 100
    storage.add_subscriptions(user_id, [long_tag])

    keyboard = build_subscription_keyboard(user_id, storage)
    for row in keyboard.inline_keyboard:
        for btn in row:
            assert len(btn.callback_data.encode("utf-8")) <= 64

@pytest.mark.asyncio
async def test_subscription_callback_handler(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path / "data"))
    user_id = 100

    update = MagicMock()
    update.effective_user.id = user_id
    query = AsyncMock()
    query.data = "toggle_sub:node_alerts_app"
    update.callback_query = query

    context = MagicMock()
    context.bot_data = {"storage": storage}

    # Toggle ON
    await subscription_callback_handler(update, context)
    assert storage.get_subscriptions(user_id) == {"node_alerts_app"}
    query.answer.assert_called_with(text="Subscribed to #node_alerts_app")
    query.edit_message_reply_markup.assert_called()

    # Toggle OFF
    await subscription_callback_handler(update, context)
    assert storage.get_subscriptions(user_id) == set()
    query.answer.assert_called_with(text="Unsubscribed from #node_alerts_app")

@pytest.mark.asyncio
async def test_subscription_callback_handler_handles_bad_request_exception(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path / "data"))
    user_id = 100

    update = MagicMock()
    update.effective_user.id = user_id
    query = AsyncMock()
    query.data = "toggle_sub:node_alerts_app"
    query.edit_message_reply_markup.side_effect = BadRequest("Message is not modified")
    update.callback_query = query

    context = MagicMock()
    context.bot_data = {"storage": storage}

    # Should not raise exception
    await subscription_callback_handler(update, context)
    query.answer.assert_called_with(text="Subscribed to #node_alerts_app")
