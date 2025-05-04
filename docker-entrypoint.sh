#!/bin/bash
set -e

echo "Instalando dependências com uv..."
uv pip install -r requirements.txt

echo "Aplicando migrações do Django..."
python manage.py migrate --no-input

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "Iniciando Gunicorn..."
exec gunicorn --bind 0.0.0.0:8001 hotel_hms.wsgi:application