import streamlit as st
import pandas as pd
import requests
import os

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000"

# --- Configuração da Página Principal do Streamlit ---
st.set_page_config(
    page_title="Simple - Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estado da Sessão ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "processed_data_preview" not in st.session_state:
    st.session_state.processed_data_preview = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "show_full_data" not in st.session_state:
    st.session_state.show_full_data = False

# --- Funções Auxiliares ---
def test_api_connection():
    """Testa a conexão com a API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_file_to_api(uploaded_file_object):
    """Envia o arquivo para o endpoint de upload da API."""
    if uploaded_file_object is not None:
        files = {"file": (uploaded_file_object.name, uploaded_file_object.getvalue(), uploaded_file_object.type)}
        try:
            response = requests.post(f"{API_BASE_URL}/api/data/upload_csv", files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.session_state.api_error = f"Erro de conexão com a API ao fazer upload: {e}"
            return None
    return None

def get_processed_data_from_api(limit=5):
    """Busca uma prévia dos dados processados da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/view_processed?limit={limit}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API ao buscar dados: {e}"
        return None

# --- Verificar Status da API ---
st.title("Simple - Análise Preditiva de Fluxo de Caixa")

api_status = test_api_connection()
if api_status:
    st.success("✅ API conectada e funcionando")
else:
    st.error("❌ API não está respondendo. Verifique se a API está rodando em http://localhost:8000")
    st.info("Para iniciar a API, execute: `uvicorn api.main:app --reload` na pasta do projeto")
    st.stop()

st.markdown("""
Simple é sua ferramenta inteligente para análise preditiva de fluxo de caixa, identificação de riscos financeiros e simulação de cenários de negócios. 
Navegue pelas seções no menu lateral para explorar as funcionalidades.

**Principais Funcionalidades:**
*   **Upload de Dados:** Carregue seus dados financeiros em formato CSV.
*   **Previsão de Fluxo de Caixa:** Obtenha projeções futuras do seu saldo e alertas de risco.
*   **Simulação de Cenários:** Teste o impacto de diferentes variações nas suas finanças.
*   **Dashboard Geral:** Visualize um resumo consolidado das suas análises.

Comece fazendo o upload dos seus dados na página "1. Upload de Dados".
""")



# --- Exibir Status do Upload ---
if st.session_state.uploaded_file_name:
    st.sidebar.info(f"Arquivo ativo: **{st.session_state.uploaded_file_name}**")
    if st.session_state.processed_data_preview is not None:
        with st.sidebar.expander("Prévia dos Dados Processados", expanded=False):
            st.dataframe(st.session_state.processed_data_preview, use_container_width=True)
            if st.button("Ver dados completos", key="toggle_full_data_main"):
                st.session_state.show_full_data = not st.session_state.show_full_data

# --- Exibir dados completos se solicitado ---
if st.session_state.show_full_data and st.session_state.uploaded_file_name:
    st.subheader("Visualização dos Dados Processados Completos")
    with st.spinner("Carregando dados completos..."):
        full_data = get_processed_data_from_api(limit=1000)
        if full_data:
            st.dataframe(pd.DataFrame(full_data))
        else:
            st.error("Não foi possível carregar os dados completos.")
            if st.session_state.api_error:
                st.error(st.session_state.api_error)

# --- Instruções de Uso ---
if not st.session_state.uploaded_file_name:
    st.markdown("---")
    st.subheader("Como começar:")
    st.markdown("""
    1. **Prepare seus dados:** O arquivo CSV deve conter pelo menos as colunas `data` e `descricao`
    2. **Faça o upload:** Use o botão na barra lateral ou vá para a página "1. Upload de Dados"
    3. **Explore as análises:** Após o upload, navegue pelas diferentes páginas do dashboard
    
    **Formato do CSV esperado:**
    ```
    data,descricao,entrada,saida
    2023-01-01,Venda Produto A,1000.00,0.00
    2023-01-02,Pagamento Fornecedor,0.00,500.00
    ...
    ```
    """)

st.markdown("---")
st.caption("Simple - Desenvolvimento de Software com IA - 2024")

# Para executar esta aplicação Streamlit:
# 1. Certifique-se de que a API FastAPI está rodando: uvicorn api.main:app --reload
# 2. Execute: streamlit run dashboard/app.py