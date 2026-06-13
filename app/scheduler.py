import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app import crud
from app.config import settings
from app.database import SessionLocal
from app.routine_notifier import process_due_events
from app.telegram_client import delete_webhook, get_updates, is_configured, send_message

logger = logging.getLogger("noteflow")

_scheduler: BackgroundScheduler | None = None
_telegram_offset: int | None = None


def process_routines() -> None:
    db = SessionLocal()
    try:
        count = process_due_events(db)
        if count:
            logger.info("Sent %s routine notification(s)", count)
    except Exception:
        logger.exception("Routine job failed")
    finally:
        db.close()


def poll_telegram() -> None:
    global _telegram_offset
    if not is_configured():
        return

    updates = get_updates(_telegram_offset)
    if not updates:
        return

    db = SessionLocal()
    try:
        for update in updates:
            _telegram_offset = update["update_id"] + 1
            message = update.get("message") or {}
            text = (message.get("text") or "").strip()
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            if not chat_id or not text.startswith("/start"):
                continue

            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                send_message(
                    chat_id,
                    "👋 Привет! Откройте ссылку из личного кабинета DayFlow.",
                )
                continue

            token = parts[1]
            user = crud.get_user_by_link_token(db, token)
            if not user:
                send_message(chat_id, "❌ Ссылка устарела. Создайте новую в DayFlow.")
                continue

            crud.link_telegram(db, user, chat_id)
            send_message(
                chat_id,
                f"✅ DayFlow подключён, <b>{user.name}</b>!\n\n"
                "Буду присылать уведомления по вашему режиму дня.",
            )
            logger.info("Telegram linked for user %s", user.id)
    except Exception:
        logger.exception("Telegram polling failed")
    finally:
        db.close()


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        process_routines,
        "interval",
        seconds=30,
        id="routines",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=15,
        next_run_time=datetime.now(),
    )
    if is_configured():
        delete_webhook()
        _scheduler.add_job(
            poll_telegram,
            "interval",
            seconds=5,
            id="telegram",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=5,
        )
        logger.info("Telegram polling started (@%s)", settings.telegram_bot_username)
    _scheduler.start()
    logger.info("Scheduler started (routine check every 30s)")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
