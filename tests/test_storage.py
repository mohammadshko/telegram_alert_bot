import os
import shutil
import pytest
from storage import JSONStorage

@pytest.fixture
def temp_storage(tmp_path):
    data_dir = str(tmp_path / "data")
    storage = JSONStorage(data_dir=data_dir)
    return storage

def test_add_and_get_subscriptions(temp_storage):
    user_id = 12345
    tags = ["#node_alerts_app", "disk_alert_cons1"]

    subs = temp_storage.add_subscriptions(user_id, tags)
    assert subs == {"node_alerts_app", "disk_alert_cons1"}

    get_subs = temp_storage.get_subscriptions(user_id)
    assert get_subs == {"node_alerts_app", "disk_alert_cons1"}

def test_remove_subscriptions(temp_storage):
    user_id = 12345
    temp_storage.add_subscriptions(user_id, ["node_alerts_app", "disk_alert_cons1", "disk_alert_cons2"])

    remaining = temp_storage.remove_subscriptions(user_id, ["disk_alert_cons1"])
    assert remaining == {"node_alerts_app", "disk_alert_cons2"}

    assert temp_storage.get_subscriptions(user_id) == {"node_alerts_app", "disk_alert_cons2"}

def test_persistence(tmp_path):
    data_dir = str(tmp_path / "data")

    storage1 = JSONStorage(data_dir=data_dir)
    storage1.add_subscriptions(100, ["tag1", "tag2"])
    storage1.set_last_processed_message_id(999)

    storage2 = JSONStorage(data_dir=data_dir)
    assert storage2.get_subscriptions(100) == {"tag1", "tag2"}
    assert storage2.get_last_processed_message_id() == 999
