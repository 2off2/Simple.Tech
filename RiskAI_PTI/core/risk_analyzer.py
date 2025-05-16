# core/risk_analyzer.py

import pandas as pd
from typing import List, Dict, Any, Optional

# Limiares de exemplo para alertas de risco
LIMIAR_SALDO_BAIXO = 1000  # Exemplo: alertar se o saldo previsto cair abaixo de 1000
LIMIAR_VARIACAO_NEGATIVA_GRANDE = -0.20 # Exemplo: alertar se o saldo cair mais de 20% em um período
DIAS_CONSECUTIVOS_NEGATIVOS = 3 # Exemplo: alertar se houver N dias consecutivos de fluxo negativo

def identificar_riscos_com_base_em_limiares(df_previsoes: pd.DataFrame, saldo_inicial_real: Optional[float] = None) -> List[Dict[str, Any]]:
    """Analisa as previsões de fluxo de caixa e identifica riscos com base em limiares predefinidos."""
    alertas = []
    if df_previsoes.empty:
        return alertas

    df_analise = df_previsoes.copy()
    df_analise = df_analise.sort_values(by="data").reset_index(drop=True)

    # Se o saldo inicial real for fornecido, ajusta o saldo previsto (se for cumulativo)
    # Esta lógica depende de como o saldo_previsto foi gerado.
    # Se o saldo_previsto já é o saldo absoluto, este ajuste pode não ser necessário
    # ou precisar de uma lógica diferente.
    if saldo_inicial_real is not None and "saldo_previsto" in df_analise.columns:
        if not df_analise.empty:
            primeiro_saldo_previsto = df_analise["saldo_previsto"].iloc[0]
            # Se o saldo_previsto é um delta ou precisa ser ancorado:
            # df_analise["saldo_previsto_ajustado"] = saldo_inicial_real + (df_analise["saldo_previsto"] - primeiro_saldo_previsto)
            # Por simplicidade, vamos assumir que o saldo_previsto já é o saldo absoluto projetado.
            pass # Ajuste conforme a natureza do saldo_previsto
    
    coluna_saldo_para_analise = "saldo_previsto_ajustado" if "saldo_previsto_ajustado" in df_analise.columns else "saldo_previsto"
    if coluna_saldo_para_analise not in df_analise.columns:
        print(f"Coluna de saldo para análise (\t'{coluna_saldo_para_analise}\t') não encontrada.")
        return alertas

    # 1. Risco de Saldo Baixo
    for index, row in df_analise.iterrows():
        if row[coluna_saldo_para_analise] < LIMIAR_SALDO_BAIXO:
            alertas.append({
                "data": row["data"].strftime("%Y-%m-%d"),
                "tipo_risco": "Saldo Baixo",
                "mensagem": f"Alerta: Saldo previsto de {row[coluna_saldo_para_analise]:.2f} em {row["data"].strftime("%Y-%m-%d")} está abaixo do limiar de {LIMIAR_SALDO_BAIXO:.2f}.",
                "nivel": "Alto"
            })

    # 2. Risco de Variação Negativa Grande (comparado ao saldo anterior ou inicial)
    saldo_anterior = saldo_inicial_real if saldo_inicial_real is not None else (df_analise[coluna_saldo_para_analise].iloc[0] if not df_analise.empty else 0)
    for index, row in df_analise.iterrows():
        if saldo_anterior > 0: # Evitar divisão por zero e analisar apenas se o saldo anterior era positivo
            variacao_percentual = (row[coluna_saldo_para_analise] - saldo_anterior) / saldo_anterior
            if variacao_percentual < LIMIAR_VARIACAO_NEGATIVA_GRANDE:
                alertas.append({
                    "data": row["data"].strftime("%Y-%m-%d"),
                    "tipo_risco": "Queda Brusca de Saldo",
                    "mensagem": f"Alerta: Queda de {(variacao_percentual*100):.2f}% no saldo para {row[coluna_saldo_para_analise]:.2f} em {row["data"].strftime("%Y-%m-%d")} (comparado a {saldo_anterior:.2f}).",
                    "nivel": "Médio"
                })
        saldo_anterior = row[coluna_saldo_para_analise]

    # 3. Risco de Dias Consecutivos com Fluxo Negativo (requer coluna de fluxo diário)
    # Esta análise é mais complexa se o df_previsoes só tem saldo. 
    # Precisaríamos do fluxo diário previsto.
    # Supondo que temos uma coluna "fluxo_diario_previsto"
    if "fluxo_diario_previsto" in df_analise.columns:
        dias_negativos_consecutivos = 0
        for index, row in df_analise.iterrows():
            if row["fluxo_diario_previsto"] < 0:
                dias_negativos_consecutivos += 1
            else:
                dias_negativos_consecutivos = 0 # Reseta a contagem
            
            if dias_negativos_consecutivos >= DIAS_CONSECUTIVOS_NEGATIVOS:
                # Evitar alertas repetidos para a mesma sequência
                if not any(a["tipo_risco"] == "Fluxo Negativo Persistente" and pd.to_datetime(a["data"]) >= (row["data"] - pd.Timedelta(days=DIAS_CONSECUTIVOS_NEGATIVOS-1)) for a in alertas):
                    alertas.append({
                        "data": row["data"].strftime("%Y-%m-%d"),
                        "tipo_risco": "Fluxo Negativo Persistente",
                        "mensagem": f"Alerta: {dias_negativos_consecutivos} dias consecutivos de fluxo de caixa negativo previsto terminando em {row["data"].strftime("%Y-%m-%d")}.",
                        "nivel": "Médio"
                    })
    else:
        print("Aviso: Coluna 'fluxo_diario_previsto' não encontrada para análise de fluxo negativo persistente.")

    # Remover duplicatas de alertas para o mesmo dia e tipo (simplificado)
    alertas_unicas_dict = {}
    for alerta in alertas:
        chave = (alerta["data"], alerta["tipo_risco"])
        if chave not in alertas_unicas_dict:
            alertas_unicas_dict[chave] = alerta
    
    alertas_finais = list(alertas_unicas_dict.values())
    alertas_finais.sort(key=lambda x: (x["data"], x["nivel"]))

    print(f"{len(alertas_finais)} alertas de risco identificados.")
    return alertas_finais

