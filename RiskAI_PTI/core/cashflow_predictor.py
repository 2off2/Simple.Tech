"""
Módulo para previsão de fluxo de caixa usando técnicas de machine learning
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CashflowPredictor:
    """Classe para previsão de fluxo de caixa"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0)
        }
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = None
        self.feature_names = None
        self.is_fitted = False
    
    def preparar_dados_para_regressao(self, df: pd.DataFrame, dias_para_prever: int = 7) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Prepara dados para treinamento do modelo de regressão
        
        Args:
            df: DataFrame com dados históricos
            dias_para_prever: Número de dias à frente para prever
            
        Returns:
            Tuple com features (X) e targets (y) ou None se erro
        """
        try:
            if len(df) < dias_para_prever + 10:  # Mínimo de dados necessários
                logger.error(f"dados insuficientes. Mínimo necessário: {dias_para_prever + 10}, disponível: {len(df)}")
                return None
            
            # Ordenar por data
            df_sorted = df.sort_values('data').reset_index(drop=True)
            
            # Gerar features e targets
            features_list = []
            targets_entrada = []
            targets_saida = []
            
            for i in range(len(df_sorted) - dias_para_prever):
                # Janela de features (dados históricos)
                window_start = max(0, i - 30)  # Usar até 30 dias de histórico
                window_data = df_sorted.iloc[window_start:i+1]
                
                if len(window_data) < 5:  # Mínimo de 5 dias de histórico
                    continue
                
                # Extrair features da janela
                features = self._extrair_features(window_data, df_sorted.iloc[i])
                features_list.append(features)
                
                # Target: soma dos próximos dias_para_prever dias
                target_window = df_sorted.iloc[i+1:i+1+dias_para_prever]
                targets_entrada.append(target_window['entrada'].sum())
                targets_saida.append(target_window['saida'].sum())
            
            if len(features_list) == 0:
                logger.error("Nenhuma amostra de treinamento gerada")
                return None
            
            X = np.array(features_list)
            y_entrada = np.array(targets_entrada)
            y_saida = np.array(targets_saida)
            
            # Combinar targets (entrada e saída)
            y = np.column_stack([y_entrada, y_saida])
            
            logger.info(f"Dados preparados: {X.shape[0]} amostras, {X.shape[1]} features")
            return X, y
            
        except Exception as e:
            logger.error(f"Erro ao preparar dados: {str(e)}")
            return None
    
    def _extrair_features(self, window_data: pd.DataFrame, current_row: pd.Series) -> List[float]:
        """Extrai features de uma janela de dados"""
        try:
            features = []
            
            # Features básicas de entrada e saída
            features.extend([
                window_data['entrada'].sum(),        # Total entradas no período
                window_data['saida'].sum(),          # Total saídas no período
                window_data['entrada'].mean(),       # Média entradas
                window_data['saida'].mean(),         # Média saídas
                window_data['entrada'].std() if len(window_data) > 1 else 0,  # Desvio padrão entradas
                window_data['saida'].std() if len(window_data) > 1 else 0,    # Desvio padrão saídas
                window_data['entrada'].max(),        # Máximo entrada
                window_data['saida'].max(),          # Máximo saída
                len(window_data[window_data['entrada'] > 0]),  # Dias com entrada
                len(window_data[window_data['saida'] > 0]),    # Dias com saída
            ])
            
            # Features de tendência
            if len(window_data) >= 7:
                entrada_recent = window_data['entrada'].tail(7).mean()
                entrada_older = window_data['entrada'].head(7).mean() if len(window_data) >= 14 else entrada_recent
                saida_recent = window_data['saida'].tail(7).mean()
                saida_older = window_data['saida'].head(7).mean() if len(window_data) >= 14 else saida_recent
                
                features.extend([
                    entrada_recent - entrada_older,  # Tendência entrada
                    saida_recent - saida_older,      # Tendência saída
                ])
            else:
                features.extend([0, 0])
            
            # Features temporais do dia atual
            current_date = current_row['data']
            features.extend([
                current_date.dayofweek,    # Dia da semana (0=segunda)
                current_date.day,          # Dia do mês
                current_date.month,        # Mês
                current_date.quarter,      # Trimestre
            ])
            
            # Features de médias móveis (se disponíveis)
            if 'entrada_ma7' in window_data.columns:
                features.extend([
                    window_data['entrada_ma7'].iloc[-1],
                    window_data['saida_ma7'].iloc[-1],
                    window_data['entrada_ma30'].iloc[-1],
                    window_data['saida_ma30'].iloc[-1],
                ])
            else:
                features.extend([0, 0, 0, 0])
            
            # Feature de saldo atual
            features.append(current_row['saldo'])
            
            # Features sazonais
            features.extend([
                np.sin(2 * np.pi * current_date.dayofyear / 365),  # Sazonalidade anual
                np.cos(2 * np.pi * current_date.dayofyear / 365),
                np.sin(2 * np.pi * current_date.dayofweek / 7),    # Sazonalidade semanal
                np.cos(2 * np.pi * current_date.dayofweek / 7),
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Erro ao extrair features: {str(e)}")
            return [0] * 25  # Retornar features zeradas em caso de erro
    
    def treinar_modelo_regressao(self, X: np.ndarray, y: np.ndarray, validacao_cruzada: bool = True):
        """
        Treina e seleciona o melhor modelo de regressão
        
        Args:
            X: Features de treinamento
            y: Targets de treinamento (entrada e saída)
            validacao_cruzada: Se deve usar validação cruzada para seleção
            
        Returns:
            Modelo treinado ou None se erro
        """
        try:
            if len(X) < 10:
                logger.error("Dados insuficientes para treinamento")
                return None
            
            # Dividir dados para treinamento e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=True
            )
            
            # Normalizar features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Treinar múltiplos modelos
            best_score = -np.inf
            best_model = None
            best_model_name = None
            model_scores = {}
            
            for name, model in self.models.items():
                try:
                    # Treinar modelo para cada target (entrada e saída)
                    model_entrada = type(model)(**model.get_params() if hasattr(model, 'get_params') else {})
                    model_saida = type(model)(**model.get_params() if hasattr(model, 'get_params') else {})
                    
                    # Treinar modelos separados para entrada e saída
                    model_entrada.fit(X_train_scaled, y_train[:, 0])  # Entrada
                    model_saida.fit(X_train_scaled, y_train[:, 1])    # Saída
                    
                    # Avaliar modelo
                    pred_entrada = model_entrada.predict(X_test_scaled)
                    pred_saida = model_saida.predict(X_test_scaled)
                    
                    # Calcular métricas
                    mae_entrada = mean_absolute_error(y_test[:, 0], pred_entrada)
                    mae_saida = mean_absolute_error(y_test[:, 1], pred_saida)
                    mae_total = (mae_entrada + mae_saida) / 2
                    
                    r2_entrada = r2_score(y_test[:, 0], pred_entrada)
                    r2_saida = r2_score(y_test[:, 1], pred_saida)
                    r2_total = (r2_entrada + r2_saida) / 2
                    
                    # Score combinado (R² é melhor quando maior, MAE é melhor quando menor)
                    score = r2_total - (mae_total / np.mean(np.abs(y_test)))
                    
                    model_scores[name] = {
                        'score': score,
                        'mae_total': mae_total,
                        'r2_total': r2_total,
                        'modelo_entrada': model_entrada,
                        'modelo_saida': model_saida
                    }
                    
                    if score > best_score:
                        best_score = score
                        best_model = {
                            'entrada': model_entrada,
                            'saida': model_saida
                        }
                        best_model_name = name
                    
                    logger.info(f"Modelo {name}: Score={score:.4f}, MAE={mae_total:.2f}, R²={r2_total:.4f}")
                    
                except Exception as model_error:
                    logger.warning(f"Erro ao treinar modelo {name}: {str(model_error)}")
                    continue
            
            if best_model is None:
                logger.error("Nenhum modelo foi treinado com sucesso")
                return None
            
            self.best_model = best_model
            self.best_model_name = best_model_name
            self.is_fitted = True
            
            logger.info(f"Melhor modelo selecionado: {best_model_name} (Score: {best_score:.4f})")
            return self.best_model
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo: {str(e)}")
            return None
    
    def gerar_previsao_com_regressao(self, modelo, df: pd.DataFrame, dias_a_prever: int = 30, 
                                   dias_para_target: int = 7) -> Optional[pd.DataFrame]:
        """
        Gera previsões usando o modelo treinado
        
        Args:
            modelo: Modelo treinado
            df: DataFrame com dados históricos
            dias_a_prever: Número de dias para prever
            dias_para_target: Janela de dias usada no treinamento
            
        Returns:
            DataFrame com previsões ou None se erro
        """
        try:
            if not self.is_fitted or modelo is None:
                logger.error("Modelo não está treinado")
                return None
            
            df_sorted = df.sort_values('data').reset_index(drop=True)
            
            # Preparar dados para previsão
            previsoes = []
            last_date = df_sorted['data'].max()
            
            # Usar uma janela deslizante para previsões sequenciais
            for dia in range(0, dias_a_prever, dias_para_target):
                # Data da previsão
                data_previsao = last_date + timedelta(days=dia+1)
                
                # Preparar features usando os dados históricos mais recentes
                window_data = df_sorted.tail(30)  # Usar últimos 30 dias
                
                # Criar uma linha fictícia para a data de previsão
                current_row = pd.Series({
                    'data': data_previsao,
                    'saldo': df_sorted['saldo'].iloc[-1],
                    'entrada': 0,
                    'saida': 0
                })
                
                # Extrair features
                features = self._extrair_features(window_data, current_row)
                X_pred = np.array([features])
                X_pred_scaled = self.scaler.transform(X_pred)
                
                # Fazer previsão
                pred_entrada = modelo['entrada'].predict(X_pred_scaled)[0]
                pred_saida = modelo['saida'].predict(X_pred_scaled)[0]
                
                # Garantir valores não negativos
                pred_entrada = max(0, pred_entrada)
                pred_saida = max(0, pred_saida)
                
                # Calcular saldo previsto
                saldo_anterior = df_sorted['saldo'].iloc[-1] if len(previsoes) == 0 else previsoes[-1]['saldo_previsto']
                saldo_previsto = saldo_anterior + pred_entrada - pred_saida
                
                # Adicionar previsões para cada dia do período
                dias_no_periodo = min(dias_para_target, dias_a_prever - dia)
                entrada_diaria = pred_entrada / dias_no_periodo
                saida_diaria = pred_saida / dias_no_periodo
                
                for d in range(dias_no_periodo):
                    data_dia = last_date + timedelta(days=dia + d + 1)
                    saldo_dia = saldo_anterior + (entrada_diaria - saida_diaria) * (d + 1)
                    
                    previsoes.append({
                        'data': data_dia,
                        'entrada_prevista': entrada_diaria,
                        'saida_prevista': saida_diaria,
                        'saldo_previsto': saldo_dia,
                        'confianca': self._calcular_confianca(dia + d)
                    })
            
            df_previsoes = pd.DataFrame(previsoes[:dias_a_prever])
            
            # Adicionar intervalos de confiança
            df_previsoes = self._adicionar_intervalos_confianca(df_previsoes, df_sorted)
            
            logger.info(f"Geradas {len(df_previsoes)} previsões")
            return df_previsoes
            
        except Exception as e:
            logger.error(f"Erro ao gerar previsões: {str(e)}")
            return None
    
    def _calcular_confianca(self, dias_futuro: int) -> float:
        """Calcula nível de confiança baseado na distância temporal"""
        # Confiança diminui com o tempo
        confianca_base = 0.95
        decaimento = 0.02
        return max(0.5, confianca_base - (dias_futuro * decaimento))
    
    def _adicionar_intervalos_confianca(self, df_previsoes: pd.DataFrame, df_historico: pd.DataFrame) -> pd.DataFrame:
        """Adiciona intervalos de confiança às previsões"""
        try:
            # Calcular volatilidade histórica
            volatilidade_entrada = df_historico['entrada'].std()
            volatilidade_saida = df_historico['saida'].std()
            
            # Adicionar intervalos (95% de confiança ~ 1.96 * desvio padrão)
            df_previsoes['entrada_min'] = df_previsoes['entrada_prevista'] - (1.96 * volatilidade_entrada * (1 - df_previsoes['confianca']))
            df_previsoes['entrada_max'] = df_previsoes['entrada_prevista'] + (1.96 * volatilidade_entrada * (1 - df_previsoes['confianca']))
            df_previsoes['saida_min'] = df_previsoes['saida_prevista'] - (1.96 * volatilidade_saida * (1 - df_previsoes['confianca']))
            df_previsoes['saida_max'] = df_previsoes['saida_prevista'] + (1.96 * volatilidade_saida * (1 - df_previsoes['confianca']))
            
            # Garantir valores não negativos
            df_previsoes['entrada_min'] = df_previsoes['entrada_min'].clip(lower=0)
            df_previsoes['saida_min'] = df_previsoes['saida_min'].clip(lower=0)
            
            return df_previsoes
            
        except Exception as e:
            logger.warning(f"Erro ao calcular intervalos de confiança: {str(e)}")
            return df_previsoes
    
    def avaliar_modelo(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Avalia o desempenho do modelo treinado"""
        try:
            if not self.is_fitted or self.best_model is None:
                return {}
            
            X_test_scaled = self.scaler.transform(X_test)
            
            # Previsões
            pred_entrada = self.best_model['entrada'].predict(X_test_scaled)
            pred_saida = self.best_model['saida'].predict(X_test_scaled)
            
            # Métricas para entrada
            mae_entrada = mean_absolute_error(y_test[:, 0], pred_entrada)
            rmse_entrada = np.sqrt(mean_squared_error(y_test[:, 0], pred_entrada))
            r2_entrada = r2_score(y_test[:, 0], pred_entrada)
            
            # Métricas para saída
            mae_saida = mean_absolute_error(y_test[:, 1], pred_saida)
            rmse_saida = np.sqrt(mean_squared_error(y_test[:, 1], pred_saida))
            r2_saida = r2_score(y_test[:, 1], pred_saida)
            
            return {
                'modelo_usado': self.best_model_name,
                'mae_entrada': mae_entrada,
                'rmse_entrada': rmse_entrada,
                'r2_entrada': r2_entrada,
                'mae_saida': mae_saida,
                'rmse_saida': rmse_saida,
                'r2_saida': r2_saida,
                'mae_total': (mae_entrada + mae_saida) / 2,
                'r2_total': (r2_entrada + r2_saida) / 2
            }
            
        except Exception as e:
            logger.error(f"Erro ao avaliar modelo: {str(e)}")
            return {}
    
    def prever_com_cenarios(self, df: pd.DataFrame, dias_a_prever: int = 30, 
                          cenarios: Dict[str, float] = None) -> Dict[str, pd.DataFrame]:
        """
        Gera previsões para diferentes cenários
        
        Args:
            df: DataFrame histórico
            dias_a_prever: Dias para prever
            cenarios: Dict com fatores multiplicativos para entrada/saída {'otimista': 1.2, 'pessimista': 0.8}
            
        Returns:
            Dict com DataFrames de previsão para cada cenário
        """
        try:
            if cenarios is None:
                cenarios = {
                    'base': 1.0,
                    'otimista': 1.2,
                    'pessimista': 0.8,
                    'conservador': 0.9
                }
            
            resultados = {}
            
            # Gerar previsão base
            previsao_base = self.gerar_previsao_com_regressao(
                self.best_model, df, dias_a_prever
            )
            
            if previsao_base is None:
                return {}
            
            # Aplicar cenários
            for nome_cenario, fator in cenarios.items():
                df_cenario = previsao_base.copy()
                
                if nome_cenario == 'base':
                    resultados[nome_cenario] = df_cenario
                    continue
                
                # Ajustar previsões baseado no cenário
                if fator > 1.0:  # Cenário otimista
                    df_cenario['entrada_prevista'] *= fator
                    df_cenario['saida_prevista'] *= (2 - fator)  # Reduzir saídas
                else:  # Cenário pessimista
                    df_cenario['entrada_prevista'] *= fator
                    df_cenario['saida_prevista'] *= (2 - fator)  # Aumentar saídas
                
                # Recalcular saldo
                saldo_inicial = df['saldo'].iloc[-1]
                df_cenario['saldo_previsto'] = saldo_inicial + (
                    df_cenario['entrada_prevista'] - df_cenario['saida_prevista']
                ).cumsum()
                
                # Ajustar confiança
                df_cenario['confianca'] *= 0.9  # Reduzir confiança em cenários alternativos
                
                resultados[nome_cenario] = df_cenario
            
            return resultados
            
        except Exception as e:
            logger.error(f"Erro ao gerar cenários: {str(e)}")
            return {}
    
    def salvar_modelo(self, caminho: str) -> bool:
        """Salva o modelo treinado"""
        try:
            import pickle
            
            if not self.is_fitted:
                logger.error("Modelo não está treinado")
                return False
            
            modelo_data = {
                'best_model': self.best_model,
                'best_model_name': self.best_model_name,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'is_fitted': self.is_fitted
            }
            
            with open(caminho, 'wb') as f:
                pickle.dump(modelo_data, f)
            
            logger.info(f"Modelo salvo em: {caminho}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {str(e)}")
            return False
    
    def carregar_modelo(self, caminho: str) -> bool:
        """Carrega modelo previamente salvo"""
        try:
            import pickle
            
            with open(caminho, 'rb') as f:
                modelo_data = pickle.load(f)
            
            self.best_model = modelo_data['best_model']
            self.best_model_name = modelo_data['best_model_name']
            self.scaler = modelo_data['scaler']
            self.feature_names = modelo_data.get('feature_names')
            self.is_fitted = modelo_data['is_fitted']
            
            logger.info(f"Modelo carregado de: {caminho}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {str(e)}")
            return False

