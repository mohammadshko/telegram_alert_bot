import pytest
from alert_processor import extract_hashtags, get_matching_users
from storage import JSONStorage

def test_extract_hashtags():
    text = "ALERT: #node_alerts_app High CPU usage detected on #app_server1! Check #disk_alert_cons1."
    tags = extract_hashtags(text)
    assert tags == {"node_alerts_app", "app_server1", "disk_alert_cons1"}

def test_extract_hashtags_empty():
    assert extract_hashtags("") == set()
    assert extract_hashtags("No hashtags here") == set()

def test_get_matching_users(tmp_path):
    storage = JSONStorage(data_dir=str(tmp_path / "data"))
    storage.add_subscriptions(1, ["node_alerts_app", "disk_alert_cons1"])
    storage.add_subscriptions(2, ["disk_alert_cons2"])
    storage.add_subscriptions(3, ["node_alerts_app"])

    message_tags = {"node_alerts_app"}
    matching = get_matching_users(storage, message_tags)
    assert set(matching) == {1, 3}

    message_tags_2 = {"disk_alert_cons2", "disk_alert_cons1"}
    matching_2 = get_matching_users(storage, message_tags_2)
    assert set(matching_2) == {1, 2}

    message_tags_3 = {"unrelated_tag"}
    matching_3 = get_matching_users(storage, message_tags_3)
    assert matching_3 == []
