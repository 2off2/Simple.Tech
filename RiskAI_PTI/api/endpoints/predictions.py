from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
from typing import List, Optional, Dict, Any
import sys

# Adiciona o diretório raiz ao path para que o Python possa encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar módulos do core
from core import cashflow_predictor, risk_analyzer

# Importar o estado compartilhado
from api.endpoints import state

# Definir o router
router = APIRouter()

# Definir os modelos de request/response
class PredictionParams(BaseModel):
    days_to_predict: int = 30
    # Parâmetros adicionais para o modelo de previsão, se necessário

class PredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

@router.post("/cashflow", response_model=PredictionResponse)
async def predict_cashflow(params: PredictionParams):
    if state.global_processed_df is None:
        raise HTTPException(status_code=400, detail="Dados não carregados. Faça upload de um arquivo CSV primeiro.")

    try:
        # Treinar modelo se ainda não foi treinado com os dados atuais
        if state.global_prediction_model is None:
            dias_para_target_modelo = 7  # Exemplo: modelo treinado para prever 7 dias à frente
            dados_treino = cashflow_predictor.preparar_dados_para_regressao(state.global_processed_df, dias_para_prever=dias_para_target_modelo)
            if dados_treino:
                X_features, y_target = dados_treino
                state.global_prediction_model = cashflow_predictor.treinar_modelo_regressao(X_features, y_target)
            else:
                raise HTTPException(status_code=500, detail="Falha ao preparar dados para treinamento do modelo.")
        
        if state.global_prediction_model is None:
             raise HTTPException(status_code=500, detail="Modelo de previsão não pôde ser treinado.")

        # Gerar previsões
        df_previsoes = cashflow_predictor.gerar_previsao_com_regressao(
            state.global_prediction_model, 
            state.global_processed_df, 
            dias_a_prever=params.days_to_predict,
            dias_para_target=7  # Deve corresponder ao usado no treino
        )
        if df_previsoes is None or df_previsoes.empty:
            raise HTTPException(status_code=500, detail="Falha ao gerar previsões de fluxo de caixa.")

        # Analisar riscos nas previsões
        saldo_inicial_real = state.global_processed_df["saldo"].iloc[-1] if not state.global_processed_df.empty else 0
        alertas = risk_analyzer.identificar_riscos_com_base_em_limiares(df_previsoes, saldo_inicial_real)
        
        return PredictionResponse(
            predictions=df_previsoes.to_dict(orient="records"),
            alerts=alertas
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar previsão: {str(e)}")