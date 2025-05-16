# dashboard/pages/03_Simulacao.py

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000"  # Assume que a API FastAPI está rodando localmente na porta 8000

# --- Configuração da Página ---
st.set_page_config(
    page_title="Simulação de Cenários - RiskAI",
    page_icon="🎲",
    layout="wide"
 )

# --- Título e Descrição ---
st.title("Simulação de Cenários Financeiros")
st.markdown("""
Utilize esta página para executar simulações de Monte Carlo e analisar o impacto de diferentes 
variações nas suas projeções financeiras.
""")

# --- Estado da Sessão ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "simulation_summary" not in st.session_state:
    st.session_state.simulation_summary = None
if "simulation_plot_data" not in st.session_state:
    st.session_state.simulation_plot_data = None # Para armazenar os dados do gráfico de simulação

# --- Funções Auxiliares para Interagir com a API ---
def run_scenario_simulation_on_api(params: dict):
    """Envia os parâmetros e solicita a execução da simulação de cenários na API."""
    try:
        response = requests.post(f"{API_BASE_URL}/simulate/scenarios", json=params, timeout=120) # Timeout maior para simulação
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        try:
            error_detail = http_err.response.json( ).get("detail", str(http_err ))
        except Exception:
            error_detail = str(http_err )
        st.session_state.api_error = f"Erro da API ao executar simulação: {error_detail}"
        return None
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API ao executar simulação: {e}"
        return None
    except Exception as e:
        st.session_state.api_error = f"Erro inesperado ao processar simulação: {e}"
        return None

# --- Layout Principal ---

# Verificar se os dados foram carregados
if st.session_state.uploaded_file_name is None:
    st.warning("⚠️ Por favor, carregue um arquivo CSV na página **1. Upload de Dados** primeiro.")
    st.image("https://img.icons8.com/dusk/128/000000/warning-shield.png", width=128 )
    st.stop()

st.success(f"Arquivo ativo para análise: **{st.session_state.uploaded_file_name}**")
st.markdown("---")

# --- Seção de Parâmetros da Simulação ---
st.header("Parâmetros da Simulação de Monte Carlo")

with st.form(key="simulation_params_form"):
    st.subheader("Configurações Gerais")
    num_simulacoes_input = st.number_input(
        "Número de Simulações:", 
        min_value=100, 
        max_value=10000, 
        value=1000, 
        step=100,
        help="Quantidade de cenários aleatórios a serem gerados (mais simulações = mais preciso, porém mais lento)."
    )
    dias_simulacao_input = st.number_input(
        "Dias para Simular no Futuro:", 
        min_value=7, 
        max_value=365, 
        value=30, 
        step=1,
        help="Período da simulação em dias."
    )
    saldo_inicial_sim_input = st.number_input(
        "Saldo Inicial para Simulação (Opcional):",
        value=None, # Deixar como None para usar o último saldo histórico da API
        step=100.0,
        format="%.2f",
        help="Se não informado, a API usará o último saldo dos dados carregados."
    )

    st.subheader("Variações Percentuais Esperadas")
    col_var1, col_var2 = st.columns(2)
    with col_var1:
        variacao_entrada_input = st.slider(
            "Variação na Média de Entradas (%):", 
            min_value=0.0, 
            max_value=100.0, 
            value=10.0, 
            step=1.0,
            format="%.1f%%",
            help="Define a faixa de variação (para mais e para menos) em torno da média histórica de entradas."
        ) / 100.0 # Converter para decimal
    with col_var2:
        variacao_saida_input = st.slider(
            "Variação na Média de Saídas (%):", 
            min_value=0.0, 
            max_value=100.0, 
            value=10.0, 
            step=1.0,
            format="%.1f%%",
            help="Define a faixa de variação (para mais e para menos) em torno da média histórica de saídas."
        ) / 100.0 # Converter para decimal

    submit_button = st.form_submit_button(label="Executar Simulação de Cenários")

if submit_button:
    simulation_params = {
        "variacao_entrada": variacao_entrada_input,
        "variacao_saida": variacao_saida_input,
        "dias_simulacao": dias_simulacao_input,
        "num_simulacoes": num_simulacoes_input,
        "saldo_inicial_simulacao": saldo_inicial_sim_input if saldo_inicial_sim_input is not None else None
    }
    
    with st.spinner("Executando simulação de cenários... Isso pode levar alguns minutos."):
        st.session_state.api_error = None # Limpar erros anteriores
        st.session_state.simulation_summary = None
        st.session_state.simulation_plot_data = None
        
        api_response = run_scenario_simulation_on_api(simulation_params)
        
        if api_response and "results_summary" in api_response:
            st.session_state.simulation_summary = api_response["results_summary"]
            # A API de exemplo não retorna os dados completos da simulação para o gráfico diretamente.
            # Em um cenário real, a API poderia retornar os dados agregados para o gráfico (percentis, média, etc.)
            # ou o dashboard teria que buscar os dados históricos e simular localmente (menos ideal para Monte Carlo pesado).
            # Para este exemplo, vamos assumir que a API retorna o necessário ou que o gráfico é construído a partir do sumário.
            # Se a API retornasse os dados para o gráfico (ex: df_resultados do core.scenario_simulator):
            # st.session_state.simulation_plot_data = pd.DataFrame(api_response.get("plot_data")) 
            st.success("Simulação de cenários concluída!")
        else:
            if not st.session_state.api_error:
                st.error("Falha ao obter resposta da API para simulação.")

    if st.session_state.api_error:
        st.error(st.session_state.api_error)

