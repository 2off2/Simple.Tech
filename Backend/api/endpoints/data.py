from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
from typing import Optional, Dict, Any
import sys
import numpy as np

# Adiciona o diretório raiz ao path para que o Python possa encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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

def processar_arquivo_csv(file_path: str) -> Optional[pd.DataFrame]:
    """
    Processa o arquivo CSV carregado e retorna um DataFrame limpo
    """
    try:
        # Ler o arquivo CSV
        df = pd.read_csv(file_path)
        
        # Verificar se o DataFrame não está vazio
        if df.empty:
            raise ValueError("Arquivo CSV está vazio")
        
        # Verificar colunas obrigatórias
        required_cols = ["data", "descricao"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_cols)}")
        
        # Converter coluna de data
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        
        # Remover linhas com datas inválidas
        df = df.dropna(subset=["data"])
        
        if df.empty:
            raise ValueError("Nenhuma data válida encontrada no arquivo")
        
        # Garantir que colunas numéricas existam (criar com 0 se não existirem)
        numeric_cols = ["entrada", "saida", "valor_fatura"]
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        
        # Calcular fluxo diário se não existir
        if "fluxo_diario" not in df.columns:
            df["fluxo_diario"] = df["entrada"] - df["saida"]
        
        # Calcular saldo acumulado se não existir
        if "saldo" not in df.columns:
            df = df.sort_values("data")
            df["saldo"] = df["fluxo_diario"].cumsum()
        
        # Converter colunas de data opcionais
        date_cols = ["data_vencimento", "data_pagamento"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        return df
        
    except Exception as e:
        print(f"Erro ao processar arquivo CSV: {str(e)}")
        return None

def calcular_estatisticas_historicas(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula estatísticas básicas do DataFrame histórico
    """
    if df.empty:
        return {}
    
    estatisticas = {}
    
    # Estatísticas de entrada e saída
    if "entrada" in df.columns and "saida" in df.columns:
        estatisticas["media_entrada"] = df["entrada"].mean()
        estatisticas["media_saida"] = df["saida"].mean()
        estatisticas["desvio_padrao_entrada"] = df["entrada"].std()
        estatisticas["desvio_padrao_saida"] = df["saida"].std()
    
    # Estatísticas de fluxo
    if "fluxo_diario" in df.columns:
        estatisticas["media_fluxo"] = df["fluxo_diario"].mean()
        estatisticas["desvio_padrao_fluxo"] = df["fluxo_diario"].std()
    
    # Estatísticas de saldo
    if "saldo" in df.columns:
        estatisticas["ultimo_saldo"] = df["saldo"].iloc[-1]
        estatisticas["media_saldo"] = df["saldo"].mean()
    
    # Estatísticas temporais
    df_sorted = df.sort_values("data")
    estatisticas["primeira_data"] = df_sorted["data"].iloc[0]
    estatisticas["ultima_data"] = df_sorted["data"].iloc[-1]
    
    return estatisticas

@router.post("/upload_csv", response_model=FileUploadResponse)
async def upload_csv_file(file: UploadFile = File(...)):
    try:
        # Verificar se o arquivo é CSV
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser do tipo CSV")
        
        # Salvar arquivo
        file_path = os.path.join(state.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Processar o arquivo carregado
        df = processar_arquivo_csv(file_path)
        if df is None:
            raise HTTPException(status_code=400, detail="Erro ao processar o arquivo CSV. Verifique o formato e conteúdo.")
        
        # Armazenar no estado global
        state.global_processed_df = df
        state.global_prediction_model = None  # Resetar modelo se novos dados forem carregados
        state.global_historical_stats = calcular_estatisticas_historicas(df)

        return FileUploadResponse(
            filename=file.filename, 
            message="Arquivo CSV carregado e processado com sucesso.",
            file_path=file_path
        )
    except HTTPException as http_exc:
        return FileUploadResponse(
            filename=file.filename if file else "unknown", 
            message="Erro de validação", 
            error=str(http_exc.detail)
         )
    except Exception as e:
        return FileUploadResponse(
            filename=file.filename if file else "unknown", 
            message="Erro interno do servidor", 
            error=str(e) if str(e) else "Erro desconhecido"
        )

@router.get("/view_processed")
async def view_processed_data(limit: int = 5):
    try:
        if state.global_processed_df is None or state.global_processed_df.empty:
            # Adicionado verificação de DataFrame vazio
            raise HTTPException(
                status_code=404,
                detail="Nenhum dado processado disponível ou DataFrame vazio. Faça upload de um arquivo primeiro."
            )

        # Pegar as primeiras 'limit' linhas
        df_copy = state.global_processed_df.head(limit).copy()

        # Lista de colunas de data conhecidas que podem existir
        possible_date_columns = ['data', 'data_vencimento', 'data_pagamento']

        for col in possible_date_columns:
            if col in df_copy.columns:
                # Verificar se a coluna contém dados antes de tentar converter
                if not df_copy[col].isnull().all():
                    # Tentar converter para string, tratando NaT (Not a Time) explicitamente
                    try:
                        # Primeiro, garantir que é datetime, se possível, tratando erros
                        # pd.to_datetime pode ser redundante se processar_arquivo_csv já fez, mas garante
                        df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                        # Agora formatar, tratando NaT que não podem ser formatados
                        df_copy[col] = df_copy[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else None)
                    except Exception:
                        # Se a conversão falhar, converter para string como fallback
                        df_copy[col] = df_copy[col].astype(str)
                else:
                    # Se a coluna só tiver nulos, converter para None
                    df_copy[col] = None

        # Converter todos os NaNs/Nones para None para compatibilidade JSON
        # Usar replace é mais seguro que fillna para substituir por None
        df_copy = df_copy.replace({pd.NA: None, np.nan: None})

        return JSONResponse(
            content=df_copy.to_dict(orient="records")
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        # Logar o erro detalhado no servidor para depuração
        import traceback
        print(f"Erro detalhado ao visualizar dados: {traceback.format_exc()}")
        # Retornar HTTPException para que o frontend receba um erro 500 claro
        raise HTTPException(
             status_code=500,
             detail=f"Erro interno do servidor ao processar a visualização de dados: {str(e)}"
         )
