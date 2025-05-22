#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Script para inicializar o RiskAI - API e Dashboard
Versão simplificada e mais robusta
"""

import subprocess
import sys
import os
import time
import threading
import webbrowser
from pathlib import Path

def run_api():
    """Executa a API FastAPI"""
    print("🚀 Iniciando API FastAPI...")
    try:
        # Navegar para o diretório do projeto
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Executar a API
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "localhost", 
            "--port", "8000", 
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return None

def run_dashboard():
    """Executa o Dashboard Streamlit"""
    print("🎨 Iniciando Dashboard Streamlit...")
    try:
        # Aguardar a API inicializar
        time.sleep(8)
        
        # Navegar para o diretório do projeto
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        # Executar o dashboard
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "dashboard/app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.headless", "true"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar Dashboard: {e}")
        return None

def open_browser():
    """Abre o navegador após um delay"""
    time.sleep(15)  # Aguarda os serviços inicializarem
    try:
        print("🌐 Abrindo navegador...")
        webbrowser.open("http://localhost:8501")
    except Exception as e:
        print(f"❌ Erro ao abrir navegador: {e}")
        print("🔗 Acesse manualmente: http://localhost:8501")

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'streamlit': 'streamlit', 
        'pandas': 'pandas',
        'numpy': 'numpy', 
        'plotly': 'plotly', 
        'scikit-learn': 'sklearn',
        'requests': 'requests'
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Pacotes faltando: {', '.join(missing_packages)}")
        print("📦 Instale com:")
        for package in missing_packages:
            print(f"   pip install {package}")
        return False
    
    return True

def main():
    """Função principal"""
    print("🔧 RiskAI - Inicializando aplicação...")
    
    # Verificar dependências
    if not check_dependencies():
        input("Pressione Enter para continuar mesmo assim ou Ctrl+C para sair...")
    
    try:
        # Iniciar API
        api_process = run_api()
        if api_process:
            print("✅ API iniciada em http://localhost:8000")
        
        # Iniciar Dashboard
        dashboard_process = run_dashboard()
        if dashboard_process:
            print("✅ Dashboard iniciado em http://localhost:8501")
        
        # Abrir navegador em thread separada
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("\n🎉 RiskAI está rodando!")
        print("📊 Dashboard: http://localhost:8501")
        print("🔗 API: http://localhost:8000")
        print("📖 Documentação da API: http://localhost:8000/docs")
        print("\n💡 O navegador será aberto automaticamente em alguns segundos...")
        print("Pressione Ctrl+C para parar...")
        
        # Manter o script rodando
        while True:
            time.sleep(1)
            
            # Verificar se os processos ainda estão rodando
            if api_process and api_process.poll() is not None:
                print("❌ API parou de funcionar")
                break
            if dashboard_process and dashboard_process.poll() is not None:
                print("❌ Dashboard parou de funcionar")
                break
            
    except KeyboardInterrupt:
        print("\n🛑 Parando aplicação...")
        
        # Finalizar processos
        if 'api_process' in locals() and api_process:
            api_process.terminate()
        if 'dashboard_process' in locals() and dashboard_process:
            dashboard_process.terminate()
            
        print("✅ Aplicação finalizada")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()