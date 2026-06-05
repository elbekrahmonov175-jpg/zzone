"""
Настройки бота — загрузка переменных из .env файла.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # Telegram Bot Token
    BOT_TOKEN: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))

    # ID администраторов (через запятую в .env)
    ADMIN_IDS: List[int] = field(default_factory=list)

    # Путь к SQLite базе данных
    DATABASE_PATH: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "data/club.db"))

    # Часовой пояс клуба (для корректной работы уведомлений)
    TIMEZONE: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Tashkent"))

    def __post_init__(self):
        raw = os.getenv("ADMIN_IDS", "")
        if raw:
            self.ADMIN_IDS = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


settings = Settings()
