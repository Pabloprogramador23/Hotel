FROM python:3.12-slim

# Argumentos de build
ARG DJANGO_ENV=production

# Variáveis de ambiente
ENV DJANGO_ENV=${DJANGO_ENV} \
    # python:
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    # pip:
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Configurações específicas para a aplicação
    DJANGO_SETTINGS_MODULE=hotel_hms.settings_prod \
    # Diretório da aplicação
    APP_HOME=/app

# Criar diretório da aplicação
WORKDIR ${APP_HOME}

# Instalar dependências do sistema necessárias para psycopg2 e outras libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gettext \
    gcc \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN pip install uv

# Instalar psycopg2 diretamente para garantir que esteja disponível
RUN pip install psycopg2-binary

# Copiar arquivos de dependências
COPY pyproject.toml requirements.txt ${APP_HOME}/

# Instalar dependências utilizando uv com a flag --system
RUN uv pip install --system -r requirements.txt

# Copiar o projeto
COPY . ${APP_HOME}/

# Criar diretório para arquivos estáticos, mídia e logs
RUN mkdir -p ${APP_HOME}/staticfiles ${APP_HOME}/media ${APP_HOME}/logs

# Copiar script de entrypoint e torná-lo executável
COPY entrypoint.sh ${APP_HOME}/
RUN chmod +x ${APP_HOME}/entrypoint.sh

# Porta que o servidor do Django irá ouvir
EXPOSE 8000

# Usuário não-root para segurança
RUN adduser --disabled-password --gecos "" django
RUN chown -R django:django ${APP_HOME}
USER django

# Comando de inicialização
ENTRYPOINT ["./entrypoint.sh"]

# Comando padrão que será executado quando o contêiner iniciar
CMD ["gunicorn", "--config", "gunicorn_config.py", "hotel_hms.wsgi:application"]