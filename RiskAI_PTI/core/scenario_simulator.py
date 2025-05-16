# core/scenario_simulator.py

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Simulação de Monte Carlo para fluxo de caixa
# Este módulo simula diferentes cenários de fluxo de caixa com base em variações aleatórias
# dos valores históricos e parâmetros definidos pelo usuário.

def calcular_estatisticas_historicas(df_historico: pd.DataFrame) -> Dict[str, Any]:
    """Calcula estatísticas básicas do histórico de fluxo de caixa para uso na simulação."""
    if df_historico.empty or "data" not in df_historico.columns:
        raise ValueError("DataFrame histórico vazio ou sem coluna 'data'.")
    
    estatisticas = {}
    
    # Verificar se temos colunas de entrada e saída ou fluxo diário
    if "entrada" in df_historico.columns and "saida" in df_historico.columns:
        # Calcular estatísticas de entrada
        estatisticas["media_entrada"] = df_historico["entrada"].mean()
        estatisticas["desvio_padrao_entrada"] = df_historico["entrada"].std()
        estatisticas["min_entrada"] = df_historico["entrada"].min()
        estatisticas["max_entrada"] = df_historico["entrada"].max()
        
        # Calcular estatísticas de saída
        estatisticas["media_saida"] = df_historico["saida"].mean()
        estatisticas["desvio_padrao_saida"] = df_historico["saida"].std()
        estatisticas["min_saida"] = df_historico["saida"].min()
        estatisticas["max_saida"] = df_historico["saida"].max()
    
    # Calcular estatísticas de fluxo diário (entrada - saída)
    if "fluxo_diario" in df_historico.columns:
        estatisticas["media_fluxo"] = df_historico["fluxo_diario"].mean()
        estatisticas["desvio_padrao_fluxo"] = df_historico["fluxo_diario"].std()
    elif "entrada" in df_historico.columns and "saida" in df_historico.columns:
        df_historico["fluxo_diario"] = df_historico["entrada"] - df_historico["saida"]
        estatisticas["media_fluxo"] = df_historico["fluxo_diario"].mean()
        estatisticas["desvio_padrao_fluxo"] = df_historico["fluxo_diario"].std()
    
    # Calcular estatísticas de saldo, se disponível
    if "saldo" in df_historico.columns:
        estatisticas["ultimo_saldo"] = df_historico["saldo"].iloc[-1]
        estatisticas["media_saldo"] = df_historico["saldo"].mean()
        estatisticas["desvio_padrao_saldo"] = df_historico["saldo"].std()
    
    # Calcular estatísticas temporais
    df_historico_sorted = df_historico.sort_values(by="data")
    estatisticas["primeira_data"] = df_historico_sorted["data"].iloc[0]
    estatisticas["ultima_data"] = df_historico_sorted["data"].iloc[-1]
    estatisticas["dias_historico"] = (estatisticas["ultima_data"] - estatisticas["primeira_data"]).days + 1
    
    return estatisticas

