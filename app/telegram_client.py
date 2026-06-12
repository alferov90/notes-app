import logging

import httpx

from app.config import settings

logger = logging.getLogger("noteflow")


def is_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_bot_username)


def api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


def send_message(chat_id: int, text: str) -> bool:
    if not settings.telegram_bot_token:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(
                api_url("sendMessage"),
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
            response.raise_for_status()
            return True
    except httpx.HTTPError:
        logger.exception("Failed to send Telegram message to %s", chat_id)
        return False


def get_updates(offset: int | None = None) -> list[dict]:
    if not settings.telegram_bot_token:
        return []
    params: dict = {"timeout": 0, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(api_url("getUpdates"), params=params)
            response.raise_for_status()
            return response.json().get("result", [])
    except httpx.HTTPError:
        logger.exception("Failed to poll Telegram updates")
        return []
