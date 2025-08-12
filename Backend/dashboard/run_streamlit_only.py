#!/usr/bin/env python3
"""
Script para executar apenas o Dashboard Streamlit
Para usar quando a API já está rodando separadamente
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def main():
    """Executa apenas o dashboard Streamlit"""
    print("Iniciando Dashboard Streamlit...")
    
    try:
        # Navegar para o diretório do projeto
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        print("Diretório atual:", os.getcwd())
        
        # Aguardar um pouco e abrir o navegador
        def open_browser_delayed():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8501")
            except:
                pass
        
        import threading
        threading.Thread(target=open_browser_delayed, daemon=True).start()
        
        # Executar o dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", 
            "run", "dashboard/app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except Exception as e:
        print(f"❌ Erro ao iniciar Dashboard: {e}")
        print(" Tente executar manualmente:")
        print("   streamlit run dashboard/app.py --server.port 8501")

if __name__ == "__main__":
    main()