# tests/test_core.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Adicionar o diretório raiz do projeto ao sys.path para permitir importações do core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import data_processing, cashflow_predictor, risk_analyzer, scenario_simulator, customer_analysis

# --- Fixtures para Dados de Teste ---
@pytest.fixture
def sample_raw_data_dict():
    """Retorna um dicionário com dados brutos de exemplo para criar um DataFrame."""
    return {
        "data": [
            "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05",
            "2023-01-06", "2023-01-07", "2023-01-08", "2023-01-09", "2023-01-10"
        ],
        "descricao": [
            "Venda A", "Pagamento X", "Venda B", "Despesa Y", "Venda C",
            "Pagamento Z", "Venda D", "Despesa W", "Venda E", "Pagamento V"
        ],
        "entrada": [100.0, 0.0, 150.0, 0.0, 200.0, 0.0, 50.0, 0.0, 300.0, 0.0],
        "saida": [0.0, 50.0, 0.0, 75.0, 0.0, 100.0, 0.0, 25.0, 0.0, 120.0],
        "id_cliente": ["C1", "F1", "C2", "S1", "C1", "F2", "C3", "S2", "C2", "F1"],
        "data_vencimento": [
            "2023-01-10", "2023-01-02", "2023-01-15", "2023-01-04", "2023-01-20",
            "2023-01-06", "2023-01-12", "2023-01-08", "2023-01-25", "2023-01-10"
        ],
        "data_pagamento": [
            "2023-01-09", "2023-01-02", None, "2023-01-04", None,
            "2023-01-07", None, "2023-01-08", None, "2023-01-11"
        ],
        "valor_fatura": [100.0, 50.0, 150.0, 75.0, 200.0, 100.0, 50.0, 25.0, 300.0, 120.0]
    }

@pytest.fixture
def sample_raw_dataframe(sample_raw_data_dict):
    """Cria um DataFrame Pandas a partir dos dados brutos de exemplo."""
    return pd.DataFrame(sample_raw_data_dict)

@pytest.fixture
def sample_processed_dataframe(sample_raw_dataframe):
    """Processa o DataFrame de exemplo usando a função do módulo data_processing."""
    # Para testar data_processing.processar_df_financeiro, precisamos de um df já lido.
    # A função processar_arquivo_completo lida com o path, então vamos simular o df pós-leitura.
    df_copy = sample_raw_dataframe.copy()
    return data_processing.processar_df_financeiro(df_copy)

# --- Testes para o Módulo data_processing ---

def test_processar_df_financeiro_colunas_essenciais(sample_raw_dataframe):
    """Testa se as colunas essenciais (data, fluxo_diario, saldo) são criadas."""
    df_processed = data_processing.processar_df_financeiro(sample_raw_dataframe.copy())
    assert df_processed is not None
    assert "data" in df_processed.columns
    assert "fluxo_diario" in df_processed.columns
    assert "saldo" in df_processed.columns
    assert pd.api.types.is_datetime64_any_dtype(df_processed["data"])

def test_processar_df_financeiro_calculo_fluxo_saldo(sample_raw_dataframe):
    """Testa o cálculo do fluxo diário e do saldo."""
    df_copy = sample_raw_dataframe.copy()
    df_copy["entrada"] = df_copy["entrada"].fillna(0)
    df_copy["saida"] = df_copy["saida"].fillna(0)
    df_processed = data_processing.processar_df_financeiro(df_copy)
    
    # Exemplo para a primeira linha
    expected_fluxo_dia1 = df_copy.loc[0, "entrada"] - df_copy.loc[0, "saida"]
    # O processamento ordena por data, então precisamos encontrar a primeira data original
    first_original_date_data = df_processed[df_processed["descricao"] == df_copy.loc[0, "descricao"]]
    assert not first_original_date_data.empty
    assert first_original_date_data["fluxo_diario"].iloc[0] == expected_fluxo_dia1
    # O saldo é cumulativo, então o primeiro saldo é o primeiro fluxo
    assert first_original_date_data["saldo"].iloc[0] == expected_fluxo_dia1

# --- Testes para o Módulo cashflow_predictor ---

