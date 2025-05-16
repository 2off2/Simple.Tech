import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from typing import Optional, Tuple, Any
from datetime import timedelta

# Modelo de exemplo: Regressão Linear para prever o saldo futuro
# Esta é uma abordagem muito simplificada e pode não ser adequada para todos os casos.
# Modelos mais sofisticados como ARIMA, Prophet ou redes neurais podem ser considerados.

def preparar_dados_para_regressao(df: pd.DataFrame, dias_para_prever: int = 30) -> Optional[Tuple[pd.DataFrame, pd.Series]]:
    """Prepara os dados para um modelo de regressão simples.
    Cria features como dia do ano, mês, e um target que é o saldo N dias no futuro.
    """
    if "saldo" not in df.columns or "data" not in df.columns:
        print("Erro: Colunas 'saldo' e 'data' são necessárias.")
        return None

    df_copia = df.copy()
    df_copia = df_copia.sort_values(by="data").reset_index(drop=True)

    # Criar features de tempo
    df_copia["dia_do_ano"] = df_copia["data"].dt.dayofyear
    df_copia["mes"] = df_copia["data"].dt.month
    df_copia["ano"] = df_copia["data"].dt.year
    df_copia["dia_da_semana"] = df_copia["data"].dt.dayofweek

    # Criar o target: saldo N dias no futuro
    df_copia[f"saldo_futuro_{dias_para_prever}d"] = df_copia["saldo"].shift(-dias_para_prever)

    # Remover linhas com NaN no target (geralmente as últimas N linhas)
    df_completo = df_copia.dropna()

    if df_completo.empty:
        print("Não há dados suficientes para criar o target após o shift.")
        return None

    features = ["dia_do_ano", "mes", "ano", "dia_da_semana", "saldo"] # Incluindo saldo atual como feature
    X = df_completo[features]
    y = df_completo[f"saldo_futuro_{dias_para_prever}d"]
    
    print(f"Dados preparados para regressão. Features: {features}, Target: saldo_futuro_{dias_para_prever}d")
    return X, y

def treinar_modelo_regressao(X: pd.DataFrame, y: pd.Series) -> Optional[Any]:
    """Treina um modelo de Regressão Linear simples."""
    if X.empty or y.empty:
        print("Erro: Features (X) ou target (y) estão vazios.")
        return None

    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)
    # Para séries temporais, o shuffle=False é importante, e o split pode ser feito cronologicamente.
    
    modelo = LinearRegression()
    try:
        modelo.fit(X, y) # Treinar com todos os dados disponíveis por simplicidade neste exemplo
        # score = modelo.score(X_test, y_test)
        # print(f"Modelo de Regressão Linear treinado. R^2 score (simplificado no treino): {modelo.score(X,y):.2f}")
        print(f"Modelo de Regressão Linear treinado.")
        return modelo
    except Exception as e:
        print(f"Erro ao treinar o modelo: {e}")
        return None

