#!/usr/bin/env python3
"""
Script para instalar as dependências do RiskAI
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Instala um pacote usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Instala todas as dependências necessárias"""
    print("📦 Instalando dependências do RiskAI...")
    
    # Lista de pacotes essenciais
    packages = [
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0", 
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.17.0",
        "scikit-learn>=1.2.0",
        "requests>=2.31.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        package_name = package.split(">=")[0]
        print(f"📥 Instalando {package_name}...")
        
        if install_package(package):
            print(f"✅ {package_name} instalado com sucesso")
        else:
            print(f"❌ Falha ao instalar {package_name}")
            failed_packages.append(package_name)
    
    if failed_packages:
        print(f"\n❌ Falha ao instalar: {', '.join(failed_packages)}")
        print("💡 Tente executar manualmente:")
        print(f"   pip install {' '.join(failed_packages)}")
        return False
    else:
        print("\n🎉 Todas as dependências foram instaladas com sucesso!")
        return True

if __name__ == "__main__":
    success = main()
    if success: 
        print("\n🚀 Agora você pode executar: python run_app.py")
    else:
        print("\n⚠️  Resolva os erros de instalação antes de continuar")
        sys.exit(1)