def test_preparar_dados_para_regressao(sample_processed_dataframe):
    """Testa a preparação de dados para modelos de regressão."""
    if sample_processed_dataframe is None or sample_processed_dataframe.empty:
        pytest.skip("DataFrame processado está vazio, pulando teste.")
    
    X, y = cashflow_predictor.preparar_dados_para_regressao(sample_processed_dataframe, dias_para_prever=7)
    assert X is not None
    assert y is not None
    assert not X.empty
    assert not y.empty
    assert len(X) == len(y)
    assert "fluxo_diario_lag_1" in X.columns # Exemplo de feature de lag
    assert "dia_da_semana" in X.columns    # Exemplo de feature de data

def test_treinar_modelo_regressao_e_prever(sample_processed_dataframe):
    """Testa o treinamento de um modelo de regressão e a geração de previsões."""
    if sample_processed_dataframe is None or sample_processed_dataframe.empty or len(sample_processed_dataframe) < 10:
        pytest.skip("DataFrame processado muito pequeno para teste de treino/previsão, pulando.")

    X, y = cashflow_predictor.preparar_dados_para_regressao(sample_processed_dataframe, dias_para_prever=3)
    if X.empty or y.empty or len(X) < 2: # Precisa de pelo menos 2 amostras para treinar/testar
        pytest.skip("Dados preparados para regressão insuficientes, pulando teste.")

    # Dividir manualmente para teste simples (não é o foco aqui testar a divisão em si)
    X_train, y_train = X.iloc[:-1], y.iloc[:-1]
    X_test = X.iloc[-1:]

    if X_train.empty:
        pytest.skip("Dados de treino insuficientes após divisão, pulando teste.")

    modelo = cashflow_predictor.treinar_modelo_regressao(X_train, y_train)
    assert modelo is not None
    
    # Testar a função de previsão completa
    df_previsoes = cashflow_predictor.gerar_previsao_com_regressao(
        modelo, 
        sample_processed_dataframe, 
        dias_a_prever=5, 
        dias_para_target=3
    )
    assert df_previsoes is not None
    assert not df_previsoes.empty
    assert len(df_previsoes) == 5
    assert "data" in df_previsoes.columns
    assert "saldo_previsto" in df_previsoes.columns

# --- Testes para o Módulo risk_analyzer ---

def test_identificar_riscos_com_base_em_limiares():
    """Testa a identificação de riscos com base em limiares."""
    datas_previsao = pd.to_datetime(["2023-02-01", "2023-02-02", "2023-02-03"])
    saldos_previstos = [1200, 800, 1300] # Um saldo abaixo do limiar padrão de 1000
    df_previsoes = pd.DataFrame({"data": datas_previsao, "saldo_previsto": saldos_previstos})
    
    alertas = risk_analyzer.identificar_riscos_com_base_em_limiares(df_previsoes)
    assert isinstance(alertas, list)
    assert len(alertas) > 0
    assert any(alerta["tipo_risco"] == "Saldo Baixo" for alerta in alertas)

# --- Testes para o Módulo scenario_simulator ---

@pytest.fixture
def sample_historical_stats(sample_processed_dataframe):
    """Calcula estatísticas históricas do DataFrame processado."""
    if sample_processed_dataframe is None or sample_processed_dataframe.empty:
        pytest.skip("DataFrame processado está vazio, pulando criação de estatísticas.")
    return scenario_simulator.calcular_estatisticas_historicas(sample_processed_dataframe)

def test_calcular_estatisticas_historicas(sample_processed_dataframe):
    """Testa o cálculo de estatísticas históricas."""
    if sample_processed_dataframe is None or sample_processed_dataframe.empty:
        pytest.skip("DataFrame processado está vazio, pulando teste de estatísticas.")
    
    stats = scenario_simulator.calcular_estatisticas_historicas(sample_processed_dataframe)
    assert isinstance(stats, dict)
    assert "media_fluxo" in stats
    assert "desvio_padrao_fluxo" in stats
    assert "ultimo_saldo" in stats

def test_gerar_parametros_simulacao(sample_historical_stats):
    """Testa a geração de parâmetros para simulação."""
    if sample_historical_stats is None:
        pytest.skip("Estatísticas históricas não disponíveis, pulando teste.")
        
    params = scenario_simulator.gerar_parametros_simulacao(sample_historical_stats, dias_simulacao=10, num_simulacoes=50)
    assert isinstance(params, dict)
    assert params["dias_simulacao"] == 10
    assert params["num_simulacoes"] == 50
    assert "saldo_inicial" in params

