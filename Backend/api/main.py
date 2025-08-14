"""
Aplicação principal FastAPI para RiskAI_PTI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar routers dos endpoints
from api.endpoints.data import router as data_router
from api.endpoints.predictions import router as predictions_router
from api.endpoints.simulations import router as simulations_router

def create_app() -> FastAPI:
    """
    Cria e configura a aplicação FastAPI
    """
    app = FastAPI(
        title="RiskAI PTI",
        description="API para análise de risco e previsão de fluxo de caixa",
        version="1.0.0"
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especificar origins específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Registrar routers com prefixos corretos
    app.include_router(data_router, prefix="/api/data", tags=["data"])
    app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
    app.include_router(simulations_router, prefix="/api/simulations", tags=["simulations"])
    
    app.include_router(data_router, prefix="/api/data", tags=["data"])
    app.include_router(predictions_router, prefix="/api/predictions", tags=["predictions"])
    app.include_router(simulations_router, prefix="/api/simulations", tags=["simulations"])
    # Endpoint raiz
    @app.get("/")
    async def root():
        return {
            "message": "RiskAI PTI API está funcionando",
            "version": "1.0.0",
            "endpoints": [
                "/api/data/upload_csv",
                "/api/data/view_processed", 
                "/api/predictions/cashflow",
                "/api/simulations/scenarios"
            ]
        }
    
    # Endpoint de saúde
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app

# Criar instância da aplicação
app = create_app()

# Para execução com uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

@app.get("/host-config")
async def host_config():
    """
    Endpoint para retornar configurações do host/ambiente
    """
    try:
        from datetime import datetime
        
        config = {
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'api_version': '1.0.0',
            'host': os.getenv('HOST', 'localhost'),
            'port': int(os.getenv('PORT', 8000)),
            'debug_mode': os.getenv('DEBUG', 'False').lower() == 'true',
            'database_connected': True,
            'features': {
                'dashboard': True,
                'upload': True,
                'previsao': True,
                'simulacao': True
            },
            'cors_enabled': True,
            'max_upload_size': '10MB',
            'timestamp': datetime.now().isoformat()
        }
        
        return config
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Erro ao obter configurações",
                "message": str(e)
            }
        )

app = FastAPI(title="Simple.Tech API")

# Permitir conexão com o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL do Vite
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Simple.Tech API funcionando!"}

@app.post("/analyze")
def analyze_data(data: dict):
    # Aqui você chama seus algoritmos Python
    result = sua_funcao_de_analise(data)
    return {"result": result, "status": "success"}