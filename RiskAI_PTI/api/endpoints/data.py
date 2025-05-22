from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
from typing import Optional, Dict, Any
import sys

# Adiciona o diretório raiz ao path para que o Python possa encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar módulos do core
from core import data_processing, scenario_simulator

# Importar o estado compartilhado
from api.endpoints import state

# Criar diretório para uploads se não existir
if not os.path.exists(state.UPLOAD_DIR):
    os.makedirs(state.UPLOAD_DIR)

# Definir o router
router = APIRouter()

# Definir o modelo de resposta
class FileUploadResponse(BaseModel):
    filename: str
    message: str
    file_path: Optional[str] = None
    error: Optional[str] = None

@router.post("/upload_csv", response_model=FileUploadResponse)
async def upload_csv_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(state.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Processar o arquivo carregado
        df = data_processing.processar_arquivo_completo(file_path)
        if df is None:
            # Obter a mensagem de erro específica
            error_msg = getattr(data_processing.processar_arquivo_completo, 'last_error', 
                               "Erro desconhecido ao processar o arquivo CSV")
            raise HTTPException(status_code=400, detail=error_msg)
        
        state.global_processed_df = df
        state.global_prediction_model = None  # Resetar modelo se novos dados forem carregados
        state.global_historical_stats = scenario_simulator.calcular_estatisticas_historicas(state.global_processed_df)

        return FileUploadResponse(
            filename=file.filename, 
            message="Arquivo CSV carregado e processado com sucesso.",
            file_path=file_path
        )
    except HTTPException as http_exc:
        return FileUploadResponse(
            filename=file.filename, 
            message="Erro de validação", 
            error=http_exc.detail
         )
    except Exception as e:
        return FileUploadResponse(
            filename=file.filename, 
            message="Erro interno do servidor", 
            error=str(e) if str(e) else "Erro desconhecido"
        )


@router.get("/view_processed")
async def view_processed_data(limit: int = 5):
    try:
        if state.global_processed_df is None:
            raise HTTPException(
                status_code=404,
                detail="Nenhum dado processado disponível. Faça upload de um arquivo primeiro"
            )
        
        return JSONResponse(
            content=state.global_processed_df.head(limit).to_dict(orient="records")
        )
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Erro ao visualizar dados: {str(e )}")
        return JSONResponse(
            status_code=500,
            content={
                "message": "Erro no processamento",
                "error": str(e)
            }
        )
