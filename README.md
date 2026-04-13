# Torre de Controle — Anjun Express BI de Operações

Dashboard operacional em tempo real para monitoramento logístico. Desenvolvido com Streamlit e PostgreSQL, consolida dados de múltiplas fontes em uma interface única para acompanhamento de backlog, produtividade, devoluções e SLA.

---

## Módulos

| Módulo | Descrição |
|---|---|
| **Backlog Atual** | Visão em tempo real do backlog por estado, cliente e faixa de tempo (24h / 48h / 72h+). Inclui mapa geográfico e download de waybills |
| **Backlog Histórico** | Evolução histórica do backlog com drill por faixa de SLA |
| **Produtividade** | Volume processado por turno e dispositivo; análise de pacotes grandes |
| **Tempo de Processamento** | SLA operacional, tempo médio por IATA e consolidação Perus + TFK |
| **Health Check** | Saúde operacional consolidada com indicadores por semana |
| **Devoluções** | Análise de pedidos devolvidos, P90, motivos e DSPs sem 3 tentativas |
| **Importação** | Upload de planilhas Excel para atualização das bases de dados |

---

## Tecnologias

- **Frontend:** [Streamlit](https://streamlit.io) — interface web em Python
- **Banco de dados:** PostgreSQL (5 databases separados por domínio)
- **Visualização:** Plotly Express + gráficos HTML customizados
- **Dados geoespaciais:** GeoJSON dos estados brasileiros

---

## Estrutura do projeto

```
logistica_dashboard/
├── app.py                  # Entrypoint — roteamento e layout global
├── pages/                  # Um arquivo por módulo do dashboard
│   ├── home.py
│   ├── backlog.py
│   ├── backlog_historico.py
│   ├── produtividade.py
│   ├── tempo_processamento.py
│   ├── health_check.py
│   ├── devolucoes.py
│   └── importacao.py
├── core/                   # Lógica de negócio e acesso a dados
│   ├── database.py         # Conexões PostgreSQL (com cache por sessão)
│   ├── repository.py       # Queries organizadas por domínio
│   └── processar_arquivo.py# ETL das planilhas importadas
├── utils/                  # Utilitários compartilhados
│   ├── style.py            # CSS global, tabela padrão, rodapé
│   ├── theme.py            # Helpers de gráficos Plotly
│   └── colors.py           # Paleta de cores Anjun
├── assets/                 # Arquivos estáticos
│   ├── style_light.css
│   ├── style_dark.css
│   └── brasil_estados.json # GeoJSON para mapa choropleth
├── requirements.txt
└── .env                    # Credenciais (não versionado)
```

---

## Configuração

### 1. Clonar e instalar dependências

```bash
git clone https://github.com/seu-usuario/logistica_dashboard.git
cd logistica_dashboard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

Crie um arquivo `.env` na raiz com as conexões PostgreSQL:

```env
DATABASE_URL_BACKLOG=postgresql://usuario:senha@host:5432/backlog
DATABASE_URL_OPERACIONAL=postgresql://usuario:senha@host:5432/operacional
DATABASE_URL_HISTORICO=postgresql://usuario:senha@host:5432/historico
DATABASE_URL_DEVOLUCOES=postgresql://usuario:senha@host:5432/devolucoes
DATABASE_URL_PROCESSAMENTO=postgresql://usuario:senha@host:5432/processamento
```

> Em produção (ex: Streamlit Cloud), configure as mesmas variáveis em **Settings → Secrets**.

### 3. Rodar localmente

```bash
streamlit run app.py
```

O dashboard abre automaticamente em `http://localhost:8501`.

---

## Deploy

O projeto está configurado para deploy no **Streamlit Community Cloud**:

1. Faça push do repositório para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte o repositório
3. Defina o entrypoint como `app.py`
4. Configure os secrets no painel do Streamlit Cloud (as mesmas variáveis do `.env`)

---

## Arquivos que não são versionados

Por segurança e tamanho, os seguintes arquivos/pastas estão no `.gitignore`:

- `.env` — credenciais do banco de dados
- `data/` — banco local e arquivos parquet
- `uploads/` — planilhas enviadas pelos usuários
- `temp/` — arquivos temporários gerados pelo sistema
- `*.xlsx`, `*.csv`, `*.parquet` — dados brutos

---

## Autor

Desenvolvido por **Samuel Freitas**  
© 2026 — Torre de Controle. Todos os direitos reservados.
