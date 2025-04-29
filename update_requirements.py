#!/usr/bin/env python
"""
Script para atualizar o arquivo requirements.txt a partir do pyproject.toml
Uso: python update_requirements.py
"""
import os
import subprocess
import sys

def main():
    """Executar comando para atualizar requirements.txt"""
    try:
        print("Atualizando requirements.txt a partir do pyproject.toml...")
        result = subprocess.run(
            ["uv", "pip", "compile", "-o", "requirements.txt", "pyproject.toml"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Arquivo requirements.txt atualizado com sucesso!")
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Erro ao atualizar requirements.txt: {e}")
        print(e.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())