# RiskAI - Análise Preditiva de Fluxo de Caixa

Sistema inteligente para análise de risco financeiro, previsão de fluxo de caixa e simulação de cenários.

## 🚀 Início Rápido

### 1. Instalação das Dependências

```bash
# Instalar dependências
pip install -r requirements.txt
```

### 2. Executar a Aplicação

#### Opção A: Script Automático (Recomendado)
```bash
python run_app.py
```

#### Opção B: Manual
```bash
# Terminal 1 - API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Dashboard
streamlit run dashboard/app.py --server.port 8501
```

### 3. Acessar a Aplicação

- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **Documentação da API**: http://localhost:8000/docs

## 📊 Como Usar

### 1. Upload de Dados
- Acesse a página "1. Upload de Dados"
- Faça upload do seu arquivo CSV financeiro
- O arquivo deve conter pelo menos as colunas: `data`, `descricao`
- Colunas recomendadas: `entrada`, `saida`

### 2. Formato do CSV

```csv
data,descricao,entrada,saida
2024-01-01,Venda Produto A,1000.00,0.00
2024-01-02,Pagamento Fornecedor,0.00,500.00
2024-01-03,Venda Produto B,1500.00,0.00
```

### 3. Análises Disponíveis

#### Previsão de Fluxo de Caixa
- Página "2. Previsão"
- Gera previsões futuras do saldo
- Identifica alertas de risco

#### Simulação de Cenários
- Página "3. Simulação"
- Simulação de Monte Carlo
- Análise de probabilidades de risco

#### Dashboard Geral
- Página "4. Dashboard Geral"
- Visão consolidada de todas as análises

## 🔧 Estrutura do Projeto

```
RiskAI_PTI/
├── api/                    # API FastAPI
│   ├── endpoints/         # Endpoints da API
│   │   ├── data.py       # Upload e processamento de dados
│   │   ├── predictions.py # Previsões de fluxo de caixa
│   │   ├── simulations.py # Simulações Monte Carlo
│   │   └── state.py      # Estado compartilhado
│   └── main.py           # Aplicação principal da API
├── dashboard/              # Interface Streamlit
│   ├── pages/            # Páginas do dashboard
│   │   ├── 01_Upload.py
│   │   ├── 02_Previsao.py
│   │   ├── 03_Simulacao.py
│   │   └── 04_Dashboard_Geral.py
│   └── app.py            # Aplicação principal do dashboard
├── core/                   # Módulos de análise
│   ├── customer_analysis.py
│   └── scenario_simulator.py
├── requirements.txt        # Dependências
├── run_app.py             # Script de inicialização
└── README.md              # Este arquivo
```

## 🛠️ Soluções de Problemas Comuns

### Erro 404 na API
- Verifique se a API está rodando: http://localhost:8000/health
- Certifique-se de que está usando os endpoints corretos com `/api/` no prefixo

### Erro de Conexão
- Verifique se ambos os serviços estão rodando
- Confirme se as portas 8000 e 8501 estão livres

### Erro no Upload de Arquivos
- Verifique se o arquivo é CSV válido
- Confirme se possui as colunas obrigatórias: `data`, `descricao`
- Verifique o formato das datas (YYYY-MM-DD)

### Problemas de Dependências
```bash
# Reinstalar dependências
pip install --upgrade -r requirements.txt

# Limpar cache do pip
pip cache purge
```

## 📈 Funcionalidades

### ✅ Implementado
- Upload e processamento de dados CSV
- Previsão de fluxo de caixa com machine learning
- Análise de riscos e alertas
- Simulação de Monte Carlo
- Dashboard interativo
- API REST completa

### 🔄 Em Desenvolvimento
- Análise de inadimplência de clientes
- Relatórios em PDF
- Integração com bancos de dados
- Autenticação de usuários

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

Para suporte e dúvidas:
- Abra uma issue no GitHub
- Entre em contato com a equipe de desenvolvimento

---

**RiskAI** - Desenvolvido com ❤️ para análise financeira inteligente