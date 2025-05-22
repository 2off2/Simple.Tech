from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar o estado compartilhado
from api.endpoints import state

# Definir o router
router = APIRouter()

# Definir os modelos de request/response
class PredictionParams(BaseModel):
    days_to_predict: int = 30

class PredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

def preparar_dados_para_regressao(df: pd.DataFrame, dias_para_prever: int = 7) -> Optional[tuple]:
    """
    Prepara os dados para treinar um modelo de regressão
    """
    try:
        if df.empty or len(df) < dias_para_prever + 1:
            return None
        
        df_sorted = df.sort_values('data').copy()
        
        # Features: usar média móvel de entradas, saídas e fluxo dos últimos dias
        window = min(7, len(df_sorted))  # Janela móvel de 7 dias ou menos se não houver dados suficientes
        
        df_sorted['entrada_ma'] = df_sorted['entrada'].rolling(window=window, min_periods=1).mean()
        df_sorted['saida_ma'] = df_sorted['saida'].rolling(window=window, min_periods=1).mean()
        df_sorted['fluxo_ma'] = df_sorted['fluxo_diario'].rolling(window=window, min_periods=1).mean()
        df_sorted['saldo_lag'] = df_sorted['saldo'].shift(1).fillna(df_sorted['saldo'].iloc[0])
        
        # Criar features e targets
        features = []
        targets = []
        
        for i in range(len(df_sorted) - dias_para_prever):
            # Features: dados atuais
            feature_row = [
                df_sorted.iloc[i]['entrada_ma'],
                df_sorted.iloc[i]['saida_ma'],
                df_sorted.iloc[i]['fluxo_ma'],
                df_sorted.iloc[i]['saldo_lag']
            ]
            features.append(feature_row)
            
            # Target: saldo após dias_para_prever dias
            targets.append(df_sorted.iloc[i + dias_para_prever]['saldo'])
        
        if len(features) == 0:
            return None
            
        return np.array(features), np.array(targets)
        
    except Exception as e:
        print(f"Erro ao preparar dados para regressão: {e}")
        return None

def treinar_modelo_regressao(X: np.ndarray, y: np.ndarray):
    """
    Treina um modelo de regressão linear
    """
    try:
        modelo = LinearRegression()
        modelo.fit(X, y)
        return modelo
    except Exception as e:
        print(f"Erro ao treinar modelo: {e}")
        return None

def gerar_previsao_com_regressao(modelo, df: pd.DataFrame, dias_a_prever: int = 30, dias_para_target: int = 7) -> Optional[pd.DataFrame]:
    """
    Gera previsões usando o modelo treinado
    """
    try:
        if df.empty:
            return None
        
        df_sorted = df.sort_values('data').copy()
        
        # Preparar features para o último ponto conhecido
        window = min(7, len(df_sorted))
        df_sorted['entrada_ma'] = df_sorted['entrada'].rolling(window=window, min_periods=1).mean()
        df_sorted['saida_ma'] = df_sorted['saida'].rolling(window=window, min_periods=1).mean()
        df_sorted['fluxo_ma'] = df_sorted['fluxo_diario'].rolling(window=window, min_periods=1).mean()
        df_sorted['saldo_lag'] = df_sorted['saldo'].shift(1).fillna(df_sorted['saldo'].iloc[0])
        
        # Última linha conhecida
        ultima_linha = df_sorted.iloc[-1]
        saldo_atual = ultima_linha['saldo']
        data_inicial = ultima_linha['data']
        
        # Gerar previsões
        previsoes = []
        for i in range(1, dias_a_prever + 1):
            data_previsao = data_inicial + timedelta(days=i)
            
            # Features para previsão (usando valores da última linha conhecida)
            features = np.array([[
                ultima_linha['entrada_ma'],
                ultima_linha['saida_ma'],
                ultima_linha['fluxo_ma'],
                saldo_atual
            ]])
            
            # Fazer previsão
            saldo_previsto = modelo.predict(features)[0]
            
            previsoes.append({
                'data': data_previsao,
                'saldo_previsto': saldo_previsto,
                'entrada_estimada': ultima_linha['entrada_ma'],
                'saida_estimada': ultima_linha['saida_ma']
            })
            
            # Atualizar saldo atual para próxima iteração
            saldo_atual = saldo_previsto
        
        return pd.DataFrame(previsoes)
        
    except Exception as e:
        print(f"Erro ao gerar previsão: {e}")
        return None

