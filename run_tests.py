#!/usr/bin/env python
"""
Script para executar testes e verificar cobertura antes do deployment
Uso: python run_tests.py
"""
import os
import subprocess
import sys

def main():
    """Executar testes com pytest e verificar cobertura"""
    try:
        print("=== Executando testes com pytest ===")
        result = subprocess.run(
            ["pytest", "-v"],
            check=True
        )
        
        print("\n=== Testes executados com sucesso! ===")
        
        # Opcional: Adicionar comando para executar cobertura de testes
        # Para isso, precisaríamos adicionar pytest-cov às dependências
        
        print("\nPara executar com cobertura de testes, instale pytest-cov:")
        print("1. Adicione 'pytest-cov>=4.1.0' ao pyproject.toml")
        print("2. Execute: uv pip install -r requirements.txt")
        print("3. Execute: pytest --cov=apps")
        
        return 0
    except subprocess.CalledProcessError:
        print("\n=== Falha na execução dos testes! ===")
        print("Corrija os erros antes de fazer o deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())