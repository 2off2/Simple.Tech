# dashboard/pages/02_Previsao.py

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000"  # Assume que a API FastAPI está rodando localmente na porta 8000

# --- Configuração da Página ---
st.set_page_config(
    page_title="Previsão de Fluxo de Caixa - RiskAI",
    page_icon="📈",
    layout="wide"
 )

# --- Título e Descrição ---
st.title("Previsão de Fluxo de Caixa e Alertas de Risco")
st.markdown("""
Nesta página, você pode gerar previsões para o seu fluxo de caixa com base nos dados carregados 
e visualizar alertas de risco identificados.
""")

# --- Estado da Sessão (para verificar se os dados foram carregados) ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "prediction_data" not in st.session_state:
    st.session_state.prediction_data = None
if "alert_data" not in st.session_state:
    st.session_state.alert_data = None

# --- Funções Auxiliares para Interagir com a API ---
def get_cashflow_prediction_from_api(days_to_predict: int):
    """Busca a previsão de fluxo de caixa e alertas da API."""
    try:
        params = {"days_to_predict": days_to_predict}
        response = requests.post(f"{API_BASE_URL}/predict/cashflow", json=params, timeout=60) # Timeout maior para previsão
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        try:
            error_detail = http_err.response.json( ).get("detail", str(http_err ))
        except Exception:
            error_detail = str(http_err )
        st.session_state.api_error = f"Erro da API ao gerar previsão: {error_detail}"
        return None
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API ao gerar previsão: {e}"
        return None
    except Exception as e:
        st.session_state.api_error = f"Erro inesperado ao processar previsão: {e}"
        return None

# --- Layout Principal ---

# Verificar se os dados foram carregados
if st.session_state.uploaded_file_name is None:
    st.warning("⚠️ Por favor, carregue um arquivo CSV na página **1. Upload de Dados** primeiro.")
    st.image("https://img.icons8.com/dusk/128/000000/warning-shield.png", width=128 )
    st.stop() # Interrompe a execução da página se os dados não foram carregados

st.success(f"Arquivo ativo para análise: **{st.session_state.uploaded_file_name}**")
st.markdown("---")

# --- Seção de Parâmetros da Previsão ---
st.header("Parâmetros da Previsão")

days_to_predict_input = st.number_input(
    "Número de dias para prever no futuro:", 
    min_value=7, 
    max_value=365, 
    value=30, 
    step=1,
    help="Defina quantos dias à frente você deseja que a previsão seja gerada (mínimo 7, máximo 365)."
)

if st.button("Gerar Previsão e Analisar Riscos", key="generate_prediction_button"):
    with st.spinner("Gerando previsão e analisando riscos... Isso pode levar alguns instantes."):
        st.session_state.api_error = None # Limpar erros anteriores
        st.session_state.prediction_data = None
        st.session_state.alert_data = None
        
        api_response = get_cashflow_prediction_from_api(days_to_predict_input)
        
        if api_response:
            if "predictions" in api_response and "alerts" in api_response:
                st.session_state.prediction_data = pd.DataFrame(api_response["predictions"])
                st.session_state.alert_data = api_response["alerts"]
                st.success("Previsão e análise de riscos concluídas!")
            else:
                error_msg = api_response.get("detail", "Resposta inesperada da API.")
                st.error(f"Erro ao obter dados da API: {error_msg}")
                st.session_state.api_error = f"Erro da API: {error_msg}"
        else:
            if not st.session_state.api_error: # Se nenhum erro específico foi definido pela função da API
                st.error("Falha ao obter resposta da API para previsão.")

    if st.session_state.api_error:
        st.error(st.session_state.api_error)

# --- Exibir Resultados da Previsão e Alertas ---
if st.session_state.prediction_data is not None:
    st.markdown("---")
    st.header("Resultados da Previsão de Fluxo de Caixa")
    
    df_pred = st.session_state.prediction_data
    
    if not df_pred.empty and "data" in df_pred.columns and "saldo_previsto" in df_pred.columns:
        df_pred["data"] = pd.to_datetime(df_pred["data"])
        
        # Gráfico de Previsão de Saldo
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_pred["data"],
            y=df_pred["saldo_previsto"],
            mode=	"lines+markers",
            name=	"Saldo Previsto",
            line=dict(color=	"royalblue", width=2),
            marker=dict(size=5)
        ))
        
        fig.update_layout(
            title="Previsão do Saldo de Caixa",
            xaxis_title="Data",
            yaxis_title="Saldo Estimado (R$)",
            hovermode="x unified",
            legend_title_text="Legenda"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de Previsões
        with st.expander("Ver tabela de previsões detalhadas"):
            st.dataframe(df_pred.style.format({"saldo_previsto": "R${:,.2f}"}), use_container_width=True)
    else:
        st.warning("Os dados de previsão recebidos não contêm as colunas esperadas ('data', 'saldo_previsto').")

if st.session_state.alert_data is not None:
    st.markdown("---")
    st.header("Alertas de Risco Identificados")
    
    alerts = st.session_state.alert_data
    if alerts:
        df_alerts = pd.DataFrame(alerts)
        df_alerts = df_alerts.sort_values(by=["data", "nivel"], ascending=[True, False])
        
        for index, row in df_alerts.iterrows():
            data_alerta = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
            if row["nivel"] == "Alto":
                st.error(f"🚨 **Risco Alto em {data_alerta}**: {row['tipo_risco']} - {row['mensagem']}")
            elif row["nivel"] == "Médio":
                st.warning(f"⚠️ **Risco Médio em {data_alerta}**: {row['tipo_risco']} - {row['mensagem']}")
            else:
                st.info(f"ℹ️ **Risco Baixo em {data_alerta}**: {row['tipo_risco']} - {row['mensagem']}")
        
        with st.expander("Ver tabela de alertas detalhados"):
            st.dataframe(df_alerts, use_container_width=True)
    else:
        st.success("✅ Nenhum alerta de risco identificado com base nos parâmetros atuais.")

# --- Rodapé ---
st.markdown("---")
st.caption(f"RiskAI - Previsão de Fluxo de Caixa • Última atualização: {datetime.now().strftime(	'%Y-%m-%d %H:%M	')}")

