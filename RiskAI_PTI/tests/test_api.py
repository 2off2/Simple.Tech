# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
import os
import sys
import pandas as pd

# Adicionar o diretório raiz do projeto ao sys.path para permitir importações da API
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Tentar importar a app FastAPI. Se api/main.py não existir ou tiver erros, isso falhará.
try:
    from api.main import app # Assumindo que sua app FastAPI está em api/main.py
except ImportError as e:
    print(f"Erro ao importar app FastAPI de api.main: {e}")
    print("Certifique-se de que api/main.py existe e não contém erros de importação.")
    # Definir app como None para que os testes que dependem dela possam ser pulados
    app = None 

# --- Fixture para o TestClient ---
@pytest.fixture(scope="module")
def client():
    if app is None:
        pytest.skip("Aplicação FastAPI não pôde ser importada, pulando testes da API.")
    # Criar o diretório de uploads se não existir, para evitar erros no endpoint de upload
    upload_dir = "data/api_uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    with TestClient(app) as c:
        yield c

# --- Testes para os Endpoints da API ---

def test_health_check(client):
    """Testa o endpoint de health check ("/")."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "RiskAI API está funcionando!"}

@pytest.fixture
def sample_csv_file_path():
    """Cria um arquivo CSV temporário para testes de upload e retorna o caminho."""
    # Usar o diretório de uploads da API para consistência
    upload_dir = "data/api_uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    file_path = os.path.join(upload_dir, "test_upload_data.csv")
    data = {
        "data": ["2023-01-01", "2023-01-02"],
        "descricao": ["Venda Teste 1", "Pagamento Teste 1"],
        "entrada": [100.0, 0.0],
        "saida": [0.0, 50.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    yield file_path # Fornece o caminho para o teste
    # Limpeza: remover o arquivo após o teste
    if os.path.exists(file_path):
        os.remove(file_path)

def test_upload_csv_file_success(client, sample_csv_file_path):
    """Testa o upload bem-sucedido de um arquivo CSV."""
    with open(sample_csv_file_path, "rb") as f:
        response = client.post("/data/upload_csv", files={"file": ("test_upload_data.csv", f, "text/csv")})
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["filename"] == "test_upload_data.csv"
    assert "Arquivo CSV carregado e processado com sucesso" in json_response["message"]
    assert json_response["file_path"] is not None

def test_upload_csv_file_invalid_format(client):
    """Testa o upload de um arquivo com formato inválido (ex: txt)."""
    # Criar um arquivo de texto simples
    invalid_file_content = b"Este nao e um CSV valido."
    response = client.post("/data/upload_csv", files={"file": ("invalid.txt", invalid_file_content, "text/plain")})
    
    # A API pode retornar 200 com uma mensagem de erro no JSON, ou um 4xx dependendo da implementação.
    # O exemplo em api/main.py retorna 200 com um erro no JSON se o processamento falhar.
    assert response.status_code == 200 
    json_response = response.json()
    assert "error" in json_response
    assert "Erro ao processar o arquivo CSV" in json_response["error"] or "Falha ao ler o arquivo CSV" in json_response["error"]

def test_view_processed_data_no_data(client):
    """Testa a visualização de dados processados quando nenhum dado foi carregado."""
    # Resetar o estado global da API (se possível, ou garantir que está limpo)
    # No exemplo atual, não há um endpoint de reset, então este teste pode depender do estado de testes anteriores.
    # Para isolamento, seria melhor ter um setup/teardown que limpa global_processed_df na API.
    # Assumindo que está limpo no início ou após um upload falho:
    response = client.get("/data/view_processed")
    # Se o estado não for limpo, este teste pode falhar se um teste anterior carregou dados.
    # Uma forma de mitigar é fazer um upload falho antes para limpar o estado.
    client.post("/data/upload_csv", files={"file": ("dummy.txt", b"invalid", "text/plain")})
    response_after_failed_upload = client.get("/data/view_processed")
    
    assert response_after_failed_upload.status_code == 404
    assert "Nenhum dado processado disponível" in response_after_failed_upload.json()["detail"]

def test_view_processed_data_with_data(client, sample_csv_file_path):
    """Testa a visualização de dados processados após um upload bem-sucedido."""
    # Primeiro, fazer upload de um arquivo válido
    with open(sample_csv_file_path, "rb") as f:
        upload_response = client.post("/data/upload_csv", files={"file": ("test_upload_data.csv", f, "text/csv")})
    assert upload_response.status_code == 200
    
    # Depois, tentar visualizar
    response = client.get("/data/view_processed?limit=1")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) == 1
    assert "data" in json_response[0]
    assert "descricao" in json_response[0]

def test_predict_cashflow_no_data(client):
    """Testa o endpoint de previsão quando nenhum dado foi carregado."""
    # Garantir que não há dados carregados (pode depender do estado)
    client.post("/data/upload_csv", files={"file": ("dummy.txt", b"invalid", "text/plain")}) # Limpa dados com upload falho
    response = client.post("/predict/cashflow", json={"days_to_predict": 7})
    assert response.status_code == 400
    assert "Dados não carregados" in response.json()["detail"]

def test_predict_cashflow_with_data(client, sample_csv_file_path):
    """Testa o endpoint de previsão após carregar dados válidos."""
    # Upload de dados válidos
    with open(sample_csv_file_path, "rb") as f:
        client.post("/data/upload_csv", files={"file": ("test_upload_data.csv", f, "text/csv")})
    
    response = client.post("/predict/cashflow", json={"days_to_predict": 7})
    assert response.status_code == 200
    json_response = response.json()
    assert "predictions" in json_response
    assert "alerts" in json_response
    assert isinstance(json_response["predictions"], list)
    assert isinstance(json_response["alerts"], list)
    if json_response["predictions"]:
        assert len(json_response["predictions"]) <= 7 # Pode ser menor se os dados históricos forem curtos

def test_simulate_scenarios_no_data(client):
    """Testa o endpoint de simulação quando nenhum dado foi carregado."""
    client.post("/data/upload_csv", files={"file": ("dummy.txt", b"invalid", "text/plain")}) # Limpa dados
    response = client.post("/simulate/scenarios", json={
        "variacao_entrada": 0.1, 
        "variacao_saida": 0.1, 
        "dias_simulacao": 10, 
        "num_simulacoes": 50
    })
    assert response.status_code == 400
    assert "Dados não carregados" in response.json()["detail"]

def test_simulate_scenarios_with_data(client, sample_csv_file_path):
    """Testa o endpoint de simulação após carregar dados válidos."""
    with open(sample_csv_file_path, "rb") as f:
        client.post("/data/upload_csv", files={"file": ("test_upload_data.csv", f, "text/csv")})
        
    response = client.post("/simulate/scenarios", json={
        "variacao_entrada": 0.1, 
        "variacao_saida": 0.1, 
        "dias_simulacao": 10, 
        "num_simulacoes": 50
    })
    assert response.status_code == 200
    json_response = response.json()
    assert "results_summary" in json_response
    assert "prob_saldo_negativo_final" in json_response["results_summary"]

def test_analyze_customer_delinquency_no_data(client):
    """Testa o endpoint de análise de inadimplência sem dados carregados."""
    client.post("/data/upload_csv", files={"file": ("dummy.txt", b"invalid", "text/plain")}) # Limpa dados
    response = client.get("/analyze/customer_delinquency")
    assert response.status_code == 400
    assert "Dados não carregados" in response.json()["detail"]

@pytest.fixture
def sample_csv_with_delinquency_path():
    """Cria um CSV com dados para análise de inadimplência."""
    upload_dir = "data/api_uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    file_path = os.path.join(upload_dir, "test_delinquency_data.csv")
    data = {
        "data": ["2023-01-01", "2023-01-05", "2023-02-01"],
        "descricao": ["Venda C1", "Venda C2", "Venda C1 Fatura 2"],
        "entrada": [100.0, 200.0, 150.0],
        "saida": [0.0, 0.0, 0.0],
        "id_cliente": ["C1", "C2", "C1"],
        "data_vencimento": ["2023-01-15", "2023-01-10", "2023-02-15"],
        "data_pagamento": [None, "2023-01-12", None], # C1 em atraso, C2 pago com atraso
        "valor_fatura": [100.0, 200.0, 150.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    yield file_path
    if os.path.exists(file_path):
        os.remove(file_path)

def test_analyze_customer_delinquency_with_data(client, sample_csv_with_delinquency_path):
    """Testa o endpoint de análise de inadimplência com dados válidos."""
    with open(sample_csv_with_delinquency_path, "rb") as f:
        client.post("/data/upload_csv", files={"file": ("test_delinquency_data.csv", f, "text/csv")})
    
    response = client.get("/analyze/customer_delinquency")
    assert response.status_code == 200
    json_response = response.json()
    assert "report" in json_response
    assert "segmented_customers" in json_response
    assert "total_clientes_com_faturas_em_atraso" in json_response["report"]

# Para executar os testes, no terminal, na raiz do projeto:
# pytest tests/test_api.py

