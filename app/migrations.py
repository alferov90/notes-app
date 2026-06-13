import logging

from sqlalchemy import inspect, text

from app.database import engine

logger = logging.getLogger("noteflow")


def migrate_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        if "users" in tables:
            user_cols = {c["name"] for c in inspector.get_columns("users")}
            if "telegram_chat_id" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN telegram_chat_id BIGINT"))
            if "telegram_link_token" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN telegram_link_token VARCHAR(64)"))
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_telegram_link_token "
                        "ON users (telegram_link_token)"
                    )
                )

        if "routine_events" not in tables:
            logger.info("Table routine_events will be created by SQLAlchemy")
