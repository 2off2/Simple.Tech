#!/usr/bin/env python3
"""
Script para inicializar o RiskAI - API e Dashboard
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_api():
    """Executa a API FastAPI"""
    print("🚀 Iniciando API FastAPI...")
    try:
        # Navegar para o diretório do projeto
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # Executar a API
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")

def run_dashboard():
    """Executa o Dashboard Streamlit"""
    print("🎨 Iniciando Dashboard Streamlit...")
    try:
        # Aguardar a API inicializar
        time.sleep(5)
        
        # Navegar para o diretório do projeto
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # Executar o dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "dashboard/app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0"
        ])
    except Exception as e:
        print(f"❌ Erro ao iniciar Dashboard: {e}")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required_packages = [
        'fastapi', 'uvicorn', 'streamlit', 'pandas', 
        'numpy', 'plotly', 'scikit-learn', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Pacotes faltando: {', '.join(missing_packages)}")
        print("📦 Instale com: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Função principal"""
    print("🔧 RiskAI - Inicializando aplicação...")
    
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Criar threads para API e Dashboard
    api_thread = threading.Thread(target=run_api, daemon=True)
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    
    try:
        # Iniciar API
        api_thread.start()
        print("✅ API iniciada em http://localhost:8000")
        
        # Iniciar Dashboard
        dashboard_thread.start()
        print("✅ Dashboard iniciado em http://localhost:8501")
        
        print("\n🎉 RiskAI está rodando!")
        print("📊 Dashboard: http://localhost:8501")
        print("🔗 API: http://localhost:8000")
        print("📖 Documentação da API: http://localhost:8000/docs")
        print("\nPressione Ctrl+C para parar...")
        
        # Manter o script rodando
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Parando aplicação...")
        sys.exit(0)

if __name__ == "__main__":
    main()