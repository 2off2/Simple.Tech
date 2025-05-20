import pandas as pd
from typing import Optional, Tuple

# Formato esperado do CSV (colunas obrigatórias e tipos esperados)
# - data (YYYY-MM-DD ou DD/MM/YYYY)
# - descricao (texto)
# - entrada (numérico, opcional, default 0)
# - saida (numérico, opcional, default 0)
# - saldo (numérico, opcional, calculado se não presente)
# - id_cliente (texto, opcional, para análise de inadimplência)
# - data_vencimento (YYYY-MM-DD ou DD/MM/YYYY, opcional, para inadimplência)
# - data_pagamento (YYYY-MM-DD ou DD/MM/YYYY, opcional, para inadimplência)
# - valor_fatura (numérico, opcional, para inadimplência)

def carregar_dados_csv(caminho_arquivo: str) -> Optional[pd.DataFrame]:
    """Carrega dados de um arquivo CSV, tentando detectar o formato da data."""
    try:
        # Tenta ler com formato de data padrão e separador vírgula
        df = pd.read_csv(caminho_arquivo, dayfirst=False, parse_dates=["data"], decimal=",")
        print(f"Arquivo {caminho_arquivo} carregado com sucesso (formato data padrão).")
    except (ValueError, TypeError):
        try:
            # Tenta ler com data no formato DD/MM/YYYY e separador ponto e vírgula
            df = pd.read_csv(caminho_arquivo, dayfirst=True, parse_dates=["data"], sep=";", decimal=",")
            print(f"Arquivo {caminho_arquivo} carregado com sucesso (formato data DD/MM/YYYY, sep=;).")
        except Exception as e_inner:
            print(f"Erro ao tentar carregar o arquivo CSV com diferentes formatos: {e_inner}")
            return None
    except FileNotFoundError:
        print(f"Erro: Arquivo {caminho_arquivo} não encontrado.")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar o arquivo CSV: {e}")
        return None
    return df

def validar_colunas_obrigatorias(df: pd.DataFrame) -> Tuple[bool, str]:
    """Valida se as colunas obrigatórias básicas existem no DataFrame."""
    colunas_obrigatorias_minimas = ["data", "descricao"]
    colunas_faltando = [col for col in colunas_obrigatorias_minimas if col not in df.columns]
    if colunas_faltando:
        return False, (f'Colunas obrigatórias faltando: {", ".join(colunas_faltando)}')
    return True, "Colunas obrigatórias presentes."

def limpar_e_transformar_dados(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Realiza a limpeza básica e transformação dos dados."""
    df_copia = df.copy()

    # Converter coluna 'data' para datetime (se não foi feito no carregamento)
    if not pd.api.types.is_datetime64_any_dtype(df_copia["data"]):
        try:
            df_copia["data"] = pd.to_datetime(df_copia["data"], dayfirst=True, errors="coerce")
        except Exception:
            try:
                df_copia["data"] = pd.to_datetime(df_copia["data"], dayfirst=False, errors="coerce")
            except Exception as e:
                print(f"Erro ao converter coluna 'data' para datetime: {e}")
                return None
    
    df_copia = df_copia.dropna(subset=["data"]) # Remove linhas onde a data não pôde ser convertida

    # Tratar colunas numéricas (entrada, saida, saldo, valor_fatura)
    colunas_numericas = ["entrada", "saida", "saldo", "valor_fatura"]
    for col in colunas_numericas:
        if col in df_copia.columns:
            if isinstance(df_copia[col].iloc[0], str): # Verifica se é string para tentar substituir vírgula
                 df_copia[col] = df_copia[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df_copia[col] = pd.to_numeric(df_copia[col], errors="coerce").fillna(0.0)
        elif col in ["entrada", "saida"]:
             df_copia[col] = 0.0 # Adiciona se não existir e for entrada/saida

    # Calcular saldo se não existir ou estiver incorreto (simplificado)
    if "saldo" not in df_copia.columns or df_copia["saldo"].sum() == 0:
        df_copia = df_copia.sort_values(by="data")
        df_copia["fluxo_diario"] = df_copia["entrada"] - df_copia["saida"]
        df_copia["saldo"] = df_copia["fluxo_diario"].cumsum()
    
    # Tratar colunas de data para inadimplência (se existirem)
    colunas_data_inadimplencia = ["data_vencimento", "data_pagamento"]
    for col in colunas_data_inadimplencia:
        if col in df_copia.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_copia[col]):
                try:
                    df_copia[col] = pd.to_datetime(df_copia[col], dayfirst=True, errors="coerce")
                except Exception:
                    df_copia[col] = pd.to_datetime(df_copia[col], dayfirst=False, errors="coerce")

    print("Limpeza e transformação de dados concluídas.")
    return df_copia

def processar_arquivo_completo(caminho_arquivo: str) -> Optional[pd.DataFrame]:
    """Função principal para carregar, validar e limpar dados de um CSV."""
    df = carregar_dados_csv(caminho_arquivo)
    if df is None:
        return None

    valido, msg_validacao = validar_colunas_obrigatorias(df)
    if not valido:
        print(f"Erro de validação: {msg_validacao}")
        return None
    
    df_limpo = limpar_e_transformar_dados(df)
    if df_limpo is None:
        print("Erro durante a limpeza e transformação dos dados.")
        return None
        
    print("Arquivo processado com sucesso.")
    return df_limpo


if __name__ == "__main__":
    # Exemplo de uso (crie um data/example.csv para testar)
    # Este caminho é relativo à raiz do projeto se você executar `python core/data_processing.py` de lá
    # ou relativo a `core/` se executar de dentro da pasta `core/`.
    # Para testes robustos, use caminhos absolutos ou fixtures em um framework de teste.
    caminho_exemplo = "C:/Users/23011372/Documents/Simple_Tech_2/RiskAI_PTI/data/example.csv" 

    dados_processados = processar_arquivo_completo(caminho_exemplo)

    if dados_processados is not None:
        print("\n--- Dados Processados (Head) ---")
        print(dados_processados.head())
        print("\n--- Tipos de Dados ---")
        print(dados_processados.dtypes)
        print("\n--- Informações do DataFrame ---")
        dados_processados.info()