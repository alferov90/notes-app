import html
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app import crud
from app.config import settings
from app.database import SessionLocal
from app.telegram_client import get_updates, is_configured, send_message

logger = logging.getLogger("noteflow")

_scheduler: BackgroundScheduler | None = None
_telegram_offset: int | None = None


def _format_reminder_message(title: str, content: str) -> str:
    title = title.strip() or "Без названия"
    preview = content.strip().replace("\n", " ")
    if len(preview) > 200:
        preview = preview[:200] + "…"
    if not preview:
        preview = "—"
    return (
        "🔔 <b>Напоминание NoteFlow</b>\n\n"
        f"<b>{html.escape(title)}</b>\n"
        f"{html.escape(preview)}"
    )


def process_reminders() -> None:
    db = SessionLocal()
    try:
        due = crud.get_due_reminders(db)
        for note in due:
            if not note.owner.telegram_chat_id:
                continue
            sent = send_message(
                note.owner.telegram_chat_id,
                _format_reminder_message(note.title, note.content),
            )
            if sent:
                crud.mark_reminder_sent(db, note)
                logger.info("Reminder sent for note %s to user %s", note.id, note.user_id)
    except Exception:
        logger.exception("Reminder job failed")
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
                    "👋 Привет! Откройте ссылку из личного кабинета NoteFlow, "
                    "чтобы подключить уведомления.",
                )
                continue

            token = parts[1]
            user = crud.get_user_by_link_token(db, token)
            if not user:
                send_message(
                    chat_id,
                    "❌ Ссылка недействительна или устарела. "
                    "Создайте новую в личном кабинете NoteFlow.",
                )
                continue

            crud.link_telegram(db, user, chat_id)
            send_message(
                chat_id,
                f"✅ Telegram подключён к аккаунту <b>{user.name}</b>!\n\n"
                "Теперь вы будете получать напоминания по заметкам.",
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
    _scheduler.add_job(process_reminders, "interval", seconds=30, id="reminders")
    if is_configured():
        _scheduler.add_job(poll_telegram, "interval", seconds=3, id="telegram")
        logger.info("Telegram bot polling started (@%s)", settings.telegram_bot_username)
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram notifications disabled")
    _scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