def gerar_parametros_simulacao(
    estatisticas: Dict[str, Any],
    variacao_entrada: float = 0.1,  # Variação percentual na média de entradas
    variacao_saida: float = 0.1,    # Variação percentual na média de saídas
    dias_simulacao: int = 30,       # Número de dias a simular
    num_simulacoes: int = 1000,     # Número de simulações de Monte Carlo
    saldo_inicial: Optional[float] = None,  # Saldo inicial para a simulação
    seed: Optional[int] = None      # Seed para reprodutibilidade
) -> Dict[str, Any]:
    """Gera parâmetros para a simulação de Monte Carlo com base nas estatísticas históricas."""
    if seed is not None:
        np.random.seed(seed)
    
    parametros = {
        "dias_simulacao": dias_simulacao,
        "num_simulacoes": num_simulacoes,
        "variacao_entrada": variacao_entrada,
        "variacao_saida": variacao_saida,
        "data_inicio_simulacao": estatisticas.get("ultima_data", datetime.now()) + timedelta(days=1)
    }
    
    # Definir saldo inicial
    if saldo_inicial is not None:
        parametros["saldo_inicial"] = saldo_inicial
    elif "ultimo_saldo" in estatisticas:
        parametros["saldo_inicial"] = estatisticas["ultimo_saldo"]
    else:
        parametros["saldo_inicial"] = 0.0
    
    # Definir parâmetros de distribuição para entradas
    if "media_entrada" in estatisticas:
        # Aplicar variação à média de entradas
        parametros["media_entrada_base"] = estatisticas["media_entrada"]
        parametros["media_entrada_min"] = estatisticas["media_entrada"] * (1 - variacao_entrada)
        parametros["media_entrada_max"] = estatisticas["media_entrada"] * (1 + variacao_entrada)
        
        # Usar desvio padrão histórico ou um valor mínimo
        parametros["desvio_padrao_entrada"] = max(
            estatisticas.get("desvio_padrao_entrada", 0),
            estatisticas["media_entrada"] * 0.05  # Mínimo de 5% da média como desvio padrão
        )
    
    # Definir parâmetros de distribuição para saídas
    if "media_saida" in estatisticas:
        # Aplicar variação à média de saídas
        parametros["media_saida_base"] = estatisticas["media_saida"]
        parametros["media_saida_min"] = estatisticas["media_saida"] * (1 - variacao_saida)
        parametros["media_saida_max"] = estatisticas["media_saida"] * (1 + variacao_saida)
        
        # Usar desvio padrão histórico ou um valor mínimo
        parametros["desvio_padrao_saida"] = max(
            estatisticas.get("desvio_padrao_saida", 0),
            estatisticas["media_saida"] * 0.05  # Mínimo de 5% da média como desvio padrão
        )
    
    # Alternativa: usar estatísticas de fluxo diário se não temos entrada/saída separadas
    if "media_fluxo" in estatisticas and ("media_entrada" not in parametros or "media_saida" not in parametros):
        parametros["media_fluxo_base"] = estatisticas["media_fluxo"]
        parametros["media_fluxo_min"] = estatisticas["media_fluxo"] * (1 - variacao_entrada)  # Usando variação_entrada como proxy
        parametros["media_fluxo_max"] = estatisticas["media_fluxo"] * (1 + variacao_entrada)
        
        parametros["desvio_padrao_fluxo"] = max(
            estatisticas.get("desvio_padrao_fluxo", 0),
            abs(estatisticas["media_fluxo"]) * 0.05  # Mínimo de 5% da média como desvio padrão
        )
    
    return parametros

