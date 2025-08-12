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
        print(f"📥 Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar {package}: {e}")
        return False

def check_package_installed(package_name, import_name=None):
    """Verifica se um pacote está instalado"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def main():
    """Instala todas as dependências necessárias"""
    print("📦 Verificando e instalando dependências do RiskAI...")
    
    # Lista de pacotes essenciais com nomes de importação corretos
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("plotly", "plotly"),
        ("scikit-learn", "sklearn"),  # Importante: sklearn é o nome para importação
        ("requests", "requests"),
        ("python-multipart", "multipart"),
        ("pydantic", "pydantic")
    ]
    
    failed_packages = []
    installed_packages = []
    
    for package_name, import_name in packages:
        if check_package_installed(package_name, import_name):
            print(f"✅ {package_name} já está instalado")
            installed_packages.append(package_name)
        else:
            if install_package(package_name):
                print(f"✅ {package_name} instalado com sucesso")
                installed_packages.append(package_name)
            else:
                failed_packages.append(package_name)
    
    print(f"\n📊 Resumo da instalação:")
    print(f"✅ Pacotes instalados: {len(installed_packages)}")
    print(f"❌ Pacotes com erro: {len(failed_packages)}")
    
    if failed_packages:
        print(f"\n❌ Falha ao instalar: {', '.join(failed_packages)}")
        print("💡 Tente executar manualmente:")
        for package in failed_packages:
            print(f"   pip install {package}")
        
        print("\n🔄 Alternativa: instale via requirements.txt:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("\n🎉 Todas as dependências foram instaladas com sucesso!")
        return True

if __name__ == "__main__":
    success = main()
    if success: 
        print("\n🚀 Agora você pode executar: python dashboard/run_app.py")
    else:
        print("\n⚠️  Resolva os erros de instalação antes de continuar")
        sys.exit(1)