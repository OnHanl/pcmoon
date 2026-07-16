#!/bin/sh
set -e

echo "== Применяю миграции =="
python manage.py migrate --noinput

echo "== Собираю статику =="
python manage.py collectstatic --noinput

echo "== Запускаю: $@ =="
exec "$@"