def identificar_riscos_com_base_em_limiares(df_previsoes: pd.DataFrame, saldo_inicial: float) -> List[Dict[str, Any]]:
    """
    Identifica riscos com base nos limites de saldo
    """
    alertas = []
    
    try:
        for _, row in df_previsoes.iterrows():
            saldo = row['saldo_previsto']
            data = row['data']
            
            if saldo < 0:
                alertas.append({
                    'data': data,
                    'tipo_risco': 'Saldo Negativo',
                    'nivel': 'Alto',
                    'mensagem': f'Saldo previsto negativo: R$ {saldo:,.2f}'
                })
            elif saldo < saldo_inicial * 0.1:  # Menos de 10% do saldo inicial
                alertas.append({
                    'data': data,
                    'tipo_risco': 'Saldo Crítico',
                    'nivel': 'Alto',
                    'mensagem': f'Saldo muito baixo: R$ {saldo:,.2f}'
                })
            elif saldo < saldo_inicial * 0.3:  # Menos de 30% do saldo inicial
                alertas.append({
                    'data': data,
                    'tipo_risco': 'Saldo Baixo',
                    'nivel': 'Médio',
                    'mensagem': f'Saldo abaixo do esperado: R$ {saldo:,.2f}'
                })
    
    except Exception as e:
        print(f"Erro ao identificar riscos: {e}")
    
    return alertas

@router.post("/cashflow", response_model=PredictionResponse)
async def predict_cashflow(params: PredictionParams):
    if state.global_processed_df is None:
        raise HTTPException(status_code=400, detail="Dados não carregados. Faça upload de um arquivo CSV primeiro.")

    try:
        # Treinar modelo se ainda não foi treinado com os dados atuais
        if state.global_prediction_model is None:
            dias_para_target_modelo = 7  # Modelo treinado para prever 7 dias à frente
            dados_treino = preparar_dados_para_regressao(state.global_processed_df, dias_para_prever=dias_para_target_modelo)
            if dados_treino:
                X_features, y_target = dados_treino
                state.global_prediction_model = treinar_modelo_regressao(X_features, y_target)
            else:
                raise HTTPException(status_code=500, detail="Falha ao preparar dados para treinamento do modelo.")
        
        if state.global_prediction_model is None:
             raise HTTPException(status_code=500, detail="Modelo de previsão não pôde ser treinado.")

        # Gerar previsões
        df_previsoes = gerar_previsao_com_regressao(
            state.global_prediction_model, 
            state.global_processed_df, 
            dias_a_prever=params.days_to_predict,
            dias_para_target=7  # Deve corresponder ao usado no treino
        )
        if df_previsoes is None or df_previsoes.empty:
            raise HTTPException(status_code=500, detail="Falha ao gerar previsões de fluxo de caixa.")

        # Converter datas para string para serialização JSON
        df_previsoes['data'] = df_previsoes['data'].dt.strftime('%Y-%m-%d')

        # Analisar riscos nas previsões
        saldo_inicial_real = state.global_processed_df["saldo"].iloc[-1] if not state.global_processed_df.empty else 0
        alertas = identificar_riscos_com_base_em_limiares(df_previsoes, saldo_inicial_real)
        
        # Converter datas nos alertas para string
        for alerta in alertas:
            if isinstance(alerta['data'], pd.Timestamp):
                alerta['data'] = alerta['data'].strftime('%Y-%m-%d')
        
        return PredictionResponse(
            predictions=df_previsoes.to_dict(orient="records"),
            alerts=alertas
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar previsão: {str(e)}")