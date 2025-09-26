FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# зависимости для psycopg и Pillow
RUN apt-get update && apt-get install -y build-essential libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# проект
COPY . /app

# статические/медиа директории
RUN mkdir -p /app/static_root /app/media && chmod -R 755 /app

# gunicorn
RUN pip install gunicorn

# скрипт запуска
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
