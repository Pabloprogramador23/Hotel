# Regras do Projeto Django com Python 3 + uv

## Python & Django
- Projeto usa **Python 3.12** e **Django 5.x** (estável mais recente).
- Todo novo app Django deve ficar em `apps/<nome_do_app>/`.

## Gerenciamento de dependências
- Instalar pacotes com **uv**: `uv pip install -r requirements.txt`.
- Gerar/atualizar lockfile com `uv pip compile -o requirements.txt pyproject.toml`.
- Nunca usar `pip install` nem `pipenv`.

## Testes
- Framework oficial: **pytest** + **pytest-django**.
- Comando de testes (CI e local):  
  ```bash
  uv pip install -r requirements.txt && pytest -q
