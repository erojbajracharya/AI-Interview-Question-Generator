# api_rotator.py
"""
API Key Rotation Manager
Handles automatic rotation of API keys when one fails.
"""

from api_config import API_KEYS


class APIRotator:
    """Manages API key rotation across multiple keys."""

    def __init__(self):
        self.current_index = 0
        self.failed_keys = set()

    @property
    def is_offline(self):
        """Returns True if no API keys are configured."""
        return len(API_KEYS) == 0

    def get_current_key(self):
        """Get the current API key."""
        if self.is_offline:
            return None
        return API_KEYS[self.current_index]

    def rotate(self):
        """Move to the next available API key."""
        if self.is_offline:
            return None
        self.current_index = (self.current_index + 1) % len(API_KEYS)
        return API_KEYS[self.current_index]
    
    def mark_failed(self, key):
        """Mark a key as failed."""
        self.failed_keys.add(key)
    
    def get_available_keys(self):
        """Get list of all available API keys."""
        return API_KEYS
    
    def reset(self):
        """Reset the rotator to the first key."""
        self.current_index = 0
        self.failed_keys = set()


# Global instance
_rotator = APIRotator()


def get_rotator():
    """Get the global API rotator instance."""
    return _rotator


def get_all_keys():
    """Get all available API keys."""
    return _rotator.get_available_keys()