if __name__ == "__main__":
    # Exemplo de uso
    datas_previsao = pd.to_datetime(["2023-02-01", "2023-02-02", "2023-02-03", "2023-02-04", "2023-02-05", "2023-02-06"])
    saldos_previstos_exemplo = [1200, 900, 1100, 800, 700, 1300]
    fluxo_diario_exemplo = [200, -300, 200, -300, -100, 600] # Exemplo de fluxo diário

    df_previsoes_exemplo = pd.DataFrame({
        "data": datas_previsao,
        "saldo_previsto": saldos_previstos_exemplo,
        "fluxo_diario_previsto": fluxo_diario_exemplo
    })

    print("--- DataFrame de Previsões de Exemplo ---")
    print(df_previsoes_exemplo)

    saldo_inicial_para_analise = 1500.0
    alertas_identificados = identificar_riscos_com_base_em_limiares(df_previsoes_exemplo, saldo_inicial_para_analise)

    if alertas_identificados:
        print("\n--- Alertas de Risco Identificados ---")
        for alerta in alertas_identificados:
            print(f"- Data: {alerta['data']}, Tipo: {alerta['tipo_risco']}, Nível: {alerta['nivel']}, Mensagem: {alerta['mensagem']}")
    else:
        print("\nNenhum alerta de risco identificado com os dados de exemplo.")

    # Exemplo com saldo consistentemente baixo
    saldos_baixos_exemplo = [950, 850, 750, 650, 550, 450]
    df_previsoes_baixas = pd.DataFrame({
        "data": datas_previsao,
        "saldo_previsto": saldos_baixos_exemplo
    })
    print("\n--- Teste com Saldos Baixos ---")
    alertas_baixas = identificar_riscos_com_base_em_limiares(df_previsoes_baixas)
    if alertas_baixas:
        for alerta in alertas_baixas:
            print(f"- Data: {alerta['data']}, Tipo: {alerta['tipo_risco']}, Nível: {alerta['nivel']}, Mensagem: {alerta['mensagem']}")

