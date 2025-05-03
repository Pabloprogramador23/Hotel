#!/usr/bin/env python
"""
Script para iniciar o servidor de desenvolvimento Django.
Executa migrações e coleta arquivos estáticos antes de iniciar o servidor.
"""
import os
import subprocess
import sys

def main():
    """Executa comandos de preparação e inicia o servidor de desenvolvimento."""
    # Diretório do projeto
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_hms.settings")
    
    print("🔄 Instalando/atualizando dependências...")
    subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
    
    print("\n🗃️ Aplicando migrações do banco de dados...")
    subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
    
    print("\n📁 Coletando arquivos estáticos...")
    subprocess.run(["python", "manage.py", "collectstatic", "--noinput"], check=True)
    
    # Verificar se já existe um superusuário
    print("\n👤 Verificando superusuário...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        print("Criando superusuário padrão (admin/admin)...")
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Superusuário criado com sucesso!")
    else:
        print("Superusuário já existe.")
    
    # Porta padrão
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    
    print(f"\n🚀 Iniciando servidor em http://127.0.0.1:{port}/")
    subprocess.run(["python", "manage.py", "runserver", f"0.0.0.0:{port}"])

if __name__ == "__main__":
    main()