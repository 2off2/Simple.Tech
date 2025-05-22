import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Previsão de Fluxo de Caixa - RiskAI",
    page_icon="📈",
    layout="wide"
)

# URL base da API
API_BASE_URL = "http://localhost:8000"

st.title("📈 Previsão de Fluxo de Caixa")

# Verificar se há dados carregados
def check_data_loaded():
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/view_processed?limit=1", timeout=5)
        return response.status_code == 200
    except:
        return False

if not check_data_loaded():
    st.warning("⚠️ Nenhum dado encontrado. Por favor, carregue seus dados na página de Upload primeiro.")
    st.stop()

st.success("✅ Dados carregados. Você pode gerar previsões!")

# Parâmetros da previsão
st.subheader("⚙️ Configurações da Previsão")

col1, col2 = st.columns(2)

with col1:
    days_to_predict = st.number_input(
        "Dias para Simular no Futuro:",
        min_value=1,
        max_value=365,
        value=30,
        help="Quantos dias à frente você quer prever"
    )

with col2:
    confidence_level = st.selectbox(
        "Nível de Confiança:",
        options=[90, 95, 99],
        index=1,
        help="Nível de confiança para as previsões"
    )

# Botão para gerar previsão
if st.button("🔮 Gerar Previsão", type="primary"):
    with st.spinner("Gerando previsões..."):
        try:
            # Fazer requisição para API
            payload = {
                "days_to_predict": days_to_predict
            }
            
            response = requests.post(
                f"{API_BASE_URL}/api/predictions/cashflow",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                predictions = result.get("predictions", [])
                alerts = result.get("alerts", [])
                
                if predictions:
                    # Converter para DataFrame
                    df_predictions = pd.DataFrame(predictions)
                    df_predictions['data'] = pd.to_datetime(df_predictions['data'])
                    
                    # Gráfico de previsão
                    st.subheader("📊 Projeção de Saldo")
                    
                    fig = go.Figure()
                    
                    # Linha principal do saldo
                    fig.add_trace(go.Scatter(
                        x=df_predictions['data'],
                        y=df_predictions['saldo_previsto'],
                        mode='lines+markers',
                        name='Saldo Previsto',
                        line=dict(color='blue', width=3)
                    ))
                    
                    # Linha zero para referência
                    fig.add_hline(y=0, line_dash="dash", line_color="red", 
                                annotation_text="Saldo Zero")
                    
                    fig.update_layout(
                        title="Projeção de Saldo nos Próximos Dias",
                        xaxis_title="Data",
                        yaxis_title="Saldo (R$)",
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela de previsões
                    st.subheader("📋 Tabela de Previsões")
                    
                    # Formatar valores monetários
                    df_display = df_predictions.copy()
                    df_display['data'] = df_display['data'].dt.strftime('%Y-%m-%d')
                    df_display['saldo_previsto'] = df_display['saldo_previsto'].apply(lambda x: f"R$ {x:,.2f}")
                    df_display['entrada_estimada'] = df_display['entrada_estimada'].apply(lambda x: f"R$ {x:,.2f}")
                    df_display['saida_estimada'] = df_display['saida_estimada'].apply(lambda x: f"R$ {x:,.2f}")
                    
                    # Renomear colunas
                    df_display = df_display.rename(columns={
                        'data': 'Data',
                        'saldo_previsto': 'Saldo Previsto',
                        'entrada_estimada': 'Entrada Estimada',
                        'saida_estimada': 'Saída Estimada'
                    })
                    
                    st.dataframe(df_display, use_container_width=True)
                    
                    # Alertas de risco
                    if alerts:
                        st.subheader("🚨 Alertas de Risco")
                        
                        for alert in alerts:
                            nivel = alert.get('nivel', 'Médio')
                            if nivel == 'Alto':
                                st.error(f"🔴 **{alert.get('tipo_risco')}** - {alert.get('data')}: {alert.get('mensagem')}")
                            elif nivel == 'Médio':
                                st.warning(f"🟡 **{alert.get('tipo_risco')}** - {alert.get('data')}: {alert.get('mensagem')}")
                            else:
                                st.info(f"🔵 **{alert.get('tipo_risco')}** - {alert.get('data')}: {alert.get('mensagem')}")
                    else:
                        st.success("✅ Nenhum alerta de risco identificado para o período!")
                    
                    # Métricas resumo
                    st.subheader("📊 Resumo da Previsão")
                    
                    saldo_final = df_predictions['saldo_previsto'].iloc[-1]
                    saldo_inicial = df_predictions['saldo_previsto'].iloc[0]
                    variacao = saldo_final - saldo_inicial
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Saldo Final Previsto", f"R$ {saldo_final:,.2f}")
                    
                    with col2:
                        st.metric("Variação Total", f"R$ {variacao:,.2f}", 
                                delta=f"R$ {variacao:,.2f}")
                    
                    with col3:
                        saldo_min = df_predictions['saldo_previsto'].min()
                        st.metric("Menor Saldo", f"R$ {saldo_min:,.2f}")
                    
                    with col4:
                        saldo_max = df_predictions['saldo_previsto'].max()
                        st.metric("Maior Saldo", f"R$ {saldo_max:,.2f}")
                    
                else:
                    st.error("❌ Nenhuma previsão foi gerada.")
                    
            else:
                error_detail = response.json().get('detail', 'Erro desconhecido')
                st.error(f"❌ Erro ao gerar previsão: {error_detail}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Erro de conexão com a API. Verifique se a API está rodando.")
        except Exception as e:
            st.error(f"❌ Erro inesperado: {str(e)}")

# Informações adicionais
st.subheader("ℹ️ Sobre as Previsões")
st.markdown("""
- **Modelo**: Utiliza regressão linear baseada em dados históricos
- **Variáveis**: Médias móveis de entradas, saídas e saldo anterior
- **Alertas**: Identifica riscos de saldo negativo ou baixo
- **Precisão**: Depende da qualidade e quantidade dos dados históricos
""")

# Botão para exportar dados
if 'df_predictions' in locals():
    csv_data = df_predictions.to_csv(index=False)
    st.download_button(
        label="📥 Baixar Previsões (CSV)",
        data=csv_data,
        file_name=f"previsoes_fluxo_caixa_{days_to_predict}_dias.csv",
        mime="text/csv"
    )