# dashboard/pages/04_Dashboard_Geral.py

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000"  # Assume que a API FastAPI está rodando localmente na porta 8000

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard Geral - RiskAI",
    page_icon="🏠",
    layout="wide"
 )

# --- Título e Descrição ---
st.title("Dashboard Geral Consolidado")
st.markdown("""
Este dashboard apresenta um resumo das principais métricas e visualizações geradas 
pelas análises de previsão, risco e simulação.
""")

# --- Estado da Sessão ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "prediction_data" not in st.session_state:
    st.session_state.prediction_data = None # Armazenado pela página de Previsão
if "alert_data" not in st.session_state:
    st.session_state.alert_data = None # Armazenado pela página de Previsão
if "simulation_summary" not in st.session_state:
    st.session_state.simulation_summary = None # Armazenado pela página de Simulação
if "customer_analysis_report" not in st.session_state:
    st.session_state.customer_analysis_report = None # Para análise de inadimplência

# --- Funções Auxiliares (reutilizadas ou específicas) ---
# (Poderiam ser movidas para um módulo de utils do dashboard se ficarem muito repetitivas)

def fetch_customer_analysis_from_api():
    """Busca o relatório de análise de inadimplência da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/analyze/customer_delinquency", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        try:
            error_detail = http_err.response.json( ).get("detail", str(http_err ))
        except Exception:
            error_detail = str(http_err )
        st.session_state.api_error = f"Erro da API (Análise de Clientes): {error_detail}"
        return None
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API (Análise de Clientes): {e}"
        return None
    return None

# --- Layout Principal ---

# Verificar se os dados foram carregados
if st.session_state.uploaded_file_name is None:
    st.warning("⚠️ Por favor, carregue um arquivo CSV na página **1. Upload de Dados** primeiro para popular o dashboard.")
    st.image("https://img.icons8.com/dusk/128/000000/warning-shield.png", width=128 )
    st.stop()

st.success(f"Exibindo dashboard para o arquivo: **{st.session_state.uploaded_file_name}**")
st.markdown("---")

# --- Botão para Atualizar Dados do Dashboard (se necessário) ---
if st.button("Atualizar Dados do Dashboard", key="refresh_dashboard_button"):
    with st.spinner("Buscando dados atualizados da API..."):
        st.session_state.api_error = None
        # Forçar a busca de dados que podem ter sido gerados em outras páginas
        # Exemplo: se a previsão e simulação fossem executadas aqui também
        # Para este exemplo, vamos assumir que os dados já estão no session_state das outras páginas
        # ou buscar a análise de clientes que pode não ter sido feita ainda.
        
        # Tentar buscar análise de clientes se ainda não foi feita
        if st.session_state.customer_analysis_report is None:
            customer_report_data = fetch_customer_analysis_from_api()
            if customer_report_data and "report" in customer_report_data:
                st.session_state.customer_analysis_report = customer_report_data["report"]
            elif st.session_state.api_error:
                 st.toast(f"Erro ao buscar análise de clientes: {st.session_state.api_error}", icon="🔥")

        st.toast("Dados do dashboard atualizados (ou tentativa de atualização).", icon="🔄")

if st.session_state.api_error:
    st.error(f"Erro da API: {st.session_state.api_error}")

# --- Seção de Resumo da Previsão e Alertas ---
st.header("Resumo da Previsão de Fluxo de Caixa e Alertas")
if st.session_state.prediction_data is not None and st.session_state.alert_data is not None:
    df_pred = st.session_state.prediction_data
    alerts = st.session_state.alert_data
    
    if not df_pred.empty and "data" in df_pred.columns and "saldo_previsto" in df_pred.columns:
        df_pred["data"] = pd.to_datetime(df_pred["data"])
        
        col_pred1, col_pred2 = st.columns(2)
        with col_pred1:
            st.subheader("Projeção de Saldo")
            fig_pred_dash = go.Figure()
            fig_pred_dash.add_trace(go.Scatter(
                x=df_pred["data"],
                y=df_pred["saldo_previsto"],
                mode=	"lines",
                name=	"Saldo Previsto",
                line=dict(color=	"green", width=2)
            ))
            fig_pred_dash.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_pred_dash, use_container_width=True)
        
        with col_pred2:
            st.subheader("Principais Alertas de Risco")
            if alerts:
                df_alerts = pd.DataFrame(alerts)
                df_alerts_summary = df_alerts.sort_values(by=["nivel", "data"], ascending=[False, True]).head(5)
                for index, row in df_alerts_summary.iterrows():
                    data_alerta = pd.to_datetime(row["data"]).strftime("%d/%m/%Y")
                    icon = "🚨" if row["nivel"] == "Alto" else ("⚠️" if row["nivel"] == "Médio" else "ℹ️")
                    st.markdown(f"{icon} **{row['nivel']} em {data_alerta}**: {row['tipo_risco']}")
                if len(alerts) > 5:
                    st.caption(f"Mostrando os 5 principais alertas de {len(alerts)} no total. Veja mais na página de Previsão.")
            else:
                st.info("✅ Nenhum alerta de risco identificado na última previsão.")
    else:
        st.info("Dados de previsão não disponíveis ou incompletos. Gere uma previsão na página **2. Previsão**.")
else:
    st.info("Execute a previsão na página **2. Previsão** para ver os resultados aqui.")

st.markdown("---")

# --- Seção de Resumo da Simulação de Cenários ---
st.header("Resumo da Simulação de Cenários")
if st.session_state.simulation_summary is not None:
    summary = st.session_state.simulation_summary
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        st.metric(
            label="Probabilidade de Saldo Negativo (Final do Período)", 
            value=f"{summary.get(	'prob_saldo_negativo_final	', 0)*100:.2f}%"
        )
        st.metric(
            label="Valor Mediano Esperado (Final do Período)", 
            value=f"R$ {summary.get(	'valor_mediano_esperado	', 0):,.2f}"
        )
    with col_sim2:
        st.metric(
            label="Probabilidade de Saldo Negativo (Qualquer Momento)", 
            value=f"{summary.get(	'prob_saldo_negativo_qualquer_momento	', 0)*100:.2f}%"
        )
        st.metric(
            label="Valor Mínimo Esperado (P5, Final do Período)", 
            value=f"R$ {summary.get(	'valor_minimo_esperado	', 0):,.2f}"
        )
    
    # Poderia adicionar um gráfico simplificado da simulação aqui se os dados fossem passados
    # st.info("Gráfico da simulação disponível na página **3. Simulação**.")
else:
    st.info("Execute uma simulação na página **3. Simulação** para ver os resultados aqui.")

st.markdown("---")

# --- Seção de Análise de Inadimplência (se aplicável) ---
st.header("Resumo da Análise de Inadimplência de Clientes")
if st.session_state.customer_analysis_report is None:
    # Tentar buscar agora se não foi feito no refresh
    if st.button("Buscar Análise de Inadimplência", key="fetch_delinquency"):
        with st.spinner("Buscando análise de inadimplência..."):
            customer_report_data = fetch_customer_analysis_from_api()
            if customer_report_data and "report" in customer_report_data:
                st.session_state.customer_analysis_report = customer_report_data["report"]
                st.rerun() # Rerun para exibir os dados
            elif st.session_state.api_error:
                 st.error(f"Erro ao buscar análise de clientes: {st.session_state.api_error}")
            else:
                st.warning("Não foi possível buscar a análise de inadimplência ou não há dados para ela.")

if st.session_state.customer_analysis_report is not None:
    report = st.session_state.customer_analysis_report
    
    if report.get("total_clientes_com_faturas_em_atraso", 0) > 0:
        col_cust1, col_cust2 = st.columns(2)
        with col_cust1:
            st.metric("Clientes com Faturas em Atraso", report.get("total_clientes_com_faturas_em_atraso", 0))
            st.metric("Valor Total em Atraso", f"R$ {report.get(	'valor_total_em_atraso	', 0):,.2f}")
        
        with col_cust2:
            st.subheader("Distribuição de Risco de Inadimplência")
            dist_risco = report.get("distribuicao_risco", {})
            if dist_risco:
                df_risco = pd.DataFrame(list(dist_risco.items()), columns=["Nível de Risco", "Número de Clientes"])
                fig_risco = go.Figure(data=[go.Pie(labels=df_risco["Nível de Risco"], values=df_risco["Número de Clientes"], hole=.3)])
                fig_risco.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20), legend_orientation="h")
                st.plotly_chart(fig_risco, use_container_width=True)
            else:
                st.info("Distribuição de risco não disponível.")
        
        st.subheader("Top Clientes em Alto Risco (em atraso)")
        top_alto_risco = report.get("top_5_clientes_alto_risco", [])
        if top_alto_risco:
            df_top_risco = pd.DataFrame(top_alto_risco)
            st.dataframe(df_top_risco[["id_cliente", "total_devido_atraso", "max_dias_atraso"]].style.format({"total_devido_atraso": "R${:,.2f}"}), use_container_width=True)
        else:
            st.info("Nenhum cliente classificado como alto risco atualmente em atraso.")
    else:
        st.info("✅ Nenhuma fatura em atraso identificada ou dados insuficientes para análise de inadimplência.")
else:
    st.info("Análise de inadimplência não disponível. Verifique se os dados carregados contêm as colunas necessárias (id_cliente, data_vencimento, valor_fatura) e tente buscar a análise.")

# --- Rodapé ---
st.markdown("---")
st.caption(f"RiskAI - Dashboard Geral • Última atualização: {datetime.now().strftime(	'%Y-%m-%d %H:%M	')}")

