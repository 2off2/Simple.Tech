import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime

# URL base da API (ajuste se necessário)
API_BASE_URL = "http://localhost:8000"  # Assume que a API FastAPI está rodando localmente na porta 8000

# --- Configuração da Página ---
st.set_page_config(
    page_title="Upload de Dados - RiskAI",
    page_icon="📤",
    layout="wide"
 )

# --- Título e Descrição ---
st.title("Upload de Dados Financeiros")
st.markdown("""
Esta página permite carregar seus dados financeiros para análise. 
O arquivo deve estar no formato CSV e conter as colunas necessárias para o processamento.
""")

# --- Funções Auxiliares ---
def upload_file_to_api(uploaded_file_object):
    """Envia o arquivo para o endpoint de upload da API."""
    if uploaded_file_object is not None:
        files = {"file": (uploaded_file_object.name, uploaded_file_object.getvalue(), uploaded_file_object.type)}
        try:
            response = requests.post(f"{API_BASE_URL}/data/upload_csv", files=files, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.session_state.api_error = f"Erro de conexão com a API: {e}"
            return None
    return None

def get_processed_data_from_api(limit=10):
    """Busca os dados processados da API."""
    try:
        response = requests.get(f"{API_BASE_URL}/data/view_processed?limit={limit}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.session_state.api_error = f"Erro de conexão com a API: {e}"
        return None

def create_example_csv():
    """Cria um arquivo CSV de exemplo para download."""
    data = {
        "data": [
            "2023-01-01", "2023-01-05", "2023-01-10", "2023-01-15", "2023-01-20",
            "2023-01-25", "2023-01-31", "2023-02-05", "2023-02-10", "2023-02-15"
        ],
        "descricao": [
            "Venda Produto A", "Pagamento Fornecedor", "Venda Produto B", 
            "Despesa Operacional", "Venda Produto C", "Pagamento Funcionários",
            "Venda Produto A", "Pagamento Aluguel", "Venda Produto B", "Despesa Marketing"
        ],
        "entrada": [1000.00, 0.00, 1500.00, 0.00, 800.00, 0.00, 1200.00, 0.00, 1800.00, 0.00],
        "saida": [0.00, 500.00, 0.00, 300.00, 0.00, 1200.00, 0.00, 800.00, 0.00, 400.00],
        "id_cliente": ["C001", "F001", "C002", "ADM", "C003", "RH", "C001", "ADM", "C002", "MKT"],
        "data_vencimento": [
            "2023-01-15", "2023-01-05", "2023-01-25", "2023-01-15", "2023-02-05", 
            "2023-01-25", "2023-02-15", "2023-02-05", "2023-02-25", "2023-02-15"
        ],
        "data_pagamento": [
            "2023-01-10", "2023-01-05", "2023-01-20", "2023-01-15", "", 
            "2023-01-25", "", "2023-02-05", "", "2023-02-15"
        ],
        "valor_fatura": [1000.00, 500.00, 1500.00, 300.00, 800.00, 1200.00, 1200.00, 800.00, 1800.00, 400.00]
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

# --- Estado da Sessão ---
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None
if "processed_data_preview" not in st.session_state:
    st.session_state.processed_data_preview = None
if "api_error" not in st.session_state:
    st.session_state.api_error = None
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False

# --- Layout Principal ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Carregar Arquivo CSV")
    
    # Seção de Upload
    uploaded_file = st.file_uploader(
        "Selecione seu arquivo CSV financeiro", 
        type=["csv"],
        help="O arquivo deve conter colunas como: data, descricao, entrada, saida."
    )
    
    if uploaded_file is not None:
        st.success(f"Arquivo '{uploaded_file.name}' selecionado!")
        
        # Exibir prévia do arquivo carregado
        try:
            df_preview = pd.read_csv(uploaded_file)
            st.subheader("Prévia do Arquivo Carregado")
            st.dataframe(df_preview.head(5), use_container_width=True)
            
            # Verificar colunas obrigatórias
            required_cols = ["data", "descricao"]
            missing_cols = [col for col in required_cols if col not in df_preview.columns]
            
            if missing_cols:
                st.warning(f"⚠️ Colunas obrigatórias faltando: {', '.join(missing_cols)}")
            else:
                st.info("✅ Todas as colunas obrigatórias estão presentes.")
                
                # Botão para processar o arquivo
                if st.button("Processar Arquivo via API", key="process_button"):
                    with st.spinner("Enviando e processando arquivo..."):
                        st.session_state.api_error = None  # Limpar erros anteriores
                        api_response = upload_file_to_api(uploaded_file)
                        
                        if api_response and "message" in api_response and "Sucesso" in api_response["message"]:
                            st.session_state.uploaded_file_name = api_response.get("filename")
                            st.session_state.upload_success = True
                            
                            # Buscar dados processados
                            preview_data = get_processed_data_from_api()
                            if preview_data:
                                st.session_state.processed_data_preview = pd.DataFrame(preview_data)
                            else:
                                st.session_state.processed_data_preview = None
                                st.warning("Não foi possível buscar a prévia dos dados processados.")
                        elif api_response and "error" in api_response:
                            st.error(f"Erro da API: {api_response['error']}")
                            st.session_state.upload_success = False
                        else:
                            st.error("Falha ao processar o arquivo via API. Verifique os logs da API.")
                            st.session_state.upload_success = False
                    
                    if st.session_state.api_error:
                        st.error(st.session_state.api_error)
        
        except Exception as e:
            st.error(f"Erro ao ler o arquivo CSV: {e}")

with col2:
    st.header("Informações")
    
    # Seção de Exemplo
    st.subheader("Arquivo de Exemplo")
    st.markdown("""
    Se você não tem um arquivo CSV pronto, pode baixar este exemplo:
    """)
    
    example_csv = create_example_csv()
    st.download_button(
        label="⬇️ Baixar CSV de Exemplo",
        data=example_csv,
        file_name="example_financial_data.csv",
        mime="text/csv"
    )
    
    # Formato Esperado
    st.subheader("Formato Esperado")
    st.markdown("""
    O arquivo CSV deve conter as seguintes colunas:
    
    **Obrigatórias:**
    - `data`: Data da transação (YYYY-MM-DD)
    - `descricao`: Descrição da transação
    
    **Recomendadas:**
    - `entrada`: Valores recebidos (numérico)
    - `saida`: Valores pagos (numérico)
    
    **Opcionais (para análise de inadimplência):**
    - `id_cliente`: Identificador do cliente
    - `data_vencimento`: Data de vencimento da fatura
    - `data_pagamento`: Data em que o pagamento foi realizado
    - `valor_fatura`: Valor da fatura
    """)

# --- Exibir Dados Processados (se disponíveis) ---
if st.session_state.upload_success and st.session_state.processed_data_preview is not None:
    st.markdown("---")
    st.header("Dados Processados")
    st.success(f"✅ Arquivo '{st.session_state.uploaded_file_name}' processado com sucesso!")
    
    st.dataframe(st.session_state.processed_data_preview, use_container_width=True)
    
    # Botões para navegar para outras páginas
    st.markdown("### Próximos Passos")
    col_next1, col_next2 = st.columns(2)
    
    with col_next1:
        st.info("Agora você pode gerar previsões de fluxo de caixa com base nos dados carregados.")
        if st.button("Ir para Previsão de Fluxo de Caixa", key="goto_prediction"):
            # No Streamlit, não podemos navegar programaticamente entre páginas,
            # mas podemos sugerir ao usuário que clique na página correspondente no menu lateral
            st.markdown("Por favor, clique em **2. Previsão** no menu lateral.")
    
    with col_next2:
        st.info("Ou simular diferentes cenários financeiros para análise de risco.")
        if st.button("Ir para Simulação de Cenários", key="goto_simulation"):
            st.markdown("Por favor, clique em **3. Simulação** no menu lateral.")

# --- Rodapé ---
st.markdown("---")
st.caption(f"RiskAI - Upload de Dados • Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