def executar_simulacao_monte_carlo(parametros: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Executa a simulação de Monte Carlo para fluxo de caixa com base nos parâmetros fornecidos."""
    dias_simulacao = parametros["dias_simulacao"]
    num_simulacoes = parametros["num_simulacoes"]
    saldo_inicial = parametros["saldo_inicial"]
    data_inicio = parametros["data_inicio_simulacao"]
    
    # Criar datas para a simulação
    datas_simulacao = [data_inicio + timedelta(days=i) for i in range(dias_simulacao)]
    
    # Matriz para armazenar resultados de todas as simulações
    # Formato: [num_simulacoes, dias_simulacao]
    matriz_saldos = np.zeros((num_simulacoes, dias_simulacao))
    
    # Executar simulações
    for sim in range(num_simulacoes):
        saldo_atual = saldo_inicial
        
        for dia in range(dias_simulacao):
            # Gerar fluxo de caixa para o dia atual
            if "media_entrada_base" in parametros and "media_saida_base" in parametros:
                # Simular entrada e saída separadamente
                # Variação aleatória nas médias para esta simulação específica
                media_entrada_sim = np.random.uniform(
                    parametros["media_entrada_min"],
                    parametros["media_entrada_max"]
                )
                media_saida_sim = np.random.uniform(
                    parametros["media_saida_min"],
                    parametros["media_saida_max"]
                )
                
                # Gerar valores diários com distribuição normal
                entrada_dia = max(0, np.random.normal(
                    media_entrada_sim,
                    parametros["desvio_padrao_entrada"]
                ))
                saida_dia = max(0, np.random.normal(
                    media_saida_sim,
                    parametros["desvio_padrao_saida"]
                ))
                
                fluxo_dia = entrada_dia - saida_dia
            
            elif "media_fluxo_base" in parametros:
                # Simular fluxo diário diretamente
                # Variação aleatória na média para esta simulação específica
                media_fluxo_sim = np.random.uniform(
                    parametros["media_fluxo_min"],
                    parametros["media_fluxo_max"]
                )
                
                # Gerar valor de fluxo diário com distribuição normal
                fluxo_dia = np.random.normal(
                    media_fluxo_sim,
                    parametros["desvio_padrao_fluxo"]
                )
            
            else:
                raise ValueError("Parâmetros insuficientes para simulação. Necessário média de entrada/saída ou fluxo.")
            
            # Atualizar saldo
            saldo_atual += fluxo_dia
            matriz_saldos[sim, dia] = saldo_atual
    
    # Criar DataFrame com resultados agregados
    percentis = [5, 10, 25, 50, 75, 90, 95]
    df_resultados = pd.DataFrame(index=datas_simulacao)
    
    for percentil in percentis:
        df_resultados[f'percentil_{percentil}'] = np.percentile(matriz_saldos, percentil, axis=0)
    
    df_resultados['media'] = np.mean(matriz_saldos, axis=0)
    df_resultados['min'] = np.min(matriz_saldos, axis=0)
    df_resultados['max'] = np.max(matriz_saldos, axis=0)
    
    # Calcular probabilidades de eventos específicos
    # Exemplo: probabilidade de saldo negativo em cada dia
    prob_saldo_negativo = np.mean(matriz_saldos < 0, axis=0)
    df_resultados['prob_saldo_negativo'] = prob_saldo_negativo
    
    # Criar DataFrame com todas as simulações individuais (para visualização detalhada)
    df_simulacoes = pd.DataFrame(
        matriz_saldos.T,  # Transpor para ter dias nas linhas e simulações nas colunas
        index=datas_simulacao,
        columns=[f'sim_{i+1}' for i in range(num_simulacoes)]
    )
    
    return df_resultados, df_simulacoes

def visualizar_resultados_simulacao(df_resultados: pd.DataFrame, titulo: str = "Simulação de Monte Carlo - Fluxo de Caixa") -> plt.Figure:
    """Cria uma visualização dos resultados da simulação de Monte Carlo."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plotar área entre percentis 5 e 95 (90% de confiança)
    ax.fill_between(
        df_resultados.index,
        df_resultados['percentil_5'],
        df_resultados['percentil_95'],
        alpha=0.3,
        color='lightblue',
        label='Intervalo de 90% de confiança'
    )
    
    # Plotar área entre percentis 25 e 75 (50% de confiança)
    ax.fill_between(
        df_resultados.index,
        df_resultados['percentil_25'],
        df_resultados['percentil_75'],
        alpha=0.5,
        color='blue',
        label='Intervalo de 50% de confiança'
    )
    
    # Plotar mediana (percentil 50)
    ax.plot(
        df_resultados.index,
        df_resultados['percentil_50'],
        'b-',
        linewidth=2,
        label='Mediana'
    )
    
    # Plotar média
    ax.plot(
        df_resultados.index,
        df_resultados['media'],
        'r--',
        linewidth=1.5,
        label='Média'
    )
    
    # Adicionar linha horizontal em y=0
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.3)
    
    # Configurar gráfico
    ax.set_title(titulo)
    ax.set_xlabel('Data')
    ax.set_ylabel('Saldo Projetado')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Formatar eixo x para datas
    fig.autofmt_xdate()
    
    return fig

