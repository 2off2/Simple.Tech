# api/main.py
import pytest
from fastapi.testclient import TestClient
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a função create_app do main.py
from api.main import create_app

# Cria uma instância da aplicação para testes
app = create_app()

# Importa o state
import api.endpoints.state as state

# Garantir que o diretório de uploads exista
os.makedirs(state.UPLOAD_DIR, exist_ok=True)

# Cliente de teste
client = TestClient(app)

# Fixture para configurar e limpar o ambiente de teste
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup - executado antes de cada teste
    state.global_processed_df = None
    state.global_prediction_model = None
    state.global_historical_stats = None
    
    # Executa o teste
    yield
    
    # Teardown - executado após cada teste
    state.global_processed_df = None
    state.global_prediction_model = None
    state.global_historical_stats = None
    
    # Limpa arquivos temporários
    for file in os.listdir(state.UPLOAD_DIR):
        file_path = os.path.join(state.UPLOAD_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

# Testes para os endpoints da API
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_view_processed_data():
    response = client.get("/api/data/view_processed")
    assert response.status_code == 404  # Deve falhar se não houver dados processados

def test_upload_csv():
    """Testa o upload e processamento de um arquivo CSV."""
    # Criar diretório de teste se não existir
    test_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Caminho completo para o arquivo de teste
    test_file_path = os.path.join(test_dir, "dados_teste.csv")
    
    # Criar um arquivo de teste temporário
    with open(test_file_path, "w") as f:
        f.write("data,descricao,id_cliente,entrada,saida\n")
        f.write("2023-01-01,Teste,C001,100.0,0.0\n")
    
    try:
        # Testar o upload
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/api/data/upload_csv",
                files={"file": ("dados_teste.csv", f, "text/csv")}
            )
        
        # Verificar resposta
        assert response.status_code == 200
        assert "filename" in response.json()
        assert response.json()["message"] == "Arquivo CSV carregado e processado com sucesso."
        
        # Verificar se os dados foram processados
        response_view = client.get("/api/data/view_processed")
        assert response_view.status_code == 200
        
    finally:
        # Limpar após o teste
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_prediction_without_data():
    response = client.post("/api/prediction/predict", json={"months": 3})
    assert response.status_code == 404  # Deve falhar se não houver dados processados

def test_risk_analysis_without_data():
    response = client.get("/api/risk/analyze")
    assert response.status_code == 404  # Deve falhar se não houver dados processados

def test_scenario_simulation_without_data():
    response = client.post("/api/scenario/simulate", 
                          json={"scenario_type": "optimistic", "impact_factor": 0.1})
    assert response.status_code == 404  # Deve falhar se não houver dados processados

def test_customer_analysis_without_data():
    response = client.get("/api/customer/analyze")
    assert response.status_code == 404  # Deve falhar se não houver dados processados

# Executa os testes se o arquivo for executado diretamente
if __name__ == "__main__":
    pytest.main(["-v"])
