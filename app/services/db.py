"""
SQLite qatlami — xom SQL (ORM yo'q, plan 2.1-bo'limiga muvofiq).
WAL rejimi yoqilgan (plan 2.1-band 2): bir vaqtda yozish/o'qish
to'qnashganda "database is locked" xatosi bermasligi uchun.

Bitta global ulanish (aiosqlite.Connection) butun ilova bo'ylab
qayta ishlatiladi — har bir so'rov uchun yangi ulanish ochish
0.5 GB byudjetda ortiqcha xarajat.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger("falak.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id           INTEGER PRIMARY KEY,
    language        TEXT NOT NULL DEFAULT 'uz',
    lat             REAL,
    lon             REAL,
    place_name      TEXT,
    tz_name         TEXT NOT NULL DEFAULT 'Asia/Tashkent',
    notify_enabled  INTEGER NOT NULL DEFAULT 0,
    notify_hour     INTEGER NOT NULL DEFAULT 7,
    notify_minute   INTEGER NOT NULL DEFAULT 0,
    last_notified_date TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_notify
    ON users (notify_enabled, notify_hour, notify_minute);
"""


class Database:
    """Yupqa wrapper — ulanishni saqlaydi, oddiy CRUD metodlarini beradi."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        # WAL rejimi — plan 2.1-band 2, xatosiz ishlash uchun muhim.
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()
        logger.info("SQLite ulandi (WAL yoqilgan): %s", self._db_path)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database hali ulanmagan — avval connect() chaqiring.")
        return self._conn

    # ---------- Foydalanuvchi metodlari ----------

    async def get_user(self, tg_id: int) -> Optional[dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE tg_id = ?", (tg_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_user_if_missing(self, tg_id: int, language: str = "uz") -> dict[str, Any]:
        existing = await self.get_user(tg_id)
        if existing:
            return existing
        await self.conn.execute(
            "INSERT INTO users (tg_id, language) VALUES (?, ?)",
            (tg_id, language),
        )
        await self.conn.commit()
        return await self.get_user(tg_id)  # type: ignore[return-value]

    async def set_language(self, tg_id: int, language: str) -> None:
        await self.conn.execute(
            "UPDATE users SET language = ?, updated_at = datetime('now') WHERE tg_id = ?",
            (language, tg_id),
        )
        await self.conn.commit()

    async def set_location(self, tg_id: int, lat: float, lon: float, place_name: str) -> None:
        await self.conn.execute(
            """UPDATE users
               SET lat = ?, lon = ?, place_name = ?, updated_at = datetime('now')
               WHERE tg_id = ?""",
            (lat, lon, place_name, tg_id),
        )
        await self.conn.commit()

    async def set_notify(
        self, tg_id: int, enabled: bool, hour: int | None = None, minute: int | None = None
    ) -> None:
        if hour is None or minute is None:
            await self.conn.execute(
                """UPDATE users SET notify_enabled = ?, updated_at = datetime('now')
                   WHERE tg_id = ?""",
                (int(enabled), tg_id),
            )
        else:
            await self.conn.execute(
                """UPDATE users
                   SET notify_enabled = ?, notify_hour = ?, notify_minute = ?,
                       updated_at = datetime('now')
                   WHERE tg_id = ?""",
                (int(enabled), hour, minute, tg_id),
            )
        await self.conn.commit()

    async def mark_notified(self, tg_id: int, date_str: str) -> None:
        await self.conn.execute(
            "UPDATE users SET last_notified_date = ? WHERE tg_id = ?",
            (date_str, tg_id),
        )
        await self.conn.commit()

    async def get_users_due_for_notification(
        self, hour: int, minute: int, today_str: str
    ) -> list[dict[str, Any]]:
        """Berilgan soat:daqiqada bildirishnoma olishi kerak bo'lgan,
        va bugun hali xabar yuborilmagan foydalanuvchilar."""
        cursor = await self.conn.execute(
            """SELECT * FROM users
               WHERE notify_enabled = 1
                 AND notify_hour = ?
                 AND notify_minute = ?
                 AND lat IS NOT NULL
                 AND (last_notified_date IS NULL OR last_notified_date != ?)""",
            (hour, minute, today_str),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
