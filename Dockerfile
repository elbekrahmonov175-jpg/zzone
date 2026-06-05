# ──────────────────────────────────────────────
# Dockerfile для Computer Club Bot
# ──────────────────────────────────────────────

FROM python:3.12-slim

# Метаданные
LABEL maintainer="Computer Club Bot"
LABEL version="1.0"

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаём директории для данных и логов
RUN mkdir -p data logs

# Запуск бота
CMD ["python", "main.py"]
