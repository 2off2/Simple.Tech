@echo off
echo 🔧 RiskAI - Inicializando...

echo 📦 Verificando e instalando dependências...
python install_dependencies.py

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erro na instalação das dependências
    pause
    exit /b 1
)

echo 🚀 Iniciando RiskAI...
python run_app.py

pause