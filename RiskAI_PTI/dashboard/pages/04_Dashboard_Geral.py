import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Dashboard Geral - RiskAI",
    page_icon="📊",
    layout="wide"
)

# URL base da API
API_BASE_URL = "http://localhost:8000"

st.title("📊 Dashboard Geral - RiskAI")

# Verificar se há dados carregados
def check_data_loaded():
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/view_processed?limit=1", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_processed_data(limit=100):
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/view_processed?limit={limit}", timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return None
    except:
        return None

if not check_data_loaded():
    st.warning("⚠️ Nenhum dado encontrado. Por favor, carregue seus dados na página de Upload primeiro.")
    
    # Mostrar dashboard de exemplo
    st.subheader("📋 Visão Geral do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Status da API", "🟢 Online" if check_data_loaded() else "🔴 Offline")
    with col2:
        st.metric("Dados Carregados", "Não")
    with col3:
        st.metric("Páginas Disponíveis", "4")
    with col4:
        st.metric("Funcionalidades", "3")
    
    st.info("Carregue seus dados para ver análises detalhadas!")
    st.stop()

# Carregar dados
df_data = get_processed_data(limit=1000)

if df_data is None or df_data.empty:
    st.error("❌ Erro ao carregar dados processados.")
    st.stop()

st.success("✅ Dados carregados com sucesso!")

# Converter coluna de data
df_data['data'] = pd.to_datetime(df_data['data'])
df_data = df_data.sort_values('data')

# Botão de atualização
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Atualizar Dados"):
        st.rerun()
with col2:
    st.caption(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

# Métricas principais
st.subheader("📊 Métricas Principais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_entrada = df_data['entrada'].sum()
    st.metric("Total de Entradas", f"R$ {total_entrada:,.2f}")

with col2:
    total_saida = df_data['saida'].sum()
    st.metric("Total de Saídas", f"R$ {total_saida:,.2f}")

with col3:
    saldo_atual = df_data['saldo'].iloc[-1] if 'saldo' in df_data.columns else 0
    st.metric("Saldo Atual", f"R$ {saldo_atual:,.2f}")

with col4:
    fluxo_liquido = total_entrada - total_saida
    st.metric("Fluxo Líquido", f"R$ {fluxo_liquido:,.2f}", 
              delta=f"R$ {fluxo_liquido:,.2f}")

# Gráficos principais
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolução do Saldo")
    if 'saldo' in df_data.columns:
        fig_saldo = px.line(df_data, x='data', y='saldo', 
                           title="Evolução do Saldo ao Longo do Tempo")
        fig_saldo.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_saldo, use_container_width=True)
    else:
        st.info("Coluna 'saldo' não encontrada nos dados")

with col2:
    st.subheader("💰 Entradas vs Saídas")
    
    # Agrupar por mês para melhor visualização
    df_monthly = df_data.groupby(df_data['data'].dt.to_period('M')).agg({
        'entrada': 'sum',
        'saida': 'sum'
    }).reset_index()
    df_monthly['data'] = df_monthly['data'].astype(str)
    
    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(name='Entradas', x=df_monthly['data'], y=df_monthly['entrada']))
    fig_bars.add_trace(go.Bar(name='Saídas', x=df_monthly['data'], y=df_monthly['saida']))
    fig_bars.update_layout(title="Entradas vs Saídas por Mês", barmode='group')
    st.plotly_chart(fig_bars, use_container_width=True)

# Análise temporal
st.subheader("📅 Análise Temporal")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Período dos Dados**")
    data_inicio = df_data['data'].min()
    data_fim = df_data['data'].max()
    dias_dados = (data_fim - data_inicio).days
    st.write(f"📅 {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")
    st.write(f"⏱️ {dias_dados} dias de histórico")

with col2:
    st.markdown("**Médias Diárias**")
    media_entrada = df_data['entrada'].mean()
    media_saida = df_data['saida'].mean()
    st.write(f"💰 Entrada: R$ {media_entrada:,.2f}")
    st.write(f"💸 Saída: R$ {media_saida:,.2f}")

with col3:
    st.markdown("**Variabilidade**")
    std_entrada = df_data['entrada'].std()
    std_saida = df_data['saida'].std()
    st.write(f"📊 Entrada (σ): R$ {std_entrada:,.2f}")
    st.write(f"📊 Saída (σ): R$ {std_saida:,.2f}")

