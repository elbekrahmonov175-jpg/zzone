# 🎮 Computer Club Bot

Полнофункциональный Telegram-бот для компьютерного клуба на **Python + aiogram 3.x + SQLite**.

---

## 📁 Структура проекта

```
computer_club_bot/
├── main.py                      # Точка входа
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example                 # Шаблон переменных окружения
├── .gitignore
│
├── config/
│   ├── __init__.py
│   └── settings.py              # Загрузка .env настроек
│
├── database/
│   ├── __init__.py
│   ├── db.py                    # Инициализация БД, get_db()
│   ├── users.py                 # CRUD пользователей и blacklist
│   ├── bookings.py              # CRUD бронирований
│   └── queries.py               # Цены, акции, локация, статистика
│
├── handlers/
│   ├── __init__.py
│   ├── common.py                # /start, главное меню
│   ├── booking.py               # FSM бронирования + мои брони + отмена
│   ├── info.py                  # Прайс-лист, акции, локация
│   ├── contact.py               # Связь с администратором
│   ├── admin_bookings.py        # Управление заявками (подтвердить/отклонить)
│   ├── admin_manage.py          # Статистика, цены, акции, локация
│   └── admin_broadcast.py      # Рассылка и чёрный список
│
├── keyboards/
│   ├── __init__.py
│   ├── user_kb.py               # Клавиатуры для пользователей
│   └── admin_kb.py              # Клавиатуры для администраторов
│
├── middlewares/
│   ├── __init__.py
│   └── user_middleware.py       # Авторегистрация пользователей
│
└── utils/
    ├── __init__.py
    ├── notifications.py         # Утилиты уведомлений
    └── scheduler.py             # Планировщик напоминаний за 30 мин
```

---

## ⚡ Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/yourname/computer_club_bot.git
cd computer_club_bot
```

### 2. Создайте файл `.env`

```bash
cp .env.example .env
```

Откройте `.env` и заполните:

```env
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
ADMIN_IDS=ВАШ_TELEGRAM_ID
DATABASE_PATH=data/club.db
TIMEZONE=Asia/Tashkent
```

> 🔑 **Узнать свой Telegram ID**: напишите боту [@userinfobot](https://t.me/userinfobot)

### 3. Установите зависимости

```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

### 4. Запустите бота

```bash
python main.py
```

---

## 🐳 Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

---

## 🎯 Функциональность

### Пользователи
| Функция | Команда/кнопка |
|---------|----------------|
| Главное меню | `/start` |
| Забронировать место | 🎮 Забронировать место |
| Просмотр цен | 💰 Прайс-лист |
| Акции | 🎁 Акции |
| Адрес и геолокация | 📍 Локация |
| Написать администратору | 💬 Связаться с администратором |
| Отменить бронь | ❌ Отменить бронь |
| Мои бронирования | 📋 Мои бронирования |

### Администраторы
| Функция | Описание |
|---------|----------|
| Панель управления | `/admin` |
| Заявки | Подтвердить / Отклонить / Предложить другое время |
| Статистика | Пользователи, брони по статусам, топ зоны |
| Цены | Редактирование Standard / VIP / PS5 |
| Акции | Создать / Изменить / Удалить / Включить-Выключить |
| Локация | Адрес, телефон, Telegram, координаты |
| Рассылка | Текст / Фото / Видео всем пользователям |
| Чёрный список | Добавить / Удалить / Просмотреть |

---

## ⏰ Напоминания за 30 минут

Бот автоматически каждую минуту проверяет подтверждённые брони и отправляет пользователю сообщение:

> ⏰ До вашей игры осталось **30 минут**! Вы уже едете? 🚀

**Важно**: время в базе данных хранится в UTC. При вводе времени бронирования (через кнопки) — это местное время пользователя. Если сервер запущен в другом часовом поясе, скорректируйте логику в `database/bookings.py` в функции `get_unreminded_upcoming_bookings`.

---

## 🗄 База данных

SQLite файл хранится в `data/club.db`. Таблицы:

| Таблица | Назначение |
|---------|------------|
| `users` | Зарегистрированные пользователи |
| `bookings` | Все бронирования с историей |
| `prices` | Цены по зонам |
| `promotions` | Акции (активные/неактивные) |
| `location` | Адрес и координаты клуба |
| `admins` | (резерв для будущих фич) |
| `blacklist` | Заблокированные пользователи |

### Переход на PostgreSQL

Замените в `database/db.py`:
```python
# SQLite (текущее)
import aiosqlite
db = await aiosqlite.connect(settings.DATABASE_PATH)

# PostgreSQL (будущее)
import asyncpg
db = await asyncpg.connect(settings.DATABASE_URL)
```

---

## 📝 Логирование

Логи пишутся одновременно в:
- **Консоль** — для отладки
- **`logs/bot.log`** — для мониторинга

---

## 🔧 Требования

- Python 3.11+
- aiogram 3.13+
- aiosqlite 0.20+
- python-dotenv 1.0+
