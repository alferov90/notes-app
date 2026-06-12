import logging

import httpx

from app.config import settings

logger = logging.getLogger("noteflow")


def is_configured() -> bool:
    return bool(settings.telegram_bot_token and settings.telegram_bot_username)


def api_url(method: str) -> str:
    return f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"


def _api_post(method: str, json: dict | None = None) -> dict | None:
    if not settings.telegram_bot_token:
        return None
    try:
        with httpx.Client(timeout=15) as client:
            response = client.post(api_url(method), json=json or {})
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram %s failed: %s", method, data.get("description"))
            return data
    except httpx.HTTPError:
        logger.exception("Telegram %s HTTP error", method)
        return None


def _api_get(method: str, params: dict | None = None) -> dict | None:
    if not settings.telegram_bot_token:
        return None
    try:
        with httpx.Client(timeout=15) as client:
            response = client.get(api_url(method), params=params or {})
            data = response.json()
            if not data.get("ok"):
                logger.error("Telegram %s failed: %s", method, data.get("description"))
            return data
    except httpx.HTTPError:
        logger.exception("Telegram %s HTTP error", method)
        return None


def check_bot() -> tuple[bool, str | None]:
    data = _api_get("getMe")
    if not data or not data.get("ok"):
        return False, (data or {}).get("description", "Bot unreachable")
    username = data["result"].get("username")
    return True, username


def delete_webhook() -> bool:
    data = _api_post("deleteWebhook", {"drop_pending_updates": True})
    if data and data.get("ok"):
        logger.info("Telegram webhook removed, polling enabled")
        return True
    return False


def send_message(chat_id: int, text: str) -> bool:
    data = _api_post(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
    )
    return bool(data and data.get("ok"))


def get_updates(offset: int | None = None) -> list[dict]:
    params: dict = {"timeout": 0, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    data = _api_get("getUpdates", params)
    if not data or not data.get("ok"):
        return []
    return data.get("result", [])