def test_executar_simulacao_monte_carlo(sample_historical_stats):
    """Testa a execução da simulação de Monte Carlo."""
    if sample_historical_stats is None:
        pytest.skip("Estatísticas históricas não disponíveis, pulando teste.")

    params = scenario_simulator.gerar_parametros_simulacao(sample_historical_stats, dias_simulacao=5, num_simulacoes=10, seed=42)
    df_resultados, df_simulacoes = scenario_simulator.executar_simulacao_monte_carlo(params)
    
    assert df_resultados is not None
    assert not df_resultados.empty
    assert len(df_resultados) == 5 # dias_simulacao
    assert "media" in df_resultados.columns
    assert "percentil_50" in df_resultados.columns
    
    assert df_simulacoes is not None
    assert not df_simulacoes.empty
    assert len(df_simulacoes) == 5 # dias_simulacao
    assert df_simulacoes.shape[1] == 10 # num_simulacoes

# --- Testes para o Módulo customer_analysis ---

@pytest.fixture
def sample_faturas_data():
    data_hoje = datetime.now()
    return {
        "id_cliente": ["C001", "C001", "C002"],
        "data_vencimento": [data_hoje - timedelta(days=10), data_hoje - timedelta(days=40), data_hoje - timedelta(days=5)],
        "data_pagamento": [None, data_hoje - timedelta(days=30), None],
        "valor_fatura": [100.0, 250.0, 50.0]
    }

@pytest.fixture
def df_faturas_exemplo(sample_faturas_data):
    df = pd.DataFrame(sample_faturas_data)
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"])
    df["data_pagamento"] = pd.to_datetime(df["data_pagamento"], errors="coerce")
    return df

def test_calcular_dias_atraso(df_faturas_exemplo):
    """Testa o cálculo de dias de atraso e status de pagamento."""
    df_analise = customer_analysis.calcular_dias_atraso(df_faturas_exemplo.copy())
    assert "status_pagamento" in df_analise.columns
    assert "dias_atraso" in df_analise.columns
    
    # C001, fatura 1 (vencida há 10 dias, não paga)
    fatura1_c001 = df_analise[(df_analise["id_cliente"] == "C001") & (df_analise["valor_fatura"] == 100.0)]
    assert fatura1_c001["status_pagamento"].iloc[0] == "Em Atraso"
    assert fatura1_c001["dias_atraso"].iloc[0] >= 9 # Pode ser 9 ou 10 dependendo da hora exata

    # C001, fatura 2 (vencida há 40 dias, paga há 30 dias -> 10 dias de atraso no pagamento)
    fatura2_c001 = df_analise[(df_analise["id_cliente"] == "C001") & (df_analise["valor_fatura"] == 250.0)]
    assert fatura2_c001["status_pagamento"].iloc[0] == "Pago com Atraso"
    assert fatura2_c001["dias_atraso"].iloc[0] == 10

def test_segmentar_clientes_por_risco_inadimplencia(df_faturas_exemplo):
    """Testa a segmentação de clientes por risco de inadimplência."""
    df_analise = customer_analysis.calcular_dias_atraso(df_faturas_exemplo.copy())
    df_segmentado = customer_analysis.segmentar_clientes_por_risco_inadimplencia(df_analise)
    
    assert df_segmentado is not None
    if not df_segmentado.empty:
        assert "id_cliente" in df_segmentado.columns
        assert "risco_inadimplencia" in df_segmentado.columns
        # Verificar se algum cliente foi classificado (pode ser Baixo, Médio ou Alto)
        assert len(df_segmentado[df_segmentado["risco_inadimplencia"].isin(["Baixo", "Médio", "Alto"])]) > 0
    else:
        # Se o df_segmentado estiver vazio, significa que não há faturas "Em Atraso"
        # nos dados de exemplo para segmentar, o que é um cenário válido.
        pass 

def test_gerar_relatorio_inadimplencia(df_faturas_exemplo):
    """Testa a geração do relatório de inadimplência."""
    df_analise = customer_analysis.calcular_dias_atraso(df_faturas_exemplo.copy())
    df_segmentado = customer_analysis.segmentar_clientes_por_risco_inadimplencia(df_analise)
    relatorio = customer_analysis.gerar_relatorio_inadimplencia(df_segmentado)
    
    assert isinstance(relatorio, dict)
    assert "total_clientes_com_faturas_em_atraso" in relatorio
    assert "valor_total_em_atraso" in relatorio
    assert "distribuicao_risco" in relatorio
    assert "top_5_clientes_alto_risco" in relatorio

# Para executar os testes, no terminal, na raiz do projeto:
# pytest tests/test_core.py

