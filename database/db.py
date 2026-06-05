"""
Инициализация базы данных SQLite.
Создаёт все таблицы при первом запуске.
Архитектура позволяет легко переключиться на PostgreSQL (aiopg/asyncpg).
"""

import aiosqlite
import logging
import os
from config.settings import settings

logger = logging.getLogger(__name__)

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id   INTEGER UNIQUE NOT NULL,
    username      TEXT,
    full_name     TEXT,
    phone         TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    zone          TEXT NOT NULL CHECK(zone IN ('Standard', 'VIP', 'PS5')),
    booking_date  TEXT NOT NULL,
    booking_time  TEXT NOT NULL,
    duration      INTEGER NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending','confirmed','rejected','cancelled')),
    admin_comment TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    reminded      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS prices (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    zone       TEXT UNIQUE NOT NULL,
    price_hour INTEGER NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promotions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    description TEXT NOT NULL,
    is_active  INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS location (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    address   TEXT NOT NULL,
    phone     TEXT NOT NULL,
    telegram  TEXT NOT NULL,
    latitude  REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS admins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name   TEXT,
    added_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blacklist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    reason      TEXT,
    added_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

INITIAL_DATA_SQL = """
INSERT OR IGNORE INTO prices (zone, price_hour) VALUES
    ('Standard', 5000),
    ('VIP', 10000),
    ('PS5', 15000);

INSERT OR IGNORE INTO location (address, phone, telegram, latitude, longitude) VALUES
    ('г. Ташкент, ул. Примерная, д. 1', '+998 90 000 00 00', '@computer_club_tg', 41.2995, 69.2401);
"""


def get_db():
    """
    Возвращает контекстный менеджер нового соединения с базой данных.
    Использование: async with get_db() as db: ...
    ВАЖНО: каждый вызов создаёт НОВОЕ соединение — aiosqlite не позволяет
    переиспользовать один объект соединения в разных корутинах.
    """
    return aiosqlite.connect(settings.DATABASE_PATH)


async def _setup_connection(db: aiosqlite.Connection):
    """Настраивает соединение: row_factory и foreign keys."""
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON;")


async def init_db():
    """Инициализирует базу данных: создаёт таблицы и добавляет начальные данные."""
    os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)

    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(CREATE_TABLES_SQL)
        await db.executescript(INITIAL_DATA_SQL)
        await db.commit()

    logger.info("✅ База данных инициализирована: %s", settings.DATABASE_PATH)
