# Hotel HMS - Sistema de Gerenciamento Hoteleiro

Sistema de gerenciamento hoteleiro completo com módulos para reservas, check-in/check-out, gestão de quartos, faturamento e relatórios.

## Requisitos

- Python 3.12+
- Django 5.x
- PostgreSQL (produção)
- Redis (cache em produção)
- uv (gerenciador de pacotes)

## Estrutura do Projeto

O projeto está organizado nos seguintes módulos:

- **apps/reservations**: Gerenciamento de reservas
- **apps/rooms**: Gerenciamento de quartos
- **apps/checkin_checkout**: Processos de check-in e check-out
- **apps/finance**: Faturamento e pagamentos
- **apps/reports**: Relatórios gerenciais
- **apps/settings_manager**: Gerenciamento de configurações do sistema
- **apps/api**: API para integração com outros sistemas

## Setup do Ambiente de Desenvolvimento

1. Clone o repositório:
   ```bash
   git clone [url-do-repositorio]
   cd hotel-hms
   ```

2. Instale as dependências usando uv (recomendado):
   ```bash
   uv pip install -r requirements.txt
   ```

3. Configure o arquivo `.env` a partir do `.env.example`:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

4. Execute as migrações:
   ```bash
   python manage.py migrate
   ```

5. Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```

6. Execute o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```

## Testes

Execute os testes usando o script fornecido:
```bash
python run_tests.py
```

Para executar testes com cobertura:
1. Adicione `pytest-cov>=4.1.0` ao `pyproject.toml`
2. Execute `uv pip install -r requirements.txt`
3. Execute `pytest --cov=apps`

## Gerenciamento de Dependências

- Adicione novas dependências ao arquivo `pyproject.toml`
- Atualize o arquivo `requirements.txt` usando o script fornecido:
  ```bash
  python update_requirements.py
  ```

## Preparação para Deployment

### Checklist de Pré-Deployment

1. **Configuração do Ambiente**:
   - Copie `.env.example` para `.env` no servidor de produção
   - Configure todas as variáveis de ambiente necessárias
   - Garanta que `DJANGO_SETTINGS_MODULE=hotel_hms.settings_prod`

2. **Banco de Dados**:
   - Configure PostgreSQL para produção
   - Execute as migrações iniciais: `python manage.py migrate`

3. **Arquivos Estáticos**:
   - Execute `python manage.py collectstatic`
   - Verifique se o diretório `STATIC_ROOT` está configurado corretamente

4. **Segurança**:
   - Garanta que `DEBUG=False`
   - Configure uma `SECRET_KEY` segura
   - Configure `ALLOWED_HOSTS` apropriadamente
   - Verifique configurações SSL/HTTPS

5. **Servidor Web**:
   - Configure o servidor Gunicorn usando `gunicorn_config.py`:
     ```bash
     gunicorn hotel_hms.wsgi:application -c gunicorn_config.py
     ```
   - Configure Nginx como proxy reverso (recomendado)

## Estrutura de Deployment Recomendada

```
[Servidor Web (Nginx)] 
       ↓
[WSGI (Gunicorn)] → [Django Application]
       ↓
[Banco de Dados (PostgreSQL)]
```

## Monitoramento em Produção

Recomendações para monitoramento:
- Configure logging apropriado (já configurado em `settings_prod.py`)
- Implemente um sistema de monitoramento de saúde da aplicação
- Configure alertas para erros críticos

## Manutenção

Para atualizar o sistema em produção:
1. Faça backup do banco de dados
2. Pull das últimas mudanças do repositório
3. Atualize dependências: `uv pip install -r requirements.txt`
4. Execute migrações: `python manage.py migrate`
5. Colete arquivos estáticos: `python manage.py collectstatic --noinput`
6. Reinicie o servidor Gunicorn

## Exemplos de Uso da API

### Obter Estatísticas do Dashboard
```bash
curl -X GET http://localhost:8000/api/dashboard/stats/ -H "Authorization: Token <seu_token>"
```

### Listar Quartos Disponíveis
```bash
curl -X GET "http://localhost:8000/api/available-rooms/?room_type=single&check_in=2025-05-01&check_out=2025-05-05" -H "Authorization: Token <seu_token>"
```

### Criar uma Nova Reserva
```bash
curl -X POST http://localhost:8000/api/reservations/ \
-H "Content-Type: application/json" \
-H "Authorization: Token <seu_token>" \
-d '{
    "guest_name": "John Doe",
    "guest_email": "john.doe@example.com",
    "room_id": 1,
    "check_in_date": "2025-05-01",
    "check_out_date": "2025-05-05",
    "notes": "Preferência por andar alto",
    "status": "confirmed"
}'
```

### Realizar Check-in
```bash
curl -X POST http://localhost:8000/checkin_checkout/checkin/1/ \
-H "Authorization: Token <seu_token>"
```

### Realizar Check-out
```bash
curl -X POST http://localhost:8000/checkin_checkout/checkout/1/ \
-H "Authorization: Token <seu_token>"
```

### Adicionar Pagamento a uma Fatura
```bash
curl -X POST http://localhost:8000/api/finance/payments/ \
-H "Content-Type: application/json" \
-H "Authorization: Token <seu_token>" \
-d '{
    "invoice_id": 1,
    "amount": 350.00,
    "method": "Cartão de Crédito",
    "notes": "Pagamento parcial"
}'
```