#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Função para aguardar o PostgreSQL estar disponível
postgres_ready() {
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        dbname="${DB_NAME:-hotel_db}",
        user="${DB_USER:-postgres}",
        password="${DB_PASSWORD}",
        host="${DB_HOST:-db}",
        port="${DB_PORT:-5432}",
    )
except psycopg2.OperationalError:
    sys.exit(1)
sys.exit(0)
END
}

# Aguardar até que o PostgreSQL esteja disponível
until postgres_ready; do
  echo "PostgreSQL indisponível - aguardando..."
  sleep 1
done
echo "PostgreSQL disponível!"

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migrações do Django
echo "Aplicando migrações..."
python manage.py migrate --noinput

# Criar superusuário (opcional)
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
  echo "Criando superusuário..."
  python manage.py createsuperuser --noinput || echo "Superusuário já existe ou não pôde ser criado."
fi

# Executar o comando passado para o entrypoint
exec "$@"