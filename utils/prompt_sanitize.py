import re

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def flatten_prompt_text(text: str) -> str:
    """Remove control characters and collapse whitespace to a single line."""
    if not text:
        return text
    cleaned = _CONTROL_CHARS.sub(" ", text)
    return _WHITESPACE.sub(" ", cleaned).strip()


def sanitize_chat_messages(messages: list[dict]) -> list[dict]:
    """Sanitize string message content before sending to chat providers."""
    sanitized: list[dict] = []
    for message in messages:
        item = dict(message)
        content = item.get("content")
        if isinstance(content, str):
            item["content"] = flatten_prompt_text(content)
        sanitized.append(item)
    return sanitized
