from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import BaseModel
import os
from typing import Dict, Any, List

app = FastAPI(title="RiskAI API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models para responses
class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    uptime: str
    version: str

class HostConfigResponse(BaseModel):
    environment: str
    api_version: str
    host: str
    port: int
    debug_mode: bool
    database_connected: bool
    features: Dict[str, bool]
    cors_enabled: bool
    max_upload_size: str
    timestamp: str

class AlertModel(BaseModel):
    type: str
    message: str

class DashboardResponse(BaseModel):
    total_users: int
    active_sessions: int
    total_uploads: int
    system_load: str
    memory_usage: str
    disk_usage: str
    last_update: str
    alerts: List[AlertModel]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint de health check para verificar se a API está funcionando
    """
    try:
        return HealthResponse(
            status="OK",
            message="API está funcionando corretamente",
            timestamp=datetime.now().isoformat(),
            uptime="API ativa",
            version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "ERROR",
                "message": "Erro no health check",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/host-config", response_model=HostConfigResponse)
async def host_config():
    """
    Endpoint para retornar configurações do host/ambiente
    """
    try:
        return HostConfigResponse(
            environment=os.getenv('ENVIRONMENT', 'development'),
            api_version="1.0.0",
            host=os.getenv('HOST', 'localhost'),
            port=int(os.getenv('PORT', 8000)),
            debug_mode=os.getenv('DEBUG', 'False').lower() == 'true',
            database_connected=True,  # Você pode adicionar verificação real do DB
            features={
                "dashboard": True,
                "upload": True,
                "previsao": True,
                "simulacao": True
            },
            cors_enabled=True,
            max_upload_size="10MB",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Erro ao obter configurações",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/dashboard/data", response_model=DashboardResponse)
async def dashboard_data():
    """
    Endpoint para dados específicos do dashboard
    """
    try:
        # Aqui você pode buscar dados reais do seu banco/sistema
        return DashboardResponse(
            total_users=150,
            active_sessions=23,
            total_uploads=89,
            system_load="45%",
            memory_usage="67%",
            disk_usage="34%",
            last_update=datetime.now().isoformat(),
            alerts=[
                AlertModel(
                    type="info",
                    message="Sistema funcionando normalmente"
                )
            ]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Erro ao obter dados do dashboard",
                "message": str(e)
            }
        )

# Endpoint adicional para root
@app.get("/")
async def root():
    return {
        "message": "RiskAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)