# --- Exibir Resultados da Simulação ---
if st.session_state.simulation_summary is not None:
    st.markdown("---")
    st.header("Resultados da Simulação de Cenários")
    
    summary = st.session_state.simulation_summary
    
    st.subheader("Análise de Probabilidades e Valores Esperados")
    col_res1, col_res2, col_res3 = st.columns(3)
    with col_res1:
        st.metric(
            label="Prob. Saldo Negativo (Final)", 
            value=f"{summary.get(	"prob_saldo_negativo_final	", 0)*100:.2f}%"
        )
        st.metric(
            label="Valor Mínimo Esperado (P5)", 
            value=f"R$ {summary.get(	"valor_minimo_esperado	", 0):,.2f}"
        )
    with col_res2:
        st.metric(
            label="Prob. Saldo Negativo (Qualquer Momento)", 
            value=f"{summary.get(	"prob_saldo_negativo_qualquer_momento	", 0)*100:.2f}%"
        )
        st.metric(
            label="Valor Mediano Esperado (P50)", 
            value=f"R$ {summary.get(	"valor_mediano_esperado	", 0):,.2f}"
        )
    with col_res3:
        dia_maior_prob_neg = pd.to_datetime(summary.get("dia_maior_prob_negativo")).strftime("%d/%m/%Y") if summary.get("dia_maior_prob_negativo") else "N/A"
        st.metric(
            label=f"Dia Maior Prob. Saldo Negativo ({dia_maior_prob_neg})", 
            value=f"{summary.get(	"valor_maior_prob_negativo	", 0)*100:.2f}%"
        )
        st.metric(
            label="Valor Máximo Esperado (P95)", 
            value=f"R$ {summary.get(	"valor_maximo_esperado	", 0):,.2f}"
        )
    
    # Gráfico da Simulação (se os dados estiverem disponíveis)
    # Como a API de exemplo não retorna os dados do gráfico, esta seção seria mais complexa.
    # Idealmente, a API retornaria os dados agregados (percentis, média) ao longo do tempo.
    # Exemplo de como seria se tivéssemos `st.session_state.simulation_plot_data` (um DataFrame com colunas como data, percentil_5, percentil_50, percentil_95, media)
    if st.session_state.simulation_plot_data is not None and not st.session_state.simulation_plot_data.empty:
        st.subheader("Distribuição dos Saldos Projetados ao Longo do Tempo")
        df_plot = st.session_state.simulation_plot_data
        df_plot["data"] = pd.to_datetime(df_plot["data"]) # Certificar que a coluna de data é datetime

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["percentil_5"], fill=None, mode=	"lines", line_color=	"lightgrey", name="Percentil 5"))
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["percentil_95"], fill=	"tonexty", mode=	"lines", line_color=	"lightgrey", name="Percentil 95 (Intervalo 90%)"))
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["percentil_25"], fill=None, mode=	"lines", line_color=	"lightblue", name="Percentil 25"))
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["percentil_75"], fill=	"tonexty", mode=	"lines", line_color=	"lightblue", name="Percentil 75 (Intervalo 50%)"))
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["percentil_50"], mode=	"lines", line=dict(color=	"blue", width=2), name="Mediana (Percentil 50)"))
        fig_sim.add_trace(go.Scatter(x=df_plot["data"], y=df_plot["media"], mode=	"lines", line=dict(color=	"red", dash=	"dash"), name="Média"))
        
        fig_sim.update_layout(
            title="Simulação de Monte Carlo - Projeção de Saldo de Caixa",
            xaxis_title="Data",
            yaxis_title="Saldo Estimado (R$)",
            hovermode="x unified"
        )
        st.plotly_chart(fig_sim, use_container_width=True)
    else:
        st.info("Visualização gráfica da simulação não disponível neste exemplo (requer que a API retorne dados detalhados dos percentis ao longo do tempo).")

    with st.expander("Ver sumário completo da simulação (JSON)"):
        st.json(summary)

# --- Rodapé ---
st.markdown("---")
st.caption(f"RiskAI - Simulação de Cenários • Última atualização: {datetime.now().strftime(	"%Y-%m-%d %H:%M	")}")

