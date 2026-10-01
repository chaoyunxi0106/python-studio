"""External AI provider adapters."""

from .deepseek import ProviderError, chat_completion, chat_json, extract_json_object

__all__ = [
    "ProviderError",
    "chat_completion",
    "chat_json",
    "extract_json_object",
]
