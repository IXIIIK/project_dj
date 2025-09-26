FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# системные зависимости для psycopg и Pillow (Debian Bookworm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libpng-dev \
    libwebp-dev \
  && rm -rf /var/lib/apt/lists/*

# зависимости python
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install gunicorn

# проект
COPY . /app

# каталоги для статики/медиа
RUN mkdir -p /app/static_root /app/media
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
