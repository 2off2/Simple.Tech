"""
Módulo para processamento e validação de dados financeiros
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import re
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    """Classe para processamento de dados financeiros"""
    
    def __init__(self):
        self.last_error = None
        self.required_columns = ['data', 'descricao', 'entrada', 'saida']
        self.optional_columns = ['id_cliente', 'categoria', 'subcategoria']
    
    def processar_arquivo_completo(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Processa um arquivo CSV completo e retorna DataFrame limpo e validado
        
        Args:
            file_path (str): Caminho para o arquivo CSV
            
        Returns:
            pd.DataFrame ou None: DataFrame processado ou None em caso de erro
        """
        try:
            # Verificar se o arquivo existe
            if not Path(file_path).exists():
                self.last_error = f"Arquivo não encontrado: {file_path}"
                logger.error(self.last_error)
                return None
            
            # Ler arquivo CSV com diferentes encodings
            df = self._ler_csv_com_encoding(file_path)
            if df is None:
                return None
            
            # Validar estrutura básica
            if not self._validar_estrutura(df):
                return None
            
            # Limpar e padronizar dados
            df = self._limpar_dados(df)
            if df is None:
                return None
            
            # Validar dados financeiros
            if not self._validar_dados_financeiros(df):
                return None
            
            # Calcular campos derivados
            df = self._calcular_campos_derivados(df)
            
            # Ordenar por data
            df = df.sort_values('data').reset_index(drop=True)
            
            logger.info(f"Arquivo processado com sucesso: {len(df)} registros válidos")
            return df
            
        except Exception as e:
            self.last_error = f"Erro inesperado ao processar arquivo: {str(e)}"
            logger.error(self.last_error)
            return None
    
    def _ler_csv_com_encoding(self, file_path: str) -> Optional[pd.DataFrame]:
        """Tenta ler CSV com diferentes encodings"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                    if len(df.columns) >= len(self.required_columns):
                        logger.info(f"Arquivo lido com encoding {encoding} e separador '{sep}'")
                        return df
                except Exception as e:
                    continue
        
        self.last_error = "Não foi possível ler o arquivo CSV com os encodings e separadores testados"
        logger.error(self.last_error)
        return None
    
    def _validar_estrutura(self, df: pd.DataFrame) -> bool:
        """Valida se o DataFrame tem as colunas necessárias"""
        try:
            # Limpar nomes das colunas
            df.columns = df.columns.str.strip().str.lower()
            
            # Mapear possíveis variações de nomes de colunas
            column_mapping = {
                'date': 'data',
                'dt': 'data',
                'dt_transacao': 'data',
                'data_transacao': 'data',
                'description': 'descricao',
                'desc': 'descricao',
                'historico': 'descricao',
                'credit': 'entrada',
                'credito': 'entrada',
                'receita': 'entrada',
                'valor_entrada': 'entrada',
                'debit': 'saida',
                'debito': 'saida',
                'despesa': 'saida',
                'valor_saida': 'saida',
                'cliente': 'id_cliente',
                'client_id': 'id_cliente',
                'customer_id': 'id_cliente'
            }
            
            # Renomear colunas baseado no mapeamento
            df.rename(columns=column_mapping, inplace=True)
            
            # Verificar colunas obrigatórias
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            
            if missing_columns:
                self.last_error = f"Colunas obrigatórias ausentes: {missing_columns}. Colunas disponíveis: {list(df.columns)}"
                logger.error(self.last_error)
                return False
            
            return True
            
        except Exception as e:
            self.last_error = f"Erro ao validar estrutura: {str(e)}"
            logger.error(self.last_error)
            return False
    
    def _limpar_dados(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Limpa e padroniza os dados"""
        try:
            df_clean = df.copy()
            
            # Limpar coluna de data
            df_clean['data'] = self._limpar_datas(df_clean['data'])
            if df_clean['data'].isna().all():
                self.last_error = "Nenhuma data válida encontrada no arquivo"
                return None
            
            # Limpar valores financeiros
            df_clean['entrada'] = self._limpar_valores_financeiros(df_clean['entrada'])
            df_clean['saida'] = self._limpar_valores_financeiros(df_clean['saida'])
            
            # Limpar descrições
            df_clean['descricao'] = df_clean['descricao'].astype(str).str.strip()
            df_clean['descricao'] = df_clean['descricao'].replace(['nan', 'NaN', ''], 'Transação sem descrição')
            
            # Remover linhas com dados críticos ausentes
            df_clean = df_clean.dropna(subset=['data'])
            
            # Remover duplicatas exatas
            df_clean = df_clean.drop_duplicates().reset_index(drop=True)
            
            return df_clean
            
        except Exception as e:
            self.last_error = f"Erro ao limpar dados: {str(e)}"
            logger.error(self.last_error)
            return None
    
    def _limpar_datas(self, serie_datas: pd.Series) -> pd.Series:
        """Limpa e converte datas para formato padrão"""
        try:
            # Tentar diferentes formatos de data
            formatos_data = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%Y/%m/%d',
                '%d.%m.%Y'
            ]
            
            datas_convertidas = pd.Series(index=serie_datas.index, dtype='datetime64[ns]')
            
            for formato in formatos_data:
                mask_na = datas_convertidas.isna()
                if not mask_na.any():
                    break
                
                try:
                    datas_temp = pd.to_datetime(serie_datas[mask_na], format=formato, errors='coerce')
                    datas_convertidas[mask_na] = datas_temp
                except:
                    continue
            
            # Tentar conversão automática para dados restantes
            mask_na = datas_convertidas.isna()
            if mask_na.any():
                datas_auto = pd.to_datetime(serie_datas[mask_na], errors='coerce', dayfirst=True)
                datas_convertidas[mask_na] = datas_auto
            
            return datas_convertidas
            
        except Exception as e:
            logger.warning(f"Erro ao processar datas: {str(e)}")
            return pd.to_datetime(serie_datas, errors='coerce')
    
    def _limpar_valores_financeiros(self, serie_valores: pd.Series) -> pd.Series:
        """Limpa e converte valores financeiros"""
        try:
            # Converter para string para limpeza
            valores_str = serie_valores.astype(str)
            
            # Remover caracteres não numéricos (exceto pontos, vírgulas e sinais)
            valores_str = valores_str.str.replace(r'[^\d.,-]', '', regex=True)
            
            # Tratar vírgulas como separadores decimais (padrão brasileiro)
            valores_str = valores_str.str.replace(',', '.')
            
            # Converter para numérico
            valores_numericos = pd.to_numeric(valores_str, errors='coerce')
            
            # Substituir NaN por 0
            valores_numericos = valores_numericos.fillna(0)
            
            # Garantir valores não negativos (usar abs para entradas/saídas)
            valores_numericos = valores_numericos.abs()
            
            return valores_numericos
            
        except Exception as e:
            logger.warning(f"Erro ao processar valores financeiros: {str(e)}")
            return pd.to_numeric(serie_valores, errors='coerce').fillna(0).abs()
    
    def _validar_dados_financeiros(self, df: pd.DataFrame) -> bool:
        """Valida a consistência dos dados financeiros"""
        try:
            # Verificar se há pelo menos uma transação com valor > 0
            if (df['entrada'].sum() + df['saida'].sum()) == 0:
                self.last_error = "Nenhuma transação financeira válida encontrada"
                return False
            
            # Verificar datas dentro de um range razoável
            data_min = df['data'].min()
            data_max = df['data'].max()
            
            if pd.isna(data_min) or pd.isna(data_max):
                self.last_error = "Datas inválidas encontradas"
                return False
            
            # Verificar se as datas não são muito antigas ou futuras
            hoje = datetime.now()
            if data_max > hoje + timedelta(days=365):
                logger.warning("Encontradas datas muito no futuro")
            
            if data_min < datetime(1900, 1, 1):
                logger.warning("Encontradas datas muito antigas")
            
            return True
            
        except Exception as e:
            self.last_error = f"Erro na validação financeira: {str(e)}"
            logger.error(self.last_error)
            return False
    
    def _calcular_campos_derivados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula campos derivados como saldo acumulado"""
        try:
            df_calc = df.copy()
            
            # Calcular saldo acumulado
            df_calc['saldo'] = (df_calc['entrada'] - df_calc['saida']).cumsum()
            
            # Adicionar informações temporais
            df_calc['ano'] = df_calc['data'].dt.year
            df_calc['mes'] = df_calc['data'].dt.month
            df_calc['dia_semana'] = df_calc['data'].dt.dayofweek
            df_calc['dia_mes'] = df_calc['data'].dt.day
            
            # Calcular médias móveis (7 e 30 dias)
            df_calc = df_calc.sort_values('data')
            df_calc['entrada_ma7'] = df_calc['entrada'].rolling(window=7, min_periods=1).mean()
            df_calc['saida_ma7'] = df_calc['saida'].rolling(window=7, min_periods=1).mean()
            df_calc['entrada_ma30'] = df_calc['entrada'].rolling(window=30, min_periods=1).mean()
            df_calc['saida_ma30'] = df_calc['saida'].rolling(window=30, min_periods=1).mean()
            
            # Adicionar flags de categorização automática
            df_calc = self._categorizar_transacoes(df_calc)
            
            return df_calc
            
        except Exception as e:
            logger.error(f"Erro ao calcular campos derivados: {str(e)}")
            return df
    
    def _categorizar_transacoes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categoriza transações automaticamente baseado na descrição"""
        try:
            df_cat = df.copy()
            
            # Dicionário de palavras-chave para categorização
            categorias = {
                'alimentacao': ['restaurante', 'lanchonete', 'mercado', 'supermercado', 'padaria', 'alimentacao', 'comida'],
                'transporte': ['uber', 'taxi', 'combustivel', 'posto', 'transporte', 'onibus', 'metro'],
                'saude': ['farmacia', 'hospital', 'medico', 'clinica', 'saude', 'remedio'],
                'educacao': ['escola', 'faculdade', 'curso', 'livro', 'educacao'],
                'lazer': ['cinema', 'teatro', 'bar', 'festa', 'lazer', 'entretenimento'],
                'salario': ['salario', 'pagamento', 'remuneracao', 'vencimento'],
                'vendas': ['venda', 'receita', 'faturamento', 'cliente']
            }
            
            # Inicializar coluna de categoria
            df_cat['categoria_auto'] = 'outros'
            
            # Aplicar categorização
            for categoria, palavras in categorias.items():
                for palavra in palavras:
                    mask = df_cat['descricao'].str.lower().str.contains(palavra, na=False)
                    df_cat.loc[mask, 'categoria_auto'] = categoria
            
            return df_cat
            
        except Exception as e:
            logger.warning(f"Erro na categorização automática: {str(e)}")
            return df
    
    def gerar_relatorio_qualidade(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera relatório de qualidade dos dados processados"""
        try:
            relatorio = {
                'total_registros': len(df),
                'periodo': {
                    'data_inicio': df['data'].min().strftime('%Y-%m-%d') if not df.empty else None,
                    'data_fim': df['data'].max().strftime('%Y-%m-%d') if not df.empty else None,
                    'dias_periodo': (df['data'].max() - df['data'].min()).days if not df.empty else 0
                },
                'valores': {
                    'total_entradas': float(df['entrada'].sum()),
                    'total_saidas': float(df['saida'].sum()),
                    'saldo_final': float(df['saldo'].iloc[-1]) if not df.empty else 0,
                    'maior_entrada': float(df['entrada'].max()),
                    'maior_saida': float(df['saida'].max())
                },
                'estatisticas': {
                    'media_entrada_diaria': float(df.groupby('data')['entrada'].sum().mean()),
                    'media_saida_diaria': float(df.groupby('data')['saida'].sum().mean()),
                    'dias_com_transacoes': df['data'].nunique(),
                    'transacoes_por_dia': float(len(df) / df['data'].nunique()) if df['data'].nunique() > 0 else 0
                },
                'qualidade': {
                    'registros_com_descricao': int((df['descricao'] != 'Transação sem descrição').sum()),
                    'registros_sem_valor': int(((df['entrada'] == 0) & (df['saida'] == 0)).sum()),
                    'duplicatas_potenciais': int(df.duplicated(subset=['data', 'entrada', 'saida']).sum())
                }
            }
            
            if 'categoria_auto' in df.columns:
                relatorio['categorias'] = df['categoria_auto'].value_counts().to_dict()
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de qualidade: {str(e)}")
            return {}

# Instância global para uso nos endpoints
data_processing = DataProcessor()