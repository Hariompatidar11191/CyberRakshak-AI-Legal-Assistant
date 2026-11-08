
import re

GREETINGS = {
    "hi", "hello", "hey",
    "namaste", "नमस्ते",
    "good morning", "good evening",
    "good afternoon"
}


def is_greeting(message: str) -> bool:
    cleaned = re.sub(r"[^\w\s]", "", message.lower()).strip()
    return cleaned in GREETINGS


def needs_retrieval(message: str) -> bool:
    """
    Skip legal document retrieval for simple greetings.
    All substantive questions still use Qdrant.
    """
    return not is_greeting(message)
