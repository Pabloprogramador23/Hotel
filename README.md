# Pousada Pajeú - Sistema de Gerenciamento Hoteleiro

![Versão](https://img.shields.io/badge/versão-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-brightgreen.svg)
![Django](https://img.shields.io/badge/Django-5.x-green.svg)

Sistema completo de gerenciamento hoteleiro desenvolvido com Django 5, oferecendo módulos para reservas, check-in/check-out, gestão de quartos, faturamento e relatórios administrativos.

## 🏨 Visão Geral

O Pousada Pajeú é um sistema de gerenciamento hoteleiro moderno e eficiente que permite:

- Gerenciamento completo de reservas
- Controle de disponibilidade de quartos
- Processos de check-in e check-out simplificados
- Sistema integrado de faturamento e pagamentos
- Geração de relatórios gerenciais
- API RESTful para integrações externas
- Configurações personalizáveis para diferentes estabelecimentos

## 🚀 Tecnologias

- **Python 3.12** - Linguagem de programação principal
- **Django 5.x** - Framework web de alto nível
- **PostgreSQL 15** - Banco de dados relacional (produção)
- **Caddy** - Servidor web com suporte automático a HTTPS
- **Gunicorn** - Servidor WSGI para Python
- **uv** - Gerenciador de pacotes e ambientes Python
- **pytest** - Framework para testes unitários e de integração
- **Docker** - Containerização para deploy consistente

## 📁 Estrutura do Projeto

O projeto segue uma arquitetura modular organizada em apps Django:

```
apps/
├── api/ - API RESTful para integrações
├── checkin_checkout/ - Processos de entrada e saída
├── finance/ - Faturamento e pagamentos
├── reports/ - Relatórios gerenciais
├── reservations/ - Gerenciamento de reservas
├── rooms/ - Gestão de quartos e tipos
└── settings_manager/ - Configurações do sistema
```

## 🛠️ Configuração do Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.12
- uv (gerenciador de pacotes Python)
- PostgreSQL (opcional para desenvolvimento)

### Instalação

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/pousada-pajeu.git
   cd pousada-pajeu
   ```

2. **Configuração do ambiente**:
   ```bash
   # Instale as dependências usando uv (recomendado)
   uv pip install -r requirements.txt
   ```

3. **Configure o arquivo `.env`**:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. **Execute as migrações**:
   ```bash
   python manage.py migrate
   ```

5. **Crie um superusuário**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Execute o servidor de desenvolvimento**:
   ```bash
   python manage.py runserver
   ```

## ⚙️ Gerenciamento de Dependências

Seguimos práticas recomendadas para o gerenciamento de dependências:

1. Adicione novas dependências ao arquivo `pyproject.toml`
2. Gere/atualize o arquivo requirements.txt:
   ```bash
   uv pip compile -o requirements.txt pyproject.toml
   ```
3. Instale as dependências atualizadas:
   ```bash
   uv pip install -r requirements.txt
   ```

⚠️ **IMPORTANTE**: Nunca use `pip install` diretamente. Sempre utilize `uv pip install -r requirements.txt`.

## 🧪 Testes

Executamos testes com pytest:

```bash
# Instale dependências e execute testes
uv pip install -r requirements.txt && pytest -q
```

Para testes com cobertura:
```bash
pytest --cov=apps
```

## 🐳 Deploy com Docker

O projeto está configurado para deploy com Docker e Docker Compose:

```bash
# Construir e iniciar todos os serviços
docker-compose up -d
```

A configuração inclui:
- Container Django com Gunicorn
- PostgreSQL 15 para banco de dados
- Caddy como servidor web com certificado SSL automático

## 📋 CI/CD

O repositório inclui workflows para CI/CD que automatizam:

- Testes automatizados em cada push
- Verificação de código com flake8, black e isort
- Deploy automatizado em ambientes de staging e produção

## 📄 Documentação da API

A API RESTful está disponível em `/api/v1/` e inclui endpoints para:

- Gerenciamento de reservas
- Disponibilidade de quartos
- Processos de check-in e check-out
- Faturas e pagamentos
- Relatórios administrativos

Documentação interativa disponível em `/api/docs/` (Swagger).

## 👥 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Escreva testes para sua feature
4. Faça commit das mudanças (`git commit -m 'Adiciona nova feature'`)
5. Faça push para a branch (`git push origin feature/nome-da-feature`)
6. Abra um Pull Request

## 📜 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

© 2025 Pousada Pajeú. Todos os direitos reservados.