"""
Módulo para análise de riscos financeiros e identificação de alertas
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """Classe para análise de riscos financeiros"""
    
    def __init__(self):
        self.risk_thresholds = {
            'saldo_critico': 0,
            'saldo_alerta': 1000,
            'volatilidade_alta': 2.0,
            'concentracao_cliente': 0.7,
            'dias_sem_entrada': 7,
            'queda_receita': 0.3,
            'aumento_despesa': 0.5
        }
    
    def identificar_riscos_com_base_em_limiares(self, df_previsoes: pd.DataFrame, 
                                              saldo_inicial: float) -> List[Dict[str, Any]]:
        """
        Identifica riscos baseado em limiares predefinidos
        
        Args:
            df_previsoes: DataFrame com previsões
            saldo_inicial: Saldo atual/inicial
            
        Returns:
            Lista de alertas de risco
        """
        alertas = []
        
        try:
            if df_previsoes.empty:
                return alertas
            
            # 1. Risco de saldo negativo
            alertas.extend(self._detectar_saldo_negativo(df_previsoes))
            
            # 2. Risco de saldo crítico
            alertas.extend(self._detectar_saldo_critico(df_previsoes))
            
            # 3. Risco de queda acentuada
            alertas.extend(self._detectar_queda_acentuada(df_previsoes, saldo_inicial))
            
            # 4. Risco de volatilidade alta
            alertas.extend(self._detectar_alta_volatilidade(df_previsoes))
            
            # 5. Risco de tendência negativa
            alertas.extend(self._detectar_tendencia_negativa(df_previsoes))
            
            # Ordenar alertas por severidade
            severidade_ordem = {'critica': 0, 'alta': 1, 'media': 2, 'baixa': 3}
            alertas.sort(key=lambda x: severidade_ordem.get(x.get('severidade', 'baixa'), 3))
            
            logger.info(f"Identificados {len(alertas)} alertas de risco")
            return alertas
            
        except Exception as e:
            logger.error(f"Erro ao identificar riscos: {str(e)}")
            return []
    
    def _detectar_saldo_negativo(self, df_previsoes: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detecta quando o saldo ficará negativo"""
        alertas = []
        
        try:
            saldos_negativos = df_previsoes[df_previsoes['saldo_previsto'] < 0]
            
            if not saldos_negativos.empty:
                primeiro_negativo = saldos_negativos.iloc[0]
                valor_negativo = primeiro_negativo['saldo_previsto']
                
                alertas.append({
                    'tipo': 'saldo_negativo',
                    'severidade': 'critica',
                    'data_ocorrencia': primeiro_negativo['data'].strftime('%Y-%m-%d'),
                    'valor': float(valor_negativo),
                    'dias_ate_ocorrencia': (primeiro_negativo['data'] - datetime.now().date()).days,
                    'mensagem': f"Saldo ficará negativo em {primeiro_negativo['data'].strftime('%d/%m/%Y')} (R$ {valor_negativo:.2f})",
                    'recomendacao': "Revisar fluxo de caixa imediatamente e considerar medidas de contenção de despesas ou aumento de receitas",
                    'impacto_financeiro': abs(float(valor_negativo))
                })
                
                # Alertas adicionais para saldos muito negativos
                saldo_min = saldos_negativos['saldo_previsto'].min()
                if saldo_min < valor_negativo * 2:
                    alertas.append({
                        'tipo': 'saldo_critico_negativo',
                        'severidade': 'critica',
                        'data_ocorrencia': saldos_negativos[saldos_negativos['saldo_previsto'] == saldo_min].iloc[0]['data'].strftime('%Y-%m-%d'),
                        'valor': float(saldo_min),
                        'mensagem': f"Saldo atingirá valor crítico de R$ {saldo_min:.2f}",
                        'recomendacao': "Situação crítica - considerar empréstimos emergenciais ou venda de ativos",
                        'impacto_financeiro': abs(float(saldo_min))
                    })
            
        except Exception as e:
            logger.error(f"Erro ao detectar saldo negativo: {str(e)}")
        
        return alertas
    
    def _detectar_saldo_critico(self, df_previsoes: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detecta quando o saldo está próximo do crítico"""
        alertas = []
        
        try:
            limite_critico = self.risk_thresholds['saldo_critico']
            limite_alerta = self.risk_thresholds['saldo_alerta']
            
            # Saldo abaixo do limite de alerta
            saldos_alerta = df_previsoes[
                (df_previsoes['saldo_previsto'] > limite_critico) & 
                (df_previsoes['saldo_previsto'] < limite_alerta)
            ]
            
            if not saldos_alerta.empty:
                primeiro_alerta = saldos_alerta.iloc[0]
                
                alertas.append({
                    'tipo': 'saldo_baixo',
                    'severidade': 'alta',
                    'data_ocorrencia': primeiro_alerta['data'].strftime('%Y-%m-%d'),
                    'valor': float(primeiro_alerta['saldo_previsto']),
                    'dias_ate_ocorrencia': (primeiro_alerta['data'] - datetime.now().date()).days,
                    'mensagem': f"Saldo baixo previsto: R$ {primeiro_alerta['saldo_previsto']:.2f} em {primeiro_alerta['data'].strftime('%d/%m/%Y')}",
                    'recomendacao': "Monitorar fluxo de caixa de perto e preparar plano de contingência",
                    'impacto_financeiro': float(limite_alerta - primeiro_alerta['saldo_previsto'])
                })
            
        except Exception as e:
            logger.error(f"Erro ao detectar saldo crítico: {str(e)}")
        
        return alertas
    
    def _detectar_queda_acentuada(self, df_previsoes: pd.DataFrame, saldo_inicial: float) -> List[Dict[str, Any]]:
        """Detecta quedas acentuadas no saldo"""
        alertas = []
        
        try:
            if len(df_previsoes) == 0 or saldo_inicial <= 0:
                return alertas
            
            saldo_final = df_previsoes['saldo_previsto'].iloc[-1]
            percentual_queda = (saldo_inicial - saldo_final) / saldo_inicial
            
            limite_queda = self.risk_thresholds['queda_receita']
            
            if percentual_queda > limite_queda:
                severidade = 'critica' if percentual_queda > 0.5 else 'alta'
                
                alertas.append({
                    'tipo': 'queda_acentuada',
                    'severidade': severidade,
                    'data_ocorrencia': df_previsoes['data'].iloc[-1].strftime('%Y-%m-%d'),
                    'valor': float(saldo_final),
                    'percentual_queda': float(percentual_queda * 100),
                    'mensagem': f"Queda acentuada de {percentual_queda*100:.1f}% no saldo prevista até {df_previsoes['data'].iloc[-1].strftime('%d/%m/%Y')}",
                    'recomendacao': "Analisar causas da queda e implementar medidas corretivas urgentes",
                    'impacto_financeiro': float(saldo_inicial - saldo_final)
                })
            
        except Exception as e:
            logger.error(f"Erro ao detectar queda acentuada: {str(e)}")
        
        return alertas
    
    def _detectar_alta_volatilidade(self, df_previsoes: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detecta alta volatilidade nas previsões"""
        alertas = []
        
        try:
            if len(df_previsoes) < 7:
                return alertas
            
            # Calcular volatilidade do saldo previsto
            volatilidade_saldo = df_previsoes['saldo_previsto'].rolling(window=7).std().mean()
            media_saldo = df_previsoes['saldo_previsto'].mean()
            
            if media_saldo > 0:
                cv_saldo = volatilidade_saldo / media_saldo  # Coeficiente de variação
                
                if cv_saldo > self.risk_thresholds['volatilidade_alta']:
                    alertas.append({
                        'tipo': 'alta_volatilidade',
                        'severidade': 'media',
                        'data_ocorrencia': df_previsoes['data'].iloc[-1].strftime('%Y-%m-%d'),
                        'valor': float(cv_saldo),
                        'mensagem': f"Alta volatilidade detectada no fluxo de caixa (CV: {cv_saldo:.2f})",
                        'recomendacao': "Considerar estratégias de estabilização do fluxo de caixa",
                        'impacto_financeiro': float(volatilidade_saldo)
                    })
            
        except Exception as e:
            logger.error(f"Erro ao detectar alta volatilidade: {str(e)}")
        
        return alertas
    
    def _detectar_tendencia_negativa(self, df_previsoes: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detecta tendência negativa persistente"""
        alertas = []
        
        try:
            if len(df_previsoes) < 5:
                return alertas
            
            # Calcular tendência usando regressão linear
            x = np.arange(len(df_previsoes))
            y = df_previsoes['saldo_previsto'].values
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Se a tendência é significativamente negativa
            if slope < 0 and p_value < 0.05 and abs(r_value) > 0.7:
                projecao_30_dias = slope * 30
                
                alertas.append({
                    'tipo': 'tendencia_negativa',
                    'severidade': 'alta' if slope < -100 else 'media',
                    'data_ocorrencia': df_previsoes['data'].iloc[-1].strftime('%Y-%m-%d'),
                    'valor': float(slope),
                    'correlacao': float(r_value),
                    'projecao_30_dias': float(projecao_30_dias),
                    'mensagem': f"Tendência negativa detectada: queda de R$ {abs(slope):.2f} por dia",
                    'recomendacao': "Investigar causas da tendência negativa e implementar ações corretivas",
                    'impacto_financeiro': abs(float(projecao_30_dias))
                })
            
        except Exception as e:
            logger.error(f"Erro ao detectar tendência negativa: {str(e)}")
        
        return alertas
    
    def analisar_riscos_historicos(self, df_historico: pd.DataFrame) -> Dict[str, Any]:
        """
        Analisa riscos baseado em dados históricos
        
        Args:
            df_historico: DataFrame com dados históricos
            
        Returns:
            Dict com análise de riscos históricos
        """
        try:
            if df_historico.empty:
                return {}
            
            analise = {
                'periodo_analise': {
                    'data_inicio': df_historico['data'].min().strftime('%Y-%m-%d'),
                    'data_fim': df_historico['data'].max().strftime('%Y-%m-%d'),
                    'dias_total': len(df_historico)
                },
                'volatilidade': self._calcular_volatilidade_historica(df_historico),
                'estresse': self._analisar_periodos_estresse(df_historico),
                'concentracao': self._analisar_concentracao_riscos(df_historico),
                'liquidez': self._analisar_liquidez(df_historico),
                'score_risco': 0
            }
            
            # Calcular score de risco geral
            analise['score_risco'] = self._calcular_score_risco(analise)
            
            return analise
            
        except Exception as e:
            logger.error(f"Erro ao analisar riscos históricos: {str(e)}")
            return {}
    
    def _calcular_volatilidade_historica(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas de volatilidade histórica"""
        try:
            # Agrupar por dia para calcular fluxo diário
            df_diario = df.groupby('data').agg({
                'entrada': 'sum',
                'saida': 'sum',
                'saldo': 'last'
            }).reset_index()
            
            # Calcular variações diárias
            df_diario['fluxo_liquido'] = df_diario['entrada'] - df_diario['saida']
            df_diario['variacao_saldo'] = df_diario['saldo'].diff()
            
            return {
                'desvio_padrao_entrada': float(df_diario['entrada'].std()),
                'desvio_padrao_saida': float(df_diario['saida'].std()),
                'desvio_padrao_fluxo': float(df_diario['fluxo_liquido'].std()),
                'coeficiente_variacao_entrada': float(df_diario['entrada'].std() / df_diario['entrada'].mean()) if df_diario['entrada'].mean() > 0 else 0,
                'coeficiente_variacao_saida': float(df_diario['saida'].std() / df_diario['saida'].mean()) if df_diario['saida'].mean() > 0 else 0,
                'volatilidade_saldo': float(df_diario['variacao_saldo'].std()),
                'range_saldo': float(df_diario['saldo'].max() - df_diario['saldo'].min()),
                'classificacao': self._classificar_volatilidade(df_diario['fluxo_liquido'].std(), df_diario['fluxo_liquido'].mean())
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular volatilidade: {str(e)}")
            return {}
    
    def _classificar_volatilidade(self, std_fluxo: float, media_fluxo: float) -> str:
        """Classifica o nível de volatilidade"""
        if media_fluxo == 0:
            return 'indefinida'
        
        cv = abs(std_fluxo / media_fluxo)
        
        if cv < 0.5:
            return 'baixa'
        elif cv < 1.0:
            return 'moderada'
        elif cv < 2.0:
            return 'alta'
        else:
            return 'muito_alta'
    
    def _analisar_periodos_estresse(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa períodos de estresse financeiro"""
        try:
            # Identificar períodos com saldo baixo ou negativo
            saldos_negativos = df[df['saldo'] < 0]
            saldos_baixos = df[(df['saldo'] >= 0) & (df['saldo'] < self.risk_thresholds['saldo_alerta'])]
            
            # Períodos consecutivos de estresse
            df_sorted = df.sort_values('data')
            df_sorted['estresse'] = (df_sorted['saldo'] < self.risk_thresholds['saldo_alerta']).astype(int)
            df_sorted['grupo_estresse'] = (df_sorted['estresse'] != df_sorted['estresse'].shift()).cumsum()
            
            periodos_estresse = df_sorted[df_sorted['estresse'] == 1].groupby('grupo_estresse').agg({
                'data': ['min', 'max', 'count'],
                'saldo': 'min'
            }).reset_index()
            
            periodos_estresse.columns = ['grupo', 'data_inicio', 'data_fim', 'duracao', 'saldo_minimo']
            
            return {
                'total_dias_negativos': len(saldos_negativos),
                'total_dias_baixos': len(saldos_baixos),
                'percentual_tempo_estresse': float(len(saldos_baixos) / len(df) * 100) if len(df) > 0 else 0,
                'pior_saldo': float(df['saldo'].min()),
                'data_pior_saldo': df.loc[df['saldo'].idxmin(), 'data'].strftime('%Y-%m-%d') if not df.empty else None,
                'num_periodos_estresse': len(periodos_estresse) if not periodos_estresse.empty else 0,
                'periodo_estresse_mais_longo': int(periodos_estresse['duracao'].max()) if not periodos_estresse.empty else 0,
                'recuperacao_media': self._calcular_tempo_recuperacao(df)
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar períodos de estresse: {str(e)}")
            return {}
    
    def _calcular_tempo_recuperacao(self, df: pd.DataFrame) -> float:
        """Calcula tempo médio de recuperação após períodos de estresse"""
        try:
            df_sorted = df.sort_values('data')
            tempos_recuperacao = []
            
            em_estresse = False
            inicio_estresse = None
            
            for idx, row in df_sorted.iterrows():
                if row['saldo'] < self.risk_thresholds['saldo_alerta'] and not em_estresse:
                    em_estresse = True
                    inicio_estresse = row['data']
                elif row['saldo'] >= self.risk_thresholds['saldo_alerta'] and em_estresse:
                    em_estresse = False
                    if inicio_estresse:
                        tempo_recuperacao = (row['data'] - inicio_estresse).days
                        tempos_recuperacao.append(tempo_recuperacao)
            
            return float(np.mean(tempos_recuperacao)) if tempos_recuperacao else 0
            
        except Exception as e:
            logger.error(f"Erro ao calcular tempo de recuperação: {str(e)}")
            return 0
    
    def _analisar_concentracao_riscos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa concentração de riscos por cliente ou categoria"""
        try:
            concentracao = {}
            
            # Concentração por cliente (se disponível)
            if 'id_cliente' in df.columns:
                receitas_por_cliente = df.groupby('id_cliente')['entrada'].sum().sort_values(ascending=False)
                total_receitas = receitas_por_cliente.sum()
                
                if total_receitas > 0:
                    # Top 3 clientes
                    top3_clientes = receitas_por_cliente.head(3)
                    concentracao_top3 = top3_clientes.sum() / total_receitas
                    
                    concentracao['clientes'] = {
                        'total_clientes': len(receitas_por_cliente),
                        'concentracao_top1': float(receitas_por_cliente.iloc[0] / total_receitas) if len(receitas_por_cliente) > 0 else 0,
                        'concentracao_top3': float(concentracao_top3),
                        'indice_herfindahl': float(((receitas_por_cliente / total_receitas) ** 2).sum()),
                        'risco_concentracao': 'alto' if concentracao_top3 > self.risk_thresholds['concentracao_cliente'] else 'baixo'
                    }
            
            # Concentração por categoria (se disponível)
            if 'categoria_auto' in df.columns:
                receitas_por_categoria = df.groupby('categoria_auto')['entrada'].sum()
                total_receitas_cat = receitas_por_categoria.sum()
                
                if total_receitas_cat > 0:
                    concentracao['categorias'] = {
                        'principal_categoria': receitas_por_categoria.idxmax(),
                        'concentracao_principal': float(receitas_por_categoria.max() / total_receitas_cat),
                        'num_categorias': len(receitas_por_categoria),
                        'distribuicao': receitas_por_categoria.to_dict()
                    }
            
            return concentracao
            
        except Exception as e:
            logger.error(f"Erro ao analisar concentração: {str(e)}")
            return {}
    
    def _analisar_liquidez(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analisa indicadores de liquidez"""
        try:
            df_sorted = df.sort_values('data')
            
            # Calcular médias móveis
            df_sorted['entrada_ma7'] = df_sorted['entrada'].rolling(window=7, min_periods=1).mean()
            df_sorted['saida_ma7'] = df_sorted['saida'].rolling(window=7, min_periods=1).mean()
            
            # Dias sem entrada
            dias_sem_entrada = 0
            max_dias_sem_entrada = 0
            
            for entrada in df_sorted['entrada']:
                if entrada == 0:
                    dias_sem_entrada += 1
                    max_dias_sem_entrada = max(max_dias_sem_entrada, dias_sem_entrada)
                else:
                    dias_sem_entrada = 0
            
            # Índice de liquidez atual
            entrada_recente = df_sorted['entrada'].tail(7).sum()
            saida_recente = df_sorted['saida'].tail(7).sum()
            indice_liquidez = entrada_recente / saida_recente if saida_recente > 0 else float('inf')
            
            return {
                'indice_liquidez_7dias': float(indice_liquidez),
                'max_dias_sem_entrada': max_dias_sem_entrada,
                'media_entrada_semanal': float(df_sorted['entrada_ma7'].iloc[-1]) if not df_sorted.empty else 0,
                'media_saida_semanal': float(df_sorted['saida_ma7'].iloc[-1]) if not df_sorted.empty else 0,
                'classificacao_liquidez': self._classificar_liquidez(indice_liquidez, max_dias_sem_entrada),
                'buffer_dias': self._calcular_buffer_dias(df_sorted)
            }
            
        except Exception as e:
            logger.error(f"Erro ao analisar liquidez: {str(e)}")
            return {}
    
    def _classificar_liquidez(self, indice_liquidez: float, max_dias_sem_entrada: int) -> str:
        """Classifica o nível de liquidez"""
        if max_dias_sem_entrada > self.risk_thresholds['dias_sem_entrada']:
            return 'baixa'
        elif indice_liquidez < 0.8:
            return 'baixa'
        elif indice_liquidez < 1.2:
            return 'moderada'
        else:
            return 'alta'
    
    def _calcular_buffer_dias(self, df_sorted: pd.DataFrame) -> float:
        """Calcula quantos dias a empresa pode operar com o saldo atual"""
        try:
            saldo_atual = df_sorted['saldo'].iloc[-1]
            saida_media_diaria = df_sorted['saida'].tail(30).mean()
            
            if saida_media_diaria > 0 and saldo_atual > 0:
                return float(saldo_atual / saida_media_diaria)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Erro ao calcular buffer: {str(e)}")
            return 0
    
    def _calcular_score_risco(self, analise: Dict[str, Any]) -> float:
        """Calcula score geral de risco (0-100, onde 100 é risco máximo)"""
        try:
            score = 0
            
            # Volatilidade (0-30 pontos)
            volatilidade = analise.get('volatilidade', {})
            if volatilidade.get('classificacao') == 'muito_alta':
                score += 30
            elif volatilidade.get('classificacao') == 'alta':
                score += 20
            elif volatilidade.get('classificacao') == 'moderada':
                score += 10
            
            # Estresse (0-25 pontos)
            estresse = analise.get('estresse', {})
            percentual_estresse = estresse.get('percentual_tempo_estresse', 0)
            score += min(25, percentual_estresse * 0.5)
            
            # Concentração (0-20 pontos)
            concentracao = analise.get('concentracao', {})
            if concentracao.get('clientes', {}).get('risco_concentracao') == 'alto':
                score += 20
            elif concentracao.get('clientes', {}).get('concentracao_top1', 0) > 0.5:
                score += 10
            
            # Liquidez (0-25 pontos)
            liquidez = analise.get('liquidez', {})
            if liquidez.get('classificacao_liquidez') == 'baixa':
                score += 25
            elif liquidez.get('classificacao_liquidez') == 'moderada':
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Erro ao calcular score de risco: {str(e)}")
            return 50  # Score médio em caso de erro
    
    def gerar_recomendacoes(self, alertas: List[Dict[str, Any]], 
                           analise_historica: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera recomendações based nos riscos identificados"""
        try:
            recomendacoes = []
            
            # Recomendações baseadas em alertas críticos
            alertas_criticos = [a for a in alertas if a.get('severidade') == 'critica']
            
            if alertas_criticos:
                recomendacoes.append({
                    'tipo': 'acao_imediata',
                    'prioridade': 'alta',
                    'titulo': 'Ação Imediata Necessária',
                    'descricao': 'Foram identificados riscos críticos que requerem atenção imediata.',
                    'acoes': [
                        'Revisar todas as contas a receber e acelerar cobranças',
                        'Negociar prazos de pagamento com fornecedores',
                        'Considerar linhas de crédito emergenciais',
                        'Reduzir despesas não essenciais imediatamente'
                    ]
                })
            
            # Recomendações baseadas na análise histórica
            score_risco = analise_historica.get('score_risco', 0)
            
            if score_risco > 70:
                recomendacoes.append({
                    'tipo': 'gestao_risco',
                    'prioridade': 'alta',
                    'titulo': 'Implementar Gestão de Riscos',
                    'descricao': 'Score de risco elevado indica necessidade de melhor gestão.',
                    'acoes': [
                        'Implementar controles de fluxo de caixa diários',
                        'Diversificar base de clientes e receitas',
                        'Criar reserva de emergência',
                        'Estabelecer limites de gastos por categoria'
                    ]
                })
            
            # Recomendações baseadas em concentração
            concentracao = analise_historica.get('concentracao', {})
            if concentracao.get('clientes', {}).get('risco_concentracao') == 'alto':
                recomendacoes.append({
                    'tipo': 'diversificacao',
                    'prioridade': 'media',
                    'titulo': 'Diversificar Base de Clientes',
                    'descricao': 'Alta concentração de receitas em poucos clientes.',
                    'acoes': [
                        'Desenvolver estratégias de aquisição de novos clientes',
                        'Reduzir dependência dos principais clientes',
                        'Criar contratos com múltiplos clientes menores',
                        'Implementar programa de fidelização'
                    ]
                })
            
            # Recomendações baseadas em liquidez
            liquidez = analise_historica.get('liquidez', {})
            if liquidez.get('classificacao_liquidez') == 'baixa':
                recomendacoes.append({
                    'tipo': 'liquidez',
                    'prioridade': 'media',
                    'titulo': 'Melhorar Liquidez',
                    'descricao': 'Indicadores de liquidez estão abaixo do ideal.',
                    'acoes': [
                        'Acelerar processo de cobrança',
                        'Revisar prazos de pagamento a clientes',
                        'Manter reserva mínima de caixa',
                        'Considerar factoring para recebíveis'
                    ]
                })
            
            return recomendacoes
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {str(e)}")
            return []

class RiskMonitor:
    """Classe para monitoramento contínuo de riscos"""
    
    def __init__(self):
        self.risk_analyzer = RiskAnalyzer()
        self.alertas_ativos = []
        self.historico_alertas = []
    
    def monitorar_riscos_tempo_real(self, df_atual: pd.DataFrame, 
                                   df_previsoes: pd.DataFrame) -> Dict[str, Any]:
        """Monitora riscos em tempo real"""
        try:
            # Analisar riscos atuais
            alertas_atuais = self.risk_analyzer.identificar_riscos_com_base_em_limiares(
                df_previsoes, df_atual['saldo'].iloc[-1] if not df_atual.empty else 0
            )
            
            # Atualizar alertas ativos
            self._atualizar_alertas_ativos(alertas_atuais)
            
            # Análise histórica
            analise_historica = self.risk_analyzer.analisar_riscos_historicos(df_atual)
            
            # Gerar dashboard de risco
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'status_geral': self._determinar_status_geral(alertas_atuais, analise_historica),
                'alertas_ativos': len(self.alertas_ativos),
                'alertas_criticos': len([a for a in alertas_atuais if a.get('severidade') == 'critica']),
                'score_risco': analise_historica.get('score_risco', 0),
                'tendencia_risco': self._calcular_tendencia_risco(),
                'proximas_acoes': self._definir_proximas_acoes(alertas_atuais)
            }
            
            return {
                'dashboard': dashboard,
                'alertas': alertas_atuais,
                'analise_historica': analise_historica,
                'recomendacoes': self.risk_analyzer.gerar_recomendacoes(alertas_atuais, analise_historica)
            }
            
        except Exception as e:
            logger.error(f"Erro no monitoramento de riscos: {str(e)}")
            return {}
    
    def _atualizar_alertas_ativos(self, novos_alertas: List[Dict[str, Any]]):
        """Atualiza lista de alertas ativos"""
        # Mover alertas antigos para histórico
        self.historico_alertas.extend(self.alertas_ativos)
        
        # Atualizar alertas ativos
        self.alertas_ativos = novos_alertas
        
        # Manter apenas últimos 1000 alertas no histórico
        if len(self.historico_alertas) > 1000:
            self.historico_alertas = self.historico_alertas[-1000:]
    
    def _determinar_status_geral(self, alertas: List[Dict[str, Any]], 
                                analise: Dict[str, Any]) -> str:
        """Determina status geral de risco"""
        alertas_criticos = [a for a in alertas if a.get('severidade') == 'critica']
        score_risco = analise.get('score_risco', 0)
        
        if alertas_criticos or score_risco > 80:
            return 'critico'
        elif score_risco > 60:
            return 'alto'
        elif score_risco > 40:
            return 'medio'
        else:
            return 'baixo'
    
    def _calcular_tendencia_risco(self) -> str:
        """Calcula tendência de risco baseada no histórico"""
        if len(self.historico_alertas) < 2:
            return 'estavel'
        
        # Comparar últimos alertas
        alertas_recentes = self.historico_alertas[-10:]
        alertas_anteriores = self.historico_alertas[-20:-10] if len(self.historico_alertas) >= 20 else []
        
        if not alertas_anteriores:
            return 'estavel'
        
        criticos_recentes = len([a for a in alertas_recentes if a.get('severidade') == 'critica'])
        criticos_anteriores = len([a for a in alertas_anteriores if a.get('severidade') == 'critica'])
        
        if criticos_recentes > criticos_anteriores:
            return 'crescente'
        elif criticos_recentes < criticos_anteriores:
            return 'decrescente'
        else:
            return 'estavel'
    
    def _definir_proximas_acoes(self, alertas: List[Dict[str, Any]]) -> List[str]:
        """Define próximas ações baseadas nos alertas"""
        acoes = []
        
        alertas_criticos = [a for a in alertas if a.get('severidade') == 'critica']
        
        if alertas_criticos:
            acoes.append("Revisar fluxo de caixa imediatamente")
            acoes.append("Contatar gerente bancário para linhas de crédito")
        
        if any(a.get('tipo') == 'saldo_negativo' for a in alertas):
            acoes.append("Implementar plano de contingência financeira")
        
        if any(a.get('tipo') == 'alta_volatilidade' for a in alertas):
            acoes.append("Analisar causas da volatilidade")
        
        return acoes[:5]  # Máximo 5 ações

# Instâncias globais
risk_analyzer = RiskAnalyzer()
risk_monitor = RiskMonitor()