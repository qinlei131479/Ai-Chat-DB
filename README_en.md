<p align="center">
  <a href="https://github.com/qinlei131479/Ai-Chat-DB">
    <img src="./docs/docs/images/logo.svg" alt="Aix-DB" width="160"/>
  </a>
</p>

<h3 align="center">Aix-DB - LLM Data Assistant</h3>

<p align="center">
  An intelligent data analytics system powered by Large Language Models and RAG technology, supporting natural language data queries (ChatBI), SQL generation, and visualization
</p>

<p align="center">
  <a href="./README.md">简体中文</a> | <a href="./README_en.md">English</a>
</p>

## Overview

Aix-DB uses **four independent agents**, routed by `qa_type` to different engines for end-to-end natural language to data insights:

- **Data Q&A / Spreadsheet Q&A**: LangGraph pipelines (Text2SQL / Excel+CSV+DuckDB)
- **General Q&A / Deep Research**: DeepAgents + Skills (General Q&A additionally supports MCP external tools)

**Core Capabilities**: General Q&A · Data Q&A (Text2SQL) · Spreadsheet Q&A · Deep Research · Data Visualization · Skill Mode · MCP Tools (General Q&A only) · API Token (OpenAPI integration)

## System Architecture

<p align="center">
  <img src="./docs/docs/images/system-architecture.svg" alt="System Architecture" width="100%" />
</p>

**Layered Architecture Design:**

- **Frontend Layer**: Web interface built with Vue 3 + TypeScript, integrated with ECharts and AntV visualization components
- **API Gateway Layer**: Async API service based on FastAPI + Uvicorn; supports login JWT (7-day) and permanent API Token (`aix_*`) authentication
- **Intelligent Service Layer**: Four agents (General Q&A / Data Q&A / Spreadsheet Q&A / Deep Research), routed by `qa_type`
- **Data Storage Layer**: PostgreSQL metadata (including table relations JSONB), multi-type business datasources; MinIO file storage (required for Spreadsheet Q&A)

## Supported Data Sources

<p align="center">
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Oracle-F80000?style=for-the-badge&logo=oracle&logoColor=white" />
  <img src="https://img.shields.io/badge/SQL%20Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=clickhouse&logoColor=black" />
  <img src="https://img.shields.io/badge/Dameng_DM-003366?style=for-the-badge&logoColor=white" />
  <img src="https://img.shields.io/badge/Apache_Doris-5C4EE5?style=for-the-badge&logo=apache&logoColor=white" />
  <img src="https://img.shields.io/badge/StarRocks-FF6F00?style=for-the-badge&logoColor=white" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/CSV-217346?style=for-the-badge&logo=files&logoColor=white" />
  <img src="https://img.shields.io/badge/Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white" />
</p>

> CSV / Excel are for **Spreadsheet Q&A** (file upload analysis), not SQL datasource types. The backend also supports Kingbase, AWS Redshift, and Elasticsearch (hidden in the UI by default).

<p align="center">
  <img src="./docs/docs/images/architecture-flow.svg" alt="Data Q&A Workflow" width="100%" />
</p>

| Step | Module | Description |
|:---:|--------|-------------|
| 1 | **User Input** | User asks data query questions in natural language |
| 2 | **LLM Intent Understanding** | LLM parses question intent, extracts key entities and query conditions |
| 3 | **RAG Knowledge Retrieval** | BM25 + FAISS hybrid table retrieval; terminology/training-sample vector search (table relations from PostgreSQL metadata) |
| 4 | **SQL Generation** | Text2SQL engine generates SQL statements with syntax validation and optimization |
| 5 | **Database Execution** | Execute SQL on target data source, supporting multiple database types |
| 6 | **Visualization** | Automatically generate ECharts/AntV charts to present analysis results |

## Quick Start

### Deploy with Docker Compose

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB/docker
cp .env.template .env
docker-compose up -d
```

### Access the System (Docker)

**Web Management Interface**
- URL: http://localhost:18080
- Username: `admin`
- Password: `123456`

**Backend API**
- URL: http://localhost:18088

**PostgreSQL (Docker mapped port)**
- Connection: `localhost:15432`
- Database: `aix_db`
- Username: `aix_db`
- Password: `1`

### Local Development

**① Clone the Repository**

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB
```

