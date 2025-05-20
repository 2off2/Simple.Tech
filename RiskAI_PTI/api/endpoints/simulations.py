from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from typing import Dict, Any, Optional
import sys

# Adiciona o diretório raiz ao path para que o Python possa encontrar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar módulos do core
from core import scenario_simulator

# Importar o estado compartilhado
from api.endpoints import state

# Definir o router
router = APIRouter()

# Definir os modelos de request/response
class ScenarioParams(BaseModel):
    variacao_entrada: float = 0.10
    variacao_saida: float = 0.10
    dias_simulacao: int = 30
    num_simulacoes: int = 100
    saldo_inicial_simulacao: Optional[float] = None

class ScenarioResponse(BaseModel):
    results_summary: Dict[str, Any]
    # full_simulation_data: Optional[List[Dict[str, Any]]] = None # Pode ser muito grande

@router.post("/scenarios", response_model=ScenarioResponse)
async def simulate_scenarios(params: ScenarioParams):
    if state.global_processed_df is None or state.global_historical_stats is None:
        raise HTTPException(status_code=400, detail="Dados não carregados ou estatísticas não calculadas. Faça upload de um arquivo CSV primeiro.")

    try:
        # Gerar parâmetros para simulação
        parametros_sim = scenario_simulator.gerar_parametros_simulacao(
            state.global_historical_stats,
            variacao_entrada=params.variacao_entrada,
            variacao_saida=params.variacao_saida,
            dias_simulacao=params.dias_simulacao,
            num_simulacoes=params.num_simulacoes,
            saldo_inicial=params.saldo_inicial_simulacao # Pode ser None para usar o último saldo histórico
        )
        
        # Executar simulação
        df_resultados_sim, _ = scenario_simulator.executar_simulacao_monte_carlo(parametros_sim)
        
        # Analisar probabilidades dos resultados da simulação
        analise_prob = scenario_simulator.analisar_probabilidades(df_resultados_sim)
        
        return ScenarioResponse(results_summary=analise_prob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao executar simulação: {str(e)}")