#!/bin/sh
set -e

# Частая ловушка Docker: если на хосте нет файла db.sqlite3 в момент
# первого запуска (например, файл в .gitignore и не попал на сервер
# через git clone), Docker молча создаёт на его месте ПУСТУЮ ПАПКУ
# и монтирует её вместо файла. Django падает с невнятным
# "unable to open database file". Ловим это здесь явно и понятно.
if [ -d /app/db.sqlite3 ]; then
  echo "=============================================================="
  echo "ОШИБКА: /app/db.sqlite3 — это папка, а не файл базы данных."
  echo ""
  echo "Обычно причина: на хосте не было файла db.sqlite3 при первом"
  echo "'docker compose up' (например, файл в .gitignore и не попал"
  echo "на сервер через git clone), и Docker создал пустую папку"
  echo "вместо монтирования файла."
  echo ""
  echo "Исправление на ХОСТЕ (не внутри контейнера):"
  echo "  docker compose down"
  echo "  rmdir db.sqlite3"
  echo "  touch db.sqlite3"
  echo "  docker compose up -d"
  echo "  docker compose exec web python manage.py loaddata fixtures/initial_data.json"
  echo "=============================================================="
  exit 1
fi

echo "== Применяю миграции =="
python manage.py migrate --noinput

echo "== Собираю статику =="
python manage.py collectstatic --noinput

echo "== Запускаю: $@ =="
exec "$@"