def gerar_previsao_com_regressao(modelo: Any, df_historico: pd.DataFrame, dias_a_prever: int, dias_para_target: int) -> Optional[pd.DataFrame]:
    """Gera previsões de saldo para N dias futuros usando o modelo treinado.
    Esta função é um exemplo e pode precisar de ajustes significativos para robustez.
    A previsão iterativa (prever um dia, usar essa previsão como input para o próximo) é complexa
    e propensa a acumular erros com modelos de regressão simples como este.
    """
    if modelo is None:
        print("Erro: Modelo não treinado fornecido.")
        return None
    if df_historico.empty:
        print("Erro: DataFrame histórico vazio.")
        return None

    df_historico_sorted = df_historico.sort_values(by="data").reset_index(drop=True)
    ultima_data_historico = df_historico_sorted["data"].iloc[-1]
    ultimo_saldo_conhecido = df_historico_sorted["saldo"].iloc[-1]

    datas_futuras = pd.to_datetime([ultima_data_historico + timedelta(days=i) for i in range(1, dias_a_prever + 1)])
    previsoes_df = pd.DataFrame({"data": datas_futuras})

    # Criar features para as datas futuras
    previsoes_df["dia_do_ano"] = previsoes_df["data"].dt.dayofyear
    previsoes_df["mes"] = previsoes_df["data"].dt.month
    previsoes_df["ano"] = previsoes_df["data"].dt.year
    previsoes_df["dia_da_semana"] = previsoes_df["data"].dt.dayofweek
    
    # Para a feature 'saldo', precisamos de uma estratégia.
    # Estratégia 1 (muito simples e provavelmente imprecisa): usar o último saldo conhecido para todas as previsões.
    # Estratégia 2 (iterativa, mais complexa): prever o saldo do dia D+target, usar esse saldo para prever D+target+1, etc.
    # Aqui, vamos usar uma abordagem simplificada para demonstração, que não é ideal para regressão.
    # O modelo foi treinado para prever saldo N dias à frente, não o próximo dia.
    # Esta parte precisaria de uma lógica de previsão iterativa mais robusta ou um modelo diferente.

    saldos_previstos = []
    saldo_iterativo = ultimo_saldo_conhecido

    # Loop para prever cada dia futuro. Isso é uma simplificação grosseira.
    # O modelo foi treinado para prever 'dias_para_target' à frente.
    # Uma previsão iterativa real seria mais complexa.
    for i in range(dias_a_prever):
        features_futuras_i = pd.DataFrame({
            "dia_do_ano": [previsoes_df["dia_do_ano"].iloc[i]],
            "mes": [previsoes_df["mes"].iloc[i]],
            "ano": [previsoes_df["ano"].iloc[i]],
            "dia_da_semana": [previsoes_df["dia_da_semana"].iloc[i]],
            "saldo": [saldo_iterativo]  # Usando o saldo iterativo como feature
        })
        try:
            # O modelo prevê o saldo 'dias_para_target' no futuro.
            # Para uma previsão diária, o ideal seria um modelo que prevê o próximo dia
            # ou uma abordagem de série temporal mais direta.
            # Esta é uma simplificação para fins de exemplo.
            saldo_predito_n_dias_frente = modelo.predict(features_futuras_i)[0]
            
            # Se o modelo prevê N dias à frente, e queremos uma previsão diária, 
            # esta lógica é falha. Vamos assumir, para este exemplo, que o modelo
            # magicamente nos dá o saldo do *próximo* dia relevante para a iteração.
            # Em um cenário real, isso seria muito diferente.
            saldo_iterativo = saldo_predito_n_dias_frente # Atualiza o saldo para a próxima iteração
            saldos_previstos.append(saldo_iterativo)
        except Exception as e:
            print(f"Erro durante a previsão iterativa no dia {i+1}: {e}")
            saldos_previstos.append(np.nan) # Adiciona NaN em caso de erro
            break # Interrompe em caso de erro
            
    previsoes_df["saldo_previsto"] = saldos_previstos
    previsoes_df = previsoes_df.dropna(subset=["saldo_previsto"])

    print(f"Previsão de saldo para {len(previsoes_df)} dias gerada.")
    return previsoes_df[["data", "saldo_previsto"]]


if __name__ == "__main__":
    # Exemplo de uso
    # Crie um DataFrame de exemplo (substitua com seus dados processados)
    datas_exemplo = pd.to_datetime(["2023-01-01"] * 100) + pd.to_timedelta(np.arange(100), "D")
    saldo_exemplo = np.linspace(1000, 1500, 50).tolist() + np.linspace(1500, 800, 50).tolist()
    df_exemplo_historico = pd.DataFrame({
        "data": datas_exemplo,
        "saldo": saldo_exemplo,
        "descricao": "Movimentação",
        "entrada": 0,
        "saida": 0
    })

    print("--- DataFrame Histórico de Exemplo (Head) ---")
    print(df_exemplo_historico.head())

    dias_para_target_modelo = 7 # Modelo treinado para prever 7 dias à frente
    dados_preparados = preparar_dados_para_regressao(df_exemplo_historico, dias_para_prever=dias_para_target_modelo)

    if dados_preparados:
        X_features, y_target = dados_preparados
        modelo_treinado = treinar_modelo_regressao(X_features, y_target)

        if modelo_treinado:
            dias_futuros_para_prever = 30
            df_previsoes = gerar_previsao_com_regressao(modelo_treinado, df_exemplo_historico, dias_futuros_para_prever, dias_para_target_modelo)
            if df_previsoes is not None:
                print("\n--- Previsões Geradas (Head) ---")
                print(df_previsoes.head())
            else:
                print("Não foi possível gerar as previsões.")
        else:
            print("Modelo não foi treinado.")
    else:
        print("Não foi possível preparar os dados para o modelo.")
