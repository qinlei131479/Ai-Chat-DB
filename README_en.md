<p align="center">
  <a href="https://github.com/qinlei131479/Ai-Chat-DB">
    <img src="docs/images/logo.svg" alt="Ai-Chat-DB" width="160"/>
  </a>
</p>

<h3 align="center">Ai-Chat-DB - LLM Data Assistant</h3>

<p align="center">
  An intelligent data analytics system powered by Large Language Models and RAG technology, enabling conversational data analysis (ChatBI) for rapid data extraction and visualization
</p>

<p align="center">
  <a href="./README.md">简体中文</a> | <a href="./README_en.md">English</a>
</p>

<p align="center">
  Our commercial product with powerful enterprise features:<br/>
  Private Deployment · Custom Development · Dedicated Support · Multi-scenario AI Applications
</p>

<p align="center">
  <a href="YOUR_CHAT_URL"><img src="https://img.shields.io/badge/💬_AI_Chat-4A90D9?style=for-the-badge" alt="AI Chat" /></a>
  <a href="YOUR_DATA_URL"><img src="https://img.shields.io/badge/📊_Data_Q&A-10B981?style=for-the-badge" alt="Data Q&A" /></a>
  <a href="http://www.aixhub.top:5006"><img src="https://img.shields.io/badge/📈_Report_Gen-F59E0B?style=for-the-badge" alt="Report Generation" /></a>
</p>


Ai-Chat-DB is built on the **LangChain/LangGraph** framework, combined with **MCP Skills** multi-agent collaboration architecture, enabling end-to-end transformation from natural language to data insights.

**Core Capabilities**: General Q&A · Data Q&A (Text2SQL) · Spreadsheet Q&A · Deep Research · Data Visualization · MCP Multi-Agent

**Product Features**: 📦 Ready to Use · 🔒 Secure & Controllable · 🔌 Easy Integration · 🎯 Increasingly Accurate

---


## System Architecture

<p align="center">
  <img src="docs/images/system-architecture.svg" alt="System Architecture" width="100%" />
</p>

**Layered Architecture Design:**

- **Frontend Layer**: Modern web interface built with Vue 3 + TypeScript, integrated with ECharts and AntV visualization components
- **API Gateway Layer**: High-performance async API service based on Fastapi, providing RESTful interfaces and JWT authentication
- **Intelligent Service Layer**: LLM services, Text2SQL Agent, RAG retrieval engine, MCP multi-agent collaboration
- **Data Storage Layer**: Support for multiple database types including relational databases, vector databases, graph databases, and file storage

---

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
  <img src="https://img.shields.io/badge/More_Coming_Soon...-gray?style=for-the-badge" />
</p>


<p align="center">
  <img src="docs/images/architecture-flow.svg" alt="Data Q&A Workflow" width="100%" />
</p>

| Step | Module | Description |
|:---:|--------|-------------|
| 1 | **User Input** | User asks data query questions in natural language |
| 2 | **LLM Intent Understanding** | LLM parses question intent, extracts key entities and query conditions |
| 3 | **RAG Knowledge Retrieval** | Embedding + BM25 hybrid retrieval, combined with Neo4j graph to obtain relevant table structures and business knowledge |
| 4 | **SQL Generation** | Text2SQL engine generates SQL statements with syntax validation and optimization |
| 5 | **Database Execution** | Execute SQL on target data source, supporting 8+ database types |
| 6 | **Visualization** | Automatically generate ECharts/AntV charts to present analysis results |


---

## Quick Start

### Deploy with Docker (Recommended)

```bash

```

> **Note**: To enable Langfuse full-chain tracing, set `LANGFUSE_TRACING_ENABLED=true` and configure the corresponding keys and URL.

### Deploy with Docker Compose

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB/docker
cp .env.template .env  # Copy env template, modify as needed
docker-compose up -d
```

### Access the System

**Web Management Interface**
- URL: http://localhost:18080
- Username: `admin`
- Password: `123456`

**PostgreSQL Database**
- Connection: `localhost:5432`
- Database: `bubble_ai`
- Username: `postgres`
- Password: `postgres`

### Local Development

**① Clone the Repository**
```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB
```

**② Start Middleware Dependencies** (PostgreSQL, MinIO, etc.)
```bash
cd docker
docker-compose up -d
```

**③ Configure Environment Variables**

Edit `.env.dev` in the project root to set database connection, MinIO address, etc. (default config works out of the box)

**④ Install Python Dependencies** (requires Python 3.12)
```bash
# Option 1: pip
pip install -r requirements.txt

# Option 2: uv (recommended, faster)
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

**⑤ Start Backend Service**
```bash
python serv.py
```

**⑥ Start Frontend Dev Server** (in another terminal)
```bash
cd web
npm install
npm run dev
```

---

## Tech Stack

**Backend**: Fastapi · SQLAlchemy · LangChain/LangGraph · Neo4j · FAISS/Chroma · MinIO

**Frontend**: Vue 3 · TypeScript · Vite 5 · Naive UI · ECharts · AntV

**AI Models**: OpenAI · Anthropic · DeepSeek · Qwen · Ollama

---

## Documentation
- [Configuration Guide](docs/index.md)
- [API Documentation](http://localhost:8088/docs) (available after startup)

---

## License

This project is licensed under the [Apache License 2.0](./LICENSE).
