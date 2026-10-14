import json
import os
import threading
from typing import Dict, Set, Optional

class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.state_file = os.path.join(self.data_dir, "state.json")
        self.lock = threading.Lock()

        self._ensure_dir()
        self.subscriptions: Dict[int, Set[str]] = self._load_users()
        self.last_processed_message_id: int = self._load_state().get("last_processed_message_id", 0)

    def _ensure_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _load_users(self) -> Dict[int, Set[str]]:
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(user_id): set(tags) for user_id, tags in data.items()}
        except Exception:
            return {}

    def _save_users(self):
        data = {str(user_id): sorted(list(tags)) for user_id, tags in self.subscriptions.items()}
        temp_file = f"{self.users_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, self.users_file)

    def _load_state(self) -> dict:
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self):
        data = {"last_processed_message_id": self.last_processed_message_id}
        temp_file = f"{self.state_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, self.state_file)

    def add_subscriptions(self, user_id: int, tags: list[str]) -> Set[str]:
        with self.lock:
            user_tags = self.subscriptions.setdefault(user_id, set())
            for tag in tags:
                normalized = tag.strip().lstrip("#").lower()
                if normalized:
                    user_tags.add(normalized)
            self._save_users()
            return set(user_tags)

    def remove_subscriptions(self, user_id: int, tags: list[str]) -> Set[str]:
        with self.lock:
            if user_id in self.subscriptions:
                for tag in tags:
                    normalized = tag.strip().lstrip("#").lower()
                    self.subscriptions[user_id].discard(normalized)
                self._save_users()
            return self.subscriptions.get(user_id, set())

    def get_subscriptions(self, user_id: int) -> Set[str]:
        with self.lock:
            return set(self.subscriptions.get(user_id, set()))

    def get_all_subscriptions(self) -> Dict[int, Set[str]]:
        with self.lock:
            return {user_id: set(tags) for user_id, tags in self.subscriptions.items()}

    def get_last_processed_message_id(self) -> int:
        with self.lock:
            return self.last_processed_message_id

    def set_last_processed_message_id(self, message_id: int):
        with self.lock:
            self.last_processed_message_id = message_id
            self._save_state()
