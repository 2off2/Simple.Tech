from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import os
from typing import List, Optional, Dict, Any

# Importar módulos do core (ajuste o caminho conforme a estrutura do seu projeto)
# Isso assume que a raiz do projeto está no PYTHONPATH ou que você está usando um ambiente virtual
# configurado corretamente.
import sys
# Adiciona o diretório pai (raiz do projeto) ao sys.path
# Isso assume que main.py está em api/ e a pasta core/ está na raiz do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import data_processing, cashflow_predictor, risk_analyzer, scenario_simulator, customer_analysis

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="RiskAI API",
    description="API para análise de risco financeiro, previsão de fluxo de caixa e simulação de cenários.",
    version="0.1.0"
)

# --- Diretório para Uploads Temporários ---
UPLOAD_DIR = "data/api_uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- Modelos Pydantic para Request/Response ---
class FileUploadResponse(BaseModel):
    filename: str
    message: str
    file_path: Optional[str] = None
    error: Optional[str] = None

class PredictionParams(BaseModel):
    days_to_predict: int = 30
    # Parâmetros adicionais para o modelo de previsão, se necessário

class PredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

class ScenarioParams(BaseModel):
    variacao_entrada: float = 0.10
    variacao_saida: float = 0.10
    dias_simulacao: int = 30
    num_simulacoes: int = 100
    saldo_inicial_simulacao: Optional[float] = None

class ScenarioResponse(BaseModel):
    results_summary: Dict[str, Any]
    # full_simulation_data: Optional[List[Dict[str, Any]]] = None # Pode ser muito grande

class CustomerAnalysisResponse(BaseModel):
    report: Dict[str, Any]
    segmented_customers: Optional[List[Dict[str, Any]]] = None

# --- Variáveis Globais / Estado (Simples - Para MVP) ---
# Em produção, considere um banco de dados ou um sistema de gerenciamento de estado mais robusto.
global_processed_df: Optional[pd.DataFrame] = None
global_prediction_model: Any = None # Armazenar o modelo treinado
global_historical_stats: Optional[Dict[str, Any]] = None

# --- Endpoints da API ---

@app.get("/", tags=["Health Check"])
async def health_check():
    return {"message": "RiskAI API está funcionando!"}

# --- Endpoints de Gerenciamento de Dados (data.py) ---
@app.post("/data/upload_csv", response_model=FileUploadResponse, tags=["Data Management"])
async def upload_csv_file(file: UploadFile = File(...) ):
    global global_processed_df, global_prediction_model, global_historical_stats
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Processar o arquivo carregado
        df = data_processing.processar_arquivo_completo(file_path)
        if df is None:
            raise HTTPException(status_code=400, detail="Erro ao processar o arquivo CSV. Verifique o formato e o conteúdo.")
        
        global_processed_df = df
        global_prediction_model = None # Resetar modelo se novos dados forem carregados
        global_historical_stats = scenario_simulator.calcular_estatisticas_historicas(global_processed_df)

        return FileUploadResponse(
            filename=file.filename, 
            message="Arquivo CSV carregado e processado com sucesso.",
            file_path=file_path
        )
    except HTTPException as http_exc:
        return FileUploadResponse(filename=file.filename, message="Erro HTTP", error=str(http_exc.detail ))
    except Exception as e:
        return FileUploadResponse(filename=file.filename, message="Erro interno do servidor", error=str(e))

@app.get("/data/view_processed", tags=["Data Management"])
async def view_processed_data(limit: int = 5):
    global global_processed_df
    if global_processed_df is None:
        raise HTTPException(status_code=404, detail="Nenhum dado processado disponível. Faça upload de um arquivo primeiro.")
    return JSONResponse(content=global_processed_df.head(limit).to_dict(orient="records"))

