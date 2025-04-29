#!/usr/bin/env python
"""
Script para migrar dados do app antigo para o settings_manager.SystemSetting.
Execute este script antes de remover o app administration do projeto.

Uso: python migrate_settings_data.py
"""
import os
import django
import sys
from datetime import datetime

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hotel_hms.settings')
django.setup()

def migrate_settings():
    """
    Migra os registros de SystemSetting do app antigo para o settings_manager.
    """
    try:
        # Importar os modelos após configuração do Django
        from apps.administration.models import SystemSetting as OldSystemSetting
        from apps.settings_manager.models import SystemSetting as NewSystemSetting
        
        # Contar registros no modelo antigo
        old_settings_count = OldSystemSetting.objects.count()
        print(f"Encontrados {old_settings_count} registros no modelo antigo.")
        
        if old_settings_count == 0:
            print("Não há dados para migrar.")
            return True
        
        # Migrar cada configuração
        migrated_count = 0
        for old_setting in OldSystemSetting.objects.all():
            # Verificar se já existe uma configuração com a mesma chave
            if NewSystemSetting.objects.filter(key=old_setting.key).exists():
                print(f"AVISO: Configuração com chave '{old_setting.key}' já existe no novo modelo. Pulando.")
                continue
                
            # Criar nova configuração
            new_setting = NewSystemSetting(
                key=old_setting.key,
                value=old_setting.value,
                description=f"Migrado de administration em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
            new_setting.save()
            migrated_count += 1
            print(f"Migrado: {old_setting.key}")
        
        print(f"\nMigração concluída. {migrated_count} de {old_settings_count} configurações foram migradas.")
        return True
    
    except ImportError as e:
        print(f"Erro ao importar modelos: {e}")
        print("Certifique-se de que o app 'settings_manager' esteja instalado.")
        return False
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando migração de dados...")
    success = migrate_settings()
    if success:
        print("\nPróximos passos:")
        print("1. Faça as migrações do novo app: python manage.py makemigrations apps.settings_manager")
        print("2. Aplique as migrações: python manage.py migrate")
        print("3. O app 'administration' já foi removido.")
        print("4. Atualize as URLs para usar o novo app (já feito)")
        sys.exit(0)
    else:
        print("\nA migração não foi concluída devido a erros. Corrija os problemas e tente novamente.")
        sys.exit(1)