# Análise de risco rápida
st.subheader("🚨 Análise de Risco Rápida")

# Calcular alguns indicadores de risco
dias_saldo_negativo = len(df_data[df_data['saldo'] < 0]) if 'saldo' in df_data.columns else 0
pct_dias_negativos = (dias_saldo_negativo / len(df_data)) * 100

col1, col2, col3 = st.columns(3)

with col1:
    if pct_dias_negativos > 20:
        st.error(f"🔴 Alto Risco: {pct_dias_negativos:.1f}% dos dias com saldo negativo")
    elif pct_dias_negativos > 5:
        st.warning(f"🟡 Risco Médio: {pct_dias_negativos:.1f}% dos dias com saldo negativo")
    else:
        st.success(f"🟢 Baixo Risco: {pct_dias_negativos:.1f}% dos dias com saldo negativo")

with col2:
    # Volatilidade do fluxo
    volatilidade = df_data['fluxo_diario'].std() if 'fluxo_diario' in df_data.columns else 0
    st.metric("Volatilidade Diária", f"R$ {volatilidade:,.2f}")

with col3:
    # Maior déficit
    menor_saldo = df_data['saldo'].min() if 'saldo' in df_data.columns else 0
    st.metric("Menor Saldo Registrado", f"R$ {menor_saldo:,.2f}")

# Previsão rápida (últimos 7 dias)
st.subheader("🔮 Previsão Rápida (Próximos 7 dias)")

try:
    quick_prediction_payload = {"days_to_predict": 7}
    response = requests.post(
        f"{API_BASE_URL}/api/predictions/cashflow",
        json=quick_prediction_payload,
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        predictions = result.get("predictions", [])
        alerts = result.get("alerts", [])
        
        if predictions:
            df_pred = pd.DataFrame(predictions)
            
            col1, col2 = st.columns(2)
            
            with col1:
                saldo_7dias = df_pred['saldo_previsto'].iloc[-1]
                variacao_7dias = saldo_7dias - saldo_atual
                st.metric("Saldo Previsto (7 dias)", 
                         f"R$ {saldo_7dias:,.2f}",
                         delta=f"R$ {variacao_7dias:,.2f}")
            
            with col2:
                if alerts:
                    st.warning(f"⚠️ {len(alerts)} alertas nos próximos 7 dias")
                else:
                    st.success("✅ Nenhum alerta nos próximos 7 dias")
        else:
            st.info("Não foi possível gerar previsão rápida")
    else:
        st.info("Previsão rápida indisponível")
        
except Exception as e:
    st.info("Previsão rápida indisponível")

# Tabela de dados recentes
st.subheader("📋 Transações Recentes")
recent_data = df_data.tail(10).copy()

# Formatar para exibição
recent_data['data'] = recent_data['data'].dt.strftime('%d/%m/%Y')
if 'entrada' in recent_data.columns:
    recent_data['entrada'] = recent_data['entrada'].apply(lambda x: f"R$ {x:,.2f}")
if 'saida' in recent_data.columns:
    recent_data['saida'] = recent_data['saida'].apply(lambda x: f"R$ {x:,.2f}")
if 'saldo' in recent_data.columns:
    recent_data['saldo'] = recent_data['saldo'].apply(lambda x: f"R$ {x:,.2f}")

# Renomear colunas
column_mapping = {
    'data': 'Data',
    'descricao': 'Descrição',
    'entrada': 'Entrada',
    'saida': 'Saída',
    'saldo': 'Saldo'
}
recent_data = recent_data.rename(columns=column_mapping)

st.dataframe(recent_data, use_container_width=True)

# Ações rápidas
st.subheader("⚡ Ações Rápidas")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📈 Gerar Previsão 30 dias"):
        st.switch_page("pages/02_Previsao.py")

with col2:
    if st.button("🎲 Executar Simulação"):
        st.switch_page("pages/03_Simulacao.py")

with col3:
    if st.button("📤 Carregar Novos Dados"):
        st.switch_page("pages/01_Upload.py")

with col4:
    # Botão para exportar dados
    csv_data = df_data.to_csv(index=False)
    st.download_button(
        label="📥 Exportar Dados",
        data=csv_data,
        file_name=f"dados_financeiros_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Rodapé
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🤖 RiskAI - Dashboard Financeiro")
with col2:
    st.caption(f"📊 {len(df_data)} transações analisadas")
with col3:
    st.caption(f"🕐 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")