**② Configure Environment Variables**

```bash
cp .env.example .env
```

Default local development values (see `.env`):

| Variable | Default |
| --- | --- |
| `SERVER_PORT` | `8088` |
| `SERVER_WORKERS` | `1` |
| `SQLALCHEMY_DATABASE_URI` | `postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/aix_db` |
| `MINIO_ENABLED` | `false` |
| `MINIO_ENDPOINT` | `127.0.0.1:9000` |
| `LANGFUSE_TRACING_ENABLED` | `false` |
| `VITE_ENABLE_PAGE_AGENT` | `false` |

**③ Prepare PostgreSQL**

Ensure PostgreSQL is running locally with database `aix_db` (matching `SQLALCHEMY_DATABASE_URI` in `.env`: `127.0.0.1:5432`, user `postgres`, password `postgres`).

> If using Docker Compose for PostgreSQL (mapped port `15432`), update `.env` to:
> `postgresql+psycopg2://aix_db:1@127.0.0.1:15432/aix_db`

**④ Install Python Dependencies** (Python 3.12)

```bash
# Option 1: pip
pip install -r requirements.txt

# Option 2: uv
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

**⑤ Start Backend Service** (loads `.env` from project root)

```bash
python serv.py
```

Backend URL: http://localhost:8088

**⑥ Start Frontend Dev Server** (in another terminal, requires Node.js >= 18.12)

```bash
cd web
npm install
npm run dev
```

> Spreadsheet Q&A and some Skill file features require MinIO: set `MINIO_ENABLED=true` in `.env` and run a MinIO service.

## CLI

Query data from the terminal with natural language and chart output.

```bash
npm install -g @apconw/aix-db-cli

aix-db-cli login
aix-db-cli login --token aix_xxx --url http://localhost:18080   # permanent API Token
aix-db-cli datasources
aix-db-cli chat "What tables are available?" --datasource 48
aix-db-cli chat "Show sales trend" --datasource 48 --stream
```

See [aix-db-cli/README.md](./aix-db-cli/README.md) for details.

## Tech Stack

**Backend**: FastAPI · Uvicorn · SQLAlchemy · LangChain/LangGraph · DeepAgents · FAISS · MinIO

**Frontend**: Vue 3 · TypeScript · Vite 6 · Naive UI · ECharts · AntV

**AI Models**: OpenAI · Anthropic · DeepSeek · Qwen · Ollama

## Documentation

Source files live in `docs/docs/` and are built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) into a static site (`docs/site/`, **not committed to Git** — build locally when needed).

| Document | Description |
| --- | --- |
| [Deployment & Development Guide](./docs/docs/deployment-guide.md) | Docker, local dev, env vars, FAQ |
| [Source Code Guide](./docs/docs/source-code-guide.md) | Frontend-to-backend flow, Agent/RAG details |
| [API Token Guide](./docs/docs/api-token-guide.md) | Permanent token management, curl/CLI examples |
| [Configuration Guide](./docs/docs/index.md) | Post-deployment setup (models, datasources, MinIO, etc.) |
| [API Documentation](http://localhost:8088/docs) | Backend Swagger (requires `python serv.py`) |

### How to Read

**① Read Markdown directly** (no build required)

Open the `.md` files under `docs/docs/` in your IDE or on GitHub.

**② Local preview** (recommended, with hot reload)

```bash
uv run mkdocs serve -f docs/mkdocs.yml
```

Open http://127.0.0.1:8000 in your browser.

**③ Build static site** (run after first clone or when docs change)

```bash
uv run mkdocs build -f docs/mkdocs.yml
```

Output goes to `docs/site/` (listed in `.gitignore`). Serve it with any static file server, for example:

```bash
cd docs/site && python3 -m http.server 8000
```

Then visit http://127.0.0.1:8000

## Contributing

Issues and Pull Requests are welcome.

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the [Apache License 2.0](./LICENSE).
