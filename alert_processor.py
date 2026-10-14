import re
from typing import Set, List, Dict
from storage import JSONStorage

HASHTAG_PATTERN = re.compile(r'#(\w+)', re.UNICODE)

def extract_hashtags(text: str) -> Set[str]:
    """
    Extract all hashtags from message text or caption and normalize them to lowercase.
    Returns a set of hashtag strings (without the '#' symbol).
    """
    if not text:
        return set()
    matches = HASHTAG_PATTERN.findall(text)
    return {tag.lower() for tag in matches}

def get_matching_users(storage: JSONStorage, message_tags: Set[str]) -> List[int]:
    """
    Given a set of message hashtags (normalized, without '#'), return list of user_ids
    that have subscribed to at least one of these hashtags.
    """
    if not message_tags:
        return []

    all_subscriptions = storage.get_all_subscriptions()
    matching_users = []

    for user_id, user_tags in all_subscriptions.items():
        if user_tags & message_tags:
            matching_users.append(user_id)

    return matching_users
