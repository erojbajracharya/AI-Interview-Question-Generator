# api_config.py
"""
API configuration for Gemini key rotation.

Set the environment variable AI_GEN_API_KEYS with a comma-separated list of
Gemini API keys, for example:

  AI_GEN_API_KEYS="key1,key2,key3"
"""

import os

API_KEYS = [
    key.strip()
    for key in os.environ.get("AI_GEN_API_KEYS", "").split(",")
    if key.strip()
]