def analisar_probabilidades(df_resultados: pd.DataFrame) -> Dict[str, Any]:
    """Analisa as probabilidades de eventos específicos com base nos resultados da simulação."""
    analise = {}
    
    # Probabilidade de saldo negativo no final do período
    analise["prob_saldo_negativo_final"] = df_resultados["prob_saldo_negativo"].iloc[-1]
    
    # Probabilidade de saldo negativo em qualquer momento
    analise["prob_saldo_negativo_qualquer_momento"] = df_resultados["prob_saldo_negativo"].max()
    
    # Dia com maior probabilidade de saldo negativo
    idx_max_prob_negativo = df_resultados["prob_saldo_negativo"].idxmax()
    analise["dia_maior_prob_negativo"] = idx_max_prob_negativo
    analise["valor_maior_prob_negativo"] = df_resultados["prob_saldo_negativo"].max()
    
    # Valor mínimo esperado (percentil 5 do último dia)
    analise["valor_minimo_esperado"] = df_resultados["percentil_5"].iloc[-1]
    
    # Valor máximo esperado (percentil 95 do último dia)
    analise["valor_maximo_esperado"] = df_resultados["percentil_95"].iloc[-1]
    
    # Valor mediano esperado (percentil 50 do último dia)
    analise["valor_mediano_esperado"] = df_resultados["percentil_50"].iloc[-1]
    
    return analise

if __name__ == "__main__":
    # Exemplo de uso
    # Criar dados históricos de exemplo
    datas_exemplo = pd.date_range(start="2023-01-01", periods=100, freq="D")
    np.random.seed(42)  # Para reprodutibilidade
    
    # Simular entradas com tendência crescente e sazonalidade semanal
    entradas_base = np.linspace(100, 150, 100)  # Tendência crescente
    sazonalidade = np.sin(np.arange(100) * (2 * np.pi / 7)) * 20  # Sazonalidade semanal
    ruido_entradas = np.random.normal(0, 10, 100)  # Ruído aleatório
    entradas = entradas_base + sazonalidade + ruido_entradas
    entradas = np.maximum(entradas, 0)  # Garantir que não há entradas negativas
    
    # Simular saídas com padrão diferente
    saidas_base = np.linspace(80, 120, 100)  # Tendência crescente mais lenta
    ruido_saidas = np.random.normal(0, 15, 100)  # Ruído aleatório maior
    saidas = saidas_base + ruido_saidas
    saidas = np.maximum(saidas, 0)  # Garantir que não há saídas negativas
    
    # Calcular fluxo e saldo
    fluxo_diario = entradas - saidas
    saldo = np.cumsum(fluxo_diario) + 1000  # Começando com saldo inicial de 1000
    
    # Criar DataFrame histórico
    df_historico = pd.DataFrame({
        "data": datas_exemplo,
        "entrada": entradas,
        "saida": saidas,
        "fluxo_diario": fluxo_diario,
        "saldo": saldo
    })
    
    print("--- DataFrame Histórico de Exemplo (Head) ---")
    print(df_historico.head())
    
    # Calcular estatísticas históricas
    estatisticas = calcular_estatisticas_historicas(df_historico)
    print("\n--- Estatísticas Históricas ---")
    for chave, valor in estatisticas.items():
        print(f"{chave}: {valor}")
    
    # Gerar parâmetros para simulação
    parametros_simulacao = gerar_parametros_simulacao(
        estatisticas,
        variacao_entrada=0.15,  # 15% de variação na média de entradas
        variacao_saida=0.20,    # 20% de variação na média de saídas
        dias_simulacao=30,      # Simular 30 dias
        num_simulacoes=500,     # 500 simulações
        seed=42                 # Para reprodutibilidade
    )
    print("\n--- Parâmetros de Simulação ---")
    for chave, valor in parametros_simulacao.items():
        print(f"{chave}: {valor}")
    
    # Executar simulação de Monte Carlo
    df_resultados, df_simulacoes = executar_simulacao_monte_carlo(parametros_simulacao)
    print("\n--- Resultados da Simulação (Head) ---")
    print(df_resultados.head())
    
    # Analisar probabilidades
    analise_prob = analisar_probabilidades(df_resultados)
    print("\n--- Análise de Probabilidades ---")
    for chave, valor in analise_prob.items():
        print(f"{chave}: {valor}")
    
    # Visualizar resultados (em ambiente interativo ou salvando a figura)
    fig = visualizar_resultados_simulacao(df_resultados)
    # fig.savefig("simulacao_monte_carlo.png")  # Descomentar para salvar a figura
    # plt.show()  # Descomentar para mostrar a figura em ambiente interativo
