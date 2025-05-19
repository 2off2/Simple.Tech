import streamlit as st
import pandas as pd
import requests # Para interagir com a API FastAPI
import os

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000" # Assume que a API FastAPI está rodando localmente na porta 8000

# --- Configuração da Página Principal do Streamlit ---
st.set_page_config(
    page_title="RiskAI - Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
 )

# --- Estado da Sessão (para manter dados entre páginas/interações) ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "processed_data_preview" not in st.session_state:
    st.session_state.processed_data_preview = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "show_full_data" not in st.session_state:
    st.session_state.show_full_data = False # Para controlar a exibição dos dados completos

# --- Funções Auxiliares para Interagir com a API ---
def upload_file_to_api(uploaded_file_object):
    """Envia o arquivo para o endpoint de upload da API."""
    if uploaded_file_object is not None:
        files = {"file": (uploaded_file_object.name, uploaded_file_object.getvalue(), uploaded_file_object.type)}
        try:
            response = requests.post(f"{API_BASE_URL}/data/upload_csv", files=files, timeout=30)
            response.raise_for_status() # Levanta um erro para códigos de status HTTP 4xx/5xx
            return response.json()
        except requests.exceptions.RequestException as e:
            st.session_state.api_error = f"Erro de conexão com a API ao fazer upload: {e}"
            return None
    return None

def get_processed_data_from_api(limit=5):
    """Busca uma prévia dos dados processados da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/data/view_processed?limit={limit}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API ao buscar dados: {e}"
        return None

# --- Página Principal / Boas-vindas (app.py) ---
# Esta será a página inicial se você não usar a estrutura de `pages/` para a primeira página,
# ou pode ser uma página de "Sobre" ou "Home" se você tiver outras páginas em `pages/`.

st.title("Bem-vindo ao RiskAI  финансовый риск-анализатор")
st.markdown("""
RiskAI é sua ferramenta inteligente para análise preditiva de fluxo de caixa, identificação de riscos financeiros e simulação de cenários de negócios. 
Navegue pelas seções no menu lateral para explorar as funcionalidades.

**Principais Funcionalidades:**
*   **Upload de Dados:** Carregue seus dados financeiros em formato CSV.
*   **Previsão de Fluxo de Caixa:** Obtenha projeções futuras do seu saldo e alertas de risco.
*   **Simulação de Cenários:** Teste o impacto de diferentes variações nas suas finanças.
*   **Análise de Clientes:** Identifique riscos relacionados à inadimplência (se aplicável).
*   **Dashboard Geral:** Visualize um resumo consolidado das suas análises.

Comece fazendo o upload dos seus dados na página "1. Upload de Dados".
""")

st.sidebar.image("https://img.icons8.com/plasticine/100/000000/financial-growth-analysis.png", caption="RiskAI v0.1" )
st.sidebar.markdown("--- ")
st.sidebar.header("Navegação Principal")
# O Streamlit criará automaticamente a navegação para os arquivos em `pages/`.
# Este `app.py` serve como a página de entrada ou uma página "Home".

# --- Seção de Upload de Arquivo (Exemplo aqui, mas idealmente em uma página dedicada `01_Upload.py`) ---
# Para demonstração, incluiremos uma pequena seção de upload aqui, mas a estrutura `pages/` é melhor.

st.sidebar.markdown("--- ")
st.sidebar.subheader("Upload Rápido de CSV")

# Usar st.file_uploader na sidebar
with st.sidebar.expander("Carregar arquivo CSV", expanded=False):
    uploaded_file = st.file_uploader(
        "Selecione seu arquivo CSV financeiro", 
        type=["csv"],
        key="main_uploader",
        help="O arquivo deve conter colunas como: data, descricao, entrada, saida. Veja o example.csv para referência."
    )

    if uploaded_file is not None:
        if st.button("Processar Arquivo via API", key="main_process_button"):
            with st.spinner("Enviando e processando arquivo..."):
                st.session_state.api_error = None # Limpar erros anteriores
                api_response = upload_file_to_api(uploaded_file)
                if api_response and api_response.get("message") == "Arquivo CSV carregado e processado com sucesso.":
                    st.session_state.uploaded_file_name = api_response.get("filename")
                    st.sidebar.success(f"Arquivo \'{st.session_state.uploaded_file_name}\' processado!")
                    
                    # Tentar buscar uma prévia dos dados processados
                    preview_data = get_processed_data_from_api(limit=5)
                    if preview_data:
                        st.session_state.processed_data_preview = pd.DataFrame(preview_data)
                    else:
                        st.session_state.processed_data_preview = None
                        st.sidebar.warning("Não foi possível buscar a prévia dos dados processados.")
                elif api_response and api_response.get("error"):
                    st.sidebar.error(f"Erro da API: {api_response.get('error')}")
                    st.session_state.uploaded_file_name = None
                    st.session_state.processed_data_preview = None
                else:
                    st.sidebar.error("Falha ao processar o arquivo via API. Verifique os logs da API.")
                    st.session_state.uploaded_file_name = None
                    st.session_state.processed_data_preview = None
            
            if st.session_state.api_error:
                st.sidebar.error(st.session_state.api_error)

if st.session_state.uploaded_file_name:
    st.sidebar.info(f"Arquivo ativo: **{st.session_state.uploaded_file_name}**")
    if st.session_state.processed_data_preview is not None:
        with st.sidebar.expander("Prévia dos Dados Processados", expanded=False):
            st.dataframe(st.session_state.processed_data_preview, use_container_width=True)
            if st.button("Ver dados completos", key="toggle_full_data_main"):
                 st.session_state.show_full_data = not st.session_state.show_full_data

# Exibir dados completos se solicitado
if st.session_state.show_full_data and st.session_state.uploaded_file_name:
    st.subheader("Visualização dos Dados Processados Completos")
    with st.spinner("Carregando dados completos..."):
        full_data = get_processed_data_from_api(limit=1000) # Ou um limite maior
        if full_data:
            st.dataframe(pd.DataFrame(full_data))
        else:
            st.error("Não foi possível carregar os dados completos.")
            if st.session_state.api_error:
                st.error(st.session_state.api_error)

st.markdown("--- ")
st.caption("RiskAI PTI - Desenvolvimento de Software com IA - 2024")

# Para executar esta aplicação Streamlit:
# 1. Certifique-se de que a API FastAPI (api/main.py) está rodando.
# 2. No terminal, na raiz do projeto, execute: streamlit run dashboard/app.py

