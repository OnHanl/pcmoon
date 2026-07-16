# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости: gcc + заголовки нужны для сборки некоторых пакетов,
# libjpeg/zlib — для Pillow (обработка изображений в портфолио/отзывах).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc \
       libjpeg62-turbo-dev \
       zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x deploy/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["deploy/docker-entrypoint.sh"]
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8000", "pcservice.wsgi:application"]
