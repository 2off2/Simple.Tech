"""
Aplicação principal FastAPI para RiskAI_PTI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    
    # Registrar routers
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