import html
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session, joinedload

from app import models
from app.config import settings
from app.telegram_client import is_configured, send_message

logger = logging.getLogger("noteflow")

WEEKDAY_LABELS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _is_today(event: models.RoutineEvent, weekday: int) -> bool:
    if event.days == "all":
        return True
    return str(weekday) in {d.strip() for d in event.days.split(",") if d.strip()}


def _format_message(event: models.RoutineEvent) -> str:
    time_str = event.event_time.strftime("%H:%M")
    title = html.escape(event.title.strip())
    return (
        f"{event.emoji} <b>{time_str}</b> — {title}\n\n"
        "<i>DayFlow · режим дня</i>"
    )


def process_due_events(db: Session) -> int:
    if not is_configured():
        return 0

    tz = ZoneInfo(settings.app_timezone)
    now = datetime.now(tz)
    today = now.date()
    current_hm = (now.hour, now.minute)

    events = (
        db.query(models.RoutineEvent)
        .options(joinedload(models.RoutineEvent.owner))
        .join(models.User)
        .filter(
            models.RoutineEvent.is_active.is_(True),
            models.User.telegram_chat_id.isnot(None),
        )
        .all()
    )

    sent = 0
    for event in events:
        if not _is_today(event, now.weekday()):
            continue
        if (event.event_time.hour, event.event_time.minute) != current_hm:
            continue
        if event.last_notified_date == today:
            continue
        if not event.owner.telegram_chat_id:
            continue

        if send_message(event.owner.telegram_chat_id, _format_message(event)):
            event.last_notified_date = today
            db.commit()
            sent += 1
            logger.info("Routine notify: user=%s event=%s", event.user_id, event.id)

    return sent