# --- Endpoints de Previsão (predictions.py) ---
@app.post("/predict/cashflow", response_model=PredictionResponse, tags=["Predictions & Alerts"])
async def predict_cashflow(params: PredictionParams):
    global global_processed_df, global_prediction_model
    if global_processed_df is None:
        raise HTTPException(status_code=400, detail="Dados não carregados. Faça upload de um arquivo CSV primeiro.")

    try:
        # Treinar modelo se ainda não foi treinado com os dados atuais
        # Esta é uma simplificação; o treinamento pode ser demorado e deve ser gerenciado com cuidado.
        if global_prediction_model is None:
            dias_para_target_modelo = 7 # Exemplo: modelo treinado para prever 7 dias à frente
            dados_treino = cashflow_predictor.preparar_dados_para_regressao(global_processed_df, dias_para_prever=dias_para_target_modelo)
            if dados_treino:
                X_features, y_target = dados_treino
                global_prediction_model = cashflow_predictor.treinar_modelo_regressao(X_features, y_target)
            else:
                raise HTTPException(status_code=500, detail="Falha ao preparar dados para treinamento do modelo.")
        
        if global_prediction_model is None:
             raise HTTPException(status_code=500, detail="Modelo de previsão não pôde ser treinado.")

        # Gerar previsões
        df_previsoes = cashflow_predictor.gerar_previsao_com_regressao(
            global_prediction_model, 
            global_processed_df, 
            dias_a_prever=params.days_to_predict,
            dias_para_target=7 # Deve corresponder ao usado no treino
        )
        if df_previsoes is None or df_previsoes.empty:
            raise HTTPException(status_code=500, detail="Falha ao gerar previsões de fluxo de caixa.")

        # Analisar riscos nas previsões
        saldo_inicial_real = global_processed_df["saldo"].iloc[-1] if not global_processed_df.empty else 0
        alertas = risk_analyzer.identificar_riscos_com_base_em_limiares(df_previsoes, saldo_inicial_real)
        
        return PredictionResponse(
            predictions=df_previsoes.to_dict(orient="records"),
            alerts=alertas
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao gerar previsão: {str(e )}")

# --- Endpoints de Simulação (simulations.py) ---
@app.post("/simulate/scenarios", response_model=ScenarioResponse, tags=["Simulations"])
async def simulate_scenarios(params: ScenarioParams):
    global global_processed_df, global_historical_stats
    if global_processed_df is None or global_historical_stats is None:
        raise HTTPException(status_code=400, detail="Dados não carregados ou estatísticas não calculadas. Faça upload de um arquivo CSV primeiro.")

    try:
        # Gerar parâmetros para simulação
        parametros_sim = scenario_simulator.gerar_parametros_simulacao(
            global_historical_stats,
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

# --- Endpoints de Análise de Clientes (customer_analysis.py) ---
@app.get("/analyze/customer_delinquency", response_model=CustomerAnalysisResponse, tags=["Customer Analysis"])
async def analyze_customer_delinquency():
    global global_processed_df
    if global_processed_df is None:
        raise HTTPException(status_code=400, detail="Dados não carregados. Faça upload de um arquivo CSV primeiro.")
    
    # Verificar se as colunas necessárias para análise de inadimplência existem
    colunas_necessarias = ["id_cliente", "data_vencimento", "valor_fatura"]
    if not all(col in global_processed_df.columns for col in colunas_necessarias):
        raise HTTPException(status_code=400, detail=f"Dados insuficientes para análise de inadimplência. Colunas necessárias: {", ".join(colunas_necessarias)}.")

    try:
        df_com_atraso = customer_analysis.calcular_dias_atraso(global_processed_df)
        df_segmentado = customer_analysis.segmentar_clientes_por_risco_inadimplencia(df_com_atraso)
        relatorio_inadimplencia = customer_analysis.gerar_relatorio_inadimplencia(df_segmentado)
        
        return CustomerAnalysisResponse(
            report=relatorio_inadimplencia,
            segmented_customers=df_segmentado.to_dict(orient="records") if df_segmentado is not None else []
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao analisar inadimplência: {str(e)}")

# --- Para executar a API (exemplo com Uvicorn) ---
# No terminal, na raiz do projeto: uvicorn api.main:app --reload
# Ou configure o VSCode para executar com Uvicorn.

if __name__ == "__main__":
    import uvicorn
    # Este bloco é útil para desenvolvimento, mas em produção, use um servidor ASGI como Uvicorn diretamente.
    print("Iniciando servidor Uvicorn para RiskAI API em http://127.0.0.1:8000" )
    print("Acesse a documentação interativa em http://127.0.0.1:8000/docs" )
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)