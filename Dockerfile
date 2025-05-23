FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema e uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copiar arquivos de requisitos primeiro para otimizar cache
COPY requirements.txt pyproject.toml ./
COPY uv.lock ./

# Expor a porta em que o Django vai rodar
EXPOSE 8001

# Copiar o resto do código
COPY . .

# Dar permissão de execução ao script de entrada
RUN chmod +x docker-entrypoint.sh

# Configurar entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
