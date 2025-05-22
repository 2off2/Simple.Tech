import pandas as pd
from typing import Optional, Tuple
from pandas.api.types import is_datetime64_any_dtype

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
    def processar_datas(df_copia):
        colunas_data = ["data_vencimento", "data_pagamento"]
        for col in colunas_data:
            if col in df_copia.columns:
                # Verifica se já é datetime
                if is_datetime64_any_dtype(df_copia[col]):
                    continue
                
                # Tenta converter com formato explícito YYYY-MM-DD
                df_copia[col] = pd.to_datetime(
                    df_copia[col],
                    format="%Y-%m-%d",
                    errors="coerce"
                )
                
                # Se falhar (todos NaT), tenta outros formatos com fallback
                if df_copia[col].isna().all():
                    df_copia[col] = pd.to_datetime(
                        df_copia[col],
                        dayfirst=True,  # Para formatos DD/MM/YYYY
                        errors="coerce"
                    )
        
        print("Limpeza e transformação de dados concluídas.")
        return df_copia

def processar_arquivo_completo(caminho_arquivo):
    """
    Processa o arquivo CSV completo, realizando todas as etapas necessárias.
    
    Args:
        caminho_arquivo (str): Caminho para o arquivo CSV
        
    Returns:
        DataFrame: DataFrame processado ou None em caso de erro
    """
    try:
        # Tentar ler o arquivo CSV
        try:
            print("Tentando ler o arquivo CSV:", caminho_arquivo)
            df = pd.read_csv(caminho_arquivo)
            print(f"Arquivo CSV lido com sucesso, colunas: {df.columns.tolist()}")
        except Exception as e:
            erro_msg = f"Erro ao ler o arquivo CSV: {str(e)}"
            print(erro_msg)
            raise Exception(erro_msg)
        
        # Verificar colunas obrigatórias
        print("Verificando colunas obrigatórias")
        colunas_obrigatorias = ['data', 'descricao', 'id_cliente']
        colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltantes:
            erro_msg = f"Colunas obrigatórias ausentes: {', '.join(colunas_faltantes)}"
            print(erro_msg)
            raise Exception(erro_msg)
        
        # Verificar colunas recomendadas
        print("Verificando colunas recomendadas")
        colunas_recomendadas = ['entrada', 'saida']
        for col in colunas_recomendadas:
            if col not in df.columns:
                print(f"Coluna recomendada ausente: {col}, adicionando com valor padrão 0.0")
                df[col] = 0.0  # Valor padrão se a coluna não existir
        
        # Processar as datas
        try:
            print("Processando coluna de data")
            df['data'] = pd.to_datetime(df['data'])
            print("Coluna de data processada com sucesso")
        except Exception as e:
            erro_msg = f"Erro ao converter coluna 'data': {str(e)}"
            print(erro_msg)
            raise Exception(erro_msg)
        
        # Processar colunas opcionais de data
        print("Processando colunas opcionais de data")
        for col in ['data_vencimento', 'data_pagamento']:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    print(f"Coluna {col} processada com sucesso")
                except Exception as e:
                    print(f"Aviso: Erro ao converter coluna '{col}': {str(e)}")
                    # Não falhar por causa de colunas opcionais
        
        # Processar valores numéricos
        print("Processando valores numéricos")
        for col in ['entrada', 'saida', 'valor_fatura']:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].fillna(0)
                    print(f"Coluna {col} processada com sucesso")
                except Exception as e:
                    print(f"Aviso: Erro ao converter coluna '{col}': {str(e)}")
        
        # Ordenar por data
        print("Ordenando por data")
        df = df.sort_values('data')
        
        print("Processamento concluído com sucesso")
        return df
        
    except Exception as e:
        # Capturar e propagar a exceção com mensagem clara
        erro_msg = str(e) if str(e) else "Erro desconhecido ao processar o arquivo"
        print(f"Erro no processamento: {erro_msg}")
        # Propagar a exceção para ser capturada pelo endpoint
        raise Exception(erro_msg)

# Inicializar o atributo de erro
processar_arquivo_completo.last_error = ""



if __name__ == "__main__":
    # Exemplo de uso (crie um data/example.csv para testar)
    # Este caminho é relativo à raiz do projeto se você executar `python core/data_processing.py` de lá
    # ou relativo a `core/` se executar de dentro da pasta `core/`.
    # Para testes robustos, use caminhos absolutos ou fixtures em um framework de teste.
    caminho_exemplo = "c:/Users/hp/Documents/Simple.Tech/RiskAI_PTI/data/example.csv" 

    dados_processados = processar_arquivo_completo(caminho_exemplo)

    if dados_processados is not None:
        print("\n--- Dados Processados (Head) ---")
        print(dados_processados.head())
        print("\n--- Tipos de Dados ---")
        print(dados_processados.dtypes)
        print("\n--- Informações do DataFrame ---")
        dados_processados.info()