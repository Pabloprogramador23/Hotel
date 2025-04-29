# Settings Manager App

O módulo `settings_manager` é um aplicativo Django para gerenciar configurações do sistema no formato chave-valor, fornecendo uma interface de usuário completa e uma API programática.

## Funcionalidades

- Armazenamento de configurações no formato chave-valor
- Interface web para listar, criar, editar e excluir configurações
- API programática para acessar configurações em outros aplicativos
- Descrições para documentar o propósito de cada configuração
- Controle de acesso baseado em permissões

## Modelos

### SystemSetting

Modelo principal para armazenar as configurações:

- `key`: String única que identifica a configuração
- `value`: Valor da configuração em formato de texto
- `description`: Descrição opcional da configuração
- `created_at`: Data/hora de criação (automático)
- `updated_at`: Data/hora da última atualização (automático)

## Views

- `settings_list`: Lista todas as configurações do sistema
- `settings_create`: Cria uma nova configuração
- `settings_edit`: Edita uma configuração existente
- `settings_delete`: Remove uma configuração

## Permissões

O acesso às views é controlado pelas permissões padrão do Django:

- `settings_manager.view_systemsetting`: Para listar configurações
- `settings_manager.add_systemsetting`: Para criar configurações
- `settings_manager.change_systemsetting`: Para editar configurações
- `settings_manager.delete_systemsetting`: Para excluir configurações

## Uso na Aplicação

### Como acessar configurações no código:

```python
from apps.settings_manager.models import SystemSetting

# Obter um valor de configuração (com valor padrão)
valor = SystemSetting.objects.filter(key='minha_chave').values_list('value', flat=True).first() or 'valor_padrao'

# Obter múltiplas configurações
configs = {item.key: item.value for item in SystemSetting.objects.filter(key__startswith='prefixo_')}
```

### Como criar uma configuração programaticamente:

```python
from apps.settings_manager.models import SystemSetting

# Criar ou atualizar uma configuração
SystemSetting.objects.update_or_create(
    key='minha_chave',
    defaults={
        'value': 'meu_valor',
        'description': 'Descrição da minha configuração'
    }
)
```

## Testes

O app inclui testes para todas as suas funcionalidades:

- Testes de modelo para verificar a criação de configurações e restrição de chave única
- Testes de views para verificar as operações CRUD nas configurações
- Testes de permissões para garantir o controle de acesso adequado

Para executar os testes específicos do app:

```bash
python -m pytest apps/settings_manager/tests.py -v
```