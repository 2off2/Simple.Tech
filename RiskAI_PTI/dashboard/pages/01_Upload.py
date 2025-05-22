import streamlit as st
import pandas as pd
import requests
import io

# Configuração da página
st.set_page_config(
    page_title="Upload de Dados - RiskAI",
    page_icon="📤",
    layout="wide"
)

# URL base da API
API_BASE_URL = "http://localhost:8000"

st.title("📤 Upload de Dados Financeiros")

st.markdown("""
Esta página permite que você carregue seus dados financeiros em formato CSV para análise.

**Formato esperado do arquivo CSV:**
- `data`: Data da transação (formato: YYYY-MM-DD)
- `descricao`: Descrição da transação
- `entrada`: Valor de entrada (opcional, será 0 se não informado)
- `saida`: Valor de saída (opcional, será 0 se não informado)
""")

# Verificar status da API
def test_api_connection():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# Status da API
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Status da Conexão")
with col2:
    if test_api_connection():
        st.success("✅ API Online")
    else:
        st.error("❌ API Offline")
        st.stop()

# Área de upload
st.subheader("Carregar Arquivo CSV")

uploaded_file = st.file_uploader(
    "Selecione seu arquivo CSV",
    type=["csv"],
    help="O arquivo deve estar em formato CSV com as colunas mencionadas acima"
)

if uploaded_file is not None:
    # Mostrar preview do arquivo
    try:
        # Ler o arquivo para preview
        df_preview = pd.read_csv(uploaded_file)
        
        st.subheader("Preview dos Dados")
        st.dataframe(df_preview.head(10))
        
        st.subheader("Informações do Arquivo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Linhas", len(df_preview))
        with col2:
            st.metric("Total de Colunas", len(df_preview.columns))
        with col3:
            st.metric("Tamanho", f"{uploaded_file.size / 1024:.1f} KB")
        
        # Mostrar colunas disponíveis
        st.subheader("Colunas Encontradas")
        cols_info = []
        for col in df_preview.columns:
            dtype = str(df_preview[col].dtype)
            null_count = df_preview[col].isnull().sum()
            cols_info.append({
                "Coluna": col,
                "Tipo": dtype,
                "Valores Nulos": null_count
            })
        
        st.dataframe(pd.DataFrame(cols_info))
        
        # Reset file pointer para upload
        uploaded_file.seek(0)
        
        # Botão para processar
        if st.button("🚀 Processar Arquivo", type="primary"):
            with st.spinner("Enviando arquivo para processamento..."):
                try:
                    # Preparar arquivo para upload
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")
                    }
                    
                    # Enviar para API
                    response = requests.post(
                        f"{API_BASE_URL}/api/data/upload_csv",
                        files=files,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ {result.get('message', 'Arquivo processado com sucesso!')}")
                        
                        # Mostrar dados processados
                        st.subheader("Dados Processados")
                        processed_response = requests.get(f"{API_BASE_URL}/api/data/view_processed?limit=10")
                        if processed_response.status_code == 200:
                            processed_data = processed_response.json()
                            st.dataframe(pd.DataFrame(processed_data))
                        
                        st.info("🎉 Dados carregados! Agora você pode acessar as páginas de Previsão e Simulação.")
                        
                    else:
                        error_detail = response.json().get('detail', 'Erro desconhecido')
                        st.error(f"❌ Erro ao processar arquivo: {error_detail}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Erro de conexão com a API. Verifique se a API está rodando.")
                except Exception as e:
                    st.error(f"❌ Erro inesperado: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erro ao ler arquivo: {str(e)}")

# Exemplo de arquivo CSV
st.subheader("📋 Exemplo de Arquivo CSV")
st.markdown("Você pode usar este exemplo como modelo:")

example_data = {
    "data": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
    "descricao": [
        "Venda Produto A",
        "Pagamento Fornecedor", 
        "Recebimento Cliente B",
        "Despesa Operacional",
        "Venda Produto C"
    ],
    "entrada": [1500.00, 0.00, 2200.00, 0.00, 1800.00],
    "saida": [0.00, 800.00, 0.00, 650.00, 0.00]
}

example_df = pd.DataFrame(example_data)
st.dataframe(example_df)

# Botão para download do exemplo
csv_example = example_df.to_csv(index=False)
st.download_button(
    label="📥 Baixar Exemplo CSV",
    data=csv_example,
    file_name="exemplo_dados_financeiros.csv",
    mime="text/csv"
)