class CashflowAnalyzer:
    """Classe para análise complementar do fluxo de caixa"""
    
    @staticmethod
    def detectar_sazonalidade(df: pd.DataFrame) -> Dict[str, Any]:
        """Detecta padrões sazonais nos dados"""
        try:
            from scipy import stats
            
            # Agrupar por dia da semana
            por_dia_semana = df.groupby(df['data'].dt.dayofweek).agg({
                'entrada': 'mean',
                'saida': 'mean'
            })
            
            # Agrupar por mês
            por_mes = df.groupby(df['data'].dt.month).agg({
                'entrada': 'mean',
                'saida': 'mean'
            })
            
            # Teste de variância (ANOVA)
            dias_semana_grupos = [df[df['data'].dt.dayofweek == i]['entrada'].values 
                                for i in range(7) if len(df[df['data'].dt.dayofweek == i]) > 0]
            
            f_stat_semana, p_val_semana = stats.f_oneway(*dias_semana_grupos) if len(dias_semana_grupos) > 1 else (0, 1)
            
            return {
                'sazonalidade_semanal': {
                    'significativa': p_val_semana < 0.05,
                    'p_valor': p_val_semana,
                    'por_dia': por_dia_semana.to_dict()
                },
                'sazonalidade_mensal': {
                    'por_mes': por_mes.to_dict()
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar sazonalidade: {str(e)}")
            return {}
    
    @staticmethod
    def identificar_tendencias(df: pd.DataFrame, janela_dias: int = 30) -> Dict[str, Any]:
        """Identifica tendências nos dados"""
        try:
            # Calcular médias móveis
            df_sorted = df.sort_values('data').copy()
            df_sorted['entrada_ma'] = df_sorted['entrada'].rolling(window=janela_dias, min_periods=1).mean()
            df_sorted['saida_ma'] = df_sorted['saida'].rolling(window=janela_dias, min_periods=1).mean()
            df_sorted['saldo_ma'] = df_sorted['saldo'].rolling(window=janela_dias, min_periods=1).mean()
            
            # Calcular tendências (regressão linear)
            from scipy.stats import linregress
            
            x = np.arange(len(df_sorted))
            
            # Tendência das entradas
            slope_entrada, intercept_entrada, r_entrada, p_entrada, _ = linregress(x, df_sorted['entrada_ma'])
            
            # Tendência das saídas
            slope_saida, intercept_saida, r_saida, p_saida, _ = linregress(x, df_sorted['saida_ma'])
            
            # Tendência do saldo
            slope_saldo, intercept_saldo, r_saldo, p_saldo, _ = linregress(x, df_sorted['saldo_ma'])
            
            return {
                'entrada': {
                    'tendencia_diaria': slope_entrada,
                    'correlacao': r_entrada,
                    'significativa': p_entrada < 0.05,
                    'direcao': 'crescente' if slope_entrada > 0 else 'decrescente'
                },
                'saida': {
                    'tendencia_diaria': slope_saida,
                    'correlacao': r_saida,
                    'significativa': p_saida < 0.05,
                    'direcao': 'crescente' if slope_saida > 0 else 'decrescente'
                },
                'saldo': {
                    'tendencia_diaria': slope_saldo,
                    'correlacao': r_saldo,
                    'significativa': p_saldo < 0.05,
                    'direcao': 'crescente' if slope_saldo > 0 else 'decrescente'
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao identificar tendências: {str(e)}")
            return {}

# Instâncias globais
cashflow_predictor = CashflowPredictor()
cashflow_analyzer = CashflowAnalyzer()