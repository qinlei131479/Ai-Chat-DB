<p align="center">
  <a href="https://github.com/qinlei131479/Ai-Chat-DB">
    <img src="./docs/docs/images/logo.svg" alt="Aix-DB" width="160"/>
  </a>
</p>

<h3 align="center">Aix-DB - 大模型数据助手</h3>

<p align="center">
  基于大语言模型和 RAG 技术的智能数据分析系统，支持自然语言数据查询（ChatBI）、SQL 生成与可视化
</p>

<p align="center">
  <a href="./README.md">简体中文</a> | <a href="./README_en.md">English</a>
</p>

## 项目介绍

Aix-DB 采用**四套独立 Agent** 架构，按 `qa_type` 路由到不同引擎，实现自然语言到数据洞察的端到端转换：

- **数据问答 / 表格问答**：LangGraph 流水线（Text2SQL / Excel+CSV+DuckDB）
- **智能问答 / 深度问数**：DeepAgents + Skills（智能问答额外支持 MCP 外部工具）

**核心能力**：智能问答 · 数据问答（Text2SQL） · 表格问答 · 深度问数 · 数据可视化 · Skill 模式 · MCP 工具（仅智能问答）

## 系统架构

<p align="center">
  <img src="./docs/docs/images/system-architecture.svg" alt="系统架构图" width="100%" />
</p>

**分层架构设计：**

- **前端层**：Vue 3 + TypeScript 构建的 Web 界面，集成 ECharts 和 AntV 可视化组件
- **API 网关层**：基于 FastAPI + Uvicorn 的异步 API 服务，提供 RESTful 接口和 JWT 认证
- **智能服务层**：四套 Agent（智能问答 / 数据问答 / 表格问答 / 深度问数），按 `qa_type` 路由
- **数据存储层**：PostgreSQL 元数据（含表关系 JSONB）、多类型业务数据源；MinIO 文件存储（表格问答必需）

## 支持的数据源

<p align="center">
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Oracle-F80000?style=for-the-badge&logo=oracle&logoColor=white" />
  <img src="https://img.shields.io/badge/SQL%20Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=clickhouse&logoColor=black" />
  <img src="https://img.shields.io/badge/达梦_DM-003366?style=for-the-badge&logoColor=white" />
  <img src="https://img.shields.io/badge/Apache_Doris-5C4EE5?style=for-the-badge&logo=apache&logoColor=white" />
  <img src="https://img.shields.io/badge/StarRocks-FF6F00?style=for-the-badge&logoColor=white" />
</p>
<p align="center">
  <img src="https://img.shields.io/badge/CSV-217346?style=for-the-badge&logo=files&logoColor=white" />
  <img src="https://img.shields.io/badge/Excel-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white" />
</p>

> CSV / Excel 用于**表格问答**（上传文件分析），不是 SQL 数据源类型。后端还支持 Kingbase、AWS Redshift、Elasticsearch（管理界面默认隐藏，可在代码中启用）。

<p align="center">
  <img src="./docs/docs/images/architecture-flow.svg" alt="数据问答核心流程" width="100%" />
</p>

| 步骤  | 模块             | 说明                                                               |
| :---: | ---------------- | ------------------------------------------------------------------ |
|   1   | **用户输入**     | 用户以自然语言提出数据查询问题                                     |
|   2   | **LLM 意图理解** | 大模型解析问题意图，抽取关键实体和查询条件                         |
|   3   | **RAG 知识检索** | BM25 + FAISS 混合检索表结构；术语库/训练样本向量检索（表关系来自 PostgreSQL 元数据） |
|   4   | **SQL 生成**     | Text2SQL 引擎生成 SQL 语句，并进行语法校验和优化                   |
|   5   | **数据库执行**   | 在目标数据源执行 SQL，支持多种数据库类型                           |
|   6   | **可视化展示**   | 自动生成 ECharts/AntV 图表，直观呈现分析结果                       |

## 快速开始

### 使用 Docker Compose

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB/docker
cp .env.template .env
docker-compose up -d
```

### 访问系统（Docker 部署）

**Web 管理界面**
- 访问地址：http://localhost:18080
- 默认账号：`admin`
- 默认密码：`123456`

**后端 API**
- 访问地址：http://localhost:18088

**PostgreSQL（Docker 容器映射）**
- 连接地址：`localhost:15432`
- 数据库名：`aix_db`
- 用户名：`aix_db`
- 密码：`1`

### 本地开发

**① 克隆项目**

```bash
git clone https://github.com/qinlei131479/Ai-Chat-DB.git
cd Ai-Chat-DB
```

**② 配置环境变量**

```bash
cp .env.example .env
```

本地开发默认配置（见 `.env`）：

| 变量 | 默认值 |
| --- | --- |
| `SERVER_PORT` | `8088` |
| `SERVER_WORKERS` | `1` |
| `SQLALCHEMY_DATABASE_URI` | `postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/aix_db` |
| `MINIO_ENABLED` | `false` |
| `MINIO_ENDPOINT` | `127.0.0.1:9000` |
| `LANGFUSE_TRACING_ENABLED` | `false` |
| `VITE_ENABLE_PAGE_AGENT` | `false` |

**③ 准备 PostgreSQL**

确保本机 PostgreSQL 已启动，并存在数据库 `aix_db`（连接信息与 `.env` 中 `SQLALCHEMY_DATABASE_URI` 一致：`127.0.0.1:5432`，用户 `postgres`，密码 `postgres`）。

> 若改用 Docker Compose 提供 PostgreSQL（映射端口 `15432`），请将 `.env` 中连接串改为：
> `postgresql+psycopg2://aix_db:1@127.0.0.1:15432/aix_db`

**④ 安装 Python 依赖**（Python 3.12）

```bash
# 方式一：pip
pip install -r requirements.txt

# 方式二：uv
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

**⑤ 启动后端服务**（读取项目根目录 `.env`）

```bash
python serv.py
```

后端默认地址：http://localhost:8088

Windows PowerShell：

```powershell
$env:PYTHONUTF8=1; python serv.py
```

**⑥ 启动前端开发服务器**（另开终端，需 Node.js >= 18.12）

```bash
cd web
npm install
npm run dev
```

> 表格问答、部分 Skill 文件能力需启用 MinIO：在 `.env` 中设置 `MINIO_ENABLED=true` 并启动 MinIO 服务。

## 命令行工具（CLI）

通过终端发起自然语言数据查询，支持图表渲染输出。

```bash
npm install -g @apconw/aix-db-cli

aix-db-cli login
aix-db-cli datasources
aix-db-cli chat "有哪些数据表？" --datasource 48
aix-db-cli chat "查询销售额趋势" --datasource 48 --stream
```

详细文档见 [aix-db-cli/README.md](./aix-db-cli/README.md)。

## 技术栈

**后端**：FastAPI · Uvicorn · SQLAlchemy · LangChain/LangGraph · DeepAgents · FAISS · MinIO

**前端**：Vue 3 · TypeScript · Vite 6 · Naive UI · ECharts · AntV

**AI 模型**：OpenAI · Anthropic · DeepSeek · Qwen · Ollama

## 文档

文档源文件位于 `docs/docs/`，使用 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 构建为静态站点（输出目录 `docs/site/`，**不纳入 Git**，需用时本地构建）。

| 文档 | 说明 |
| --- | --- |
| [部署与开发指南](./docs/docs/deployment-guide.md) | Docker 部署、本地开发、环境变量、FAQ |
| [源码理解指南](./docs/docs/source-code-guide.md) | 前后端链路与 Agent/RAG 说明 |
| [配置指南](./docs/docs/index.md) | 部署后系统配置（模型、数据源、MinIO 等） |
| [API 文档](http://localhost:8088/docs) | 后端 Swagger（需先启动 `python serv.py`） |

### 阅读方式

**① 直接阅读 Markdown**（无需构建）

在 IDE 或 GitHub 中打开 `docs/docs/` 下对应 `.md` 文件即可。

**② 本地预览站点**（推荐，支持热更新）

```bash
uv run mkdocs serve -f docs/mkdocs.yml
```

浏览器访问 http://127.0.0.1:8000

**③ 构建静态站点**（首次或文档更新后执行）

```bash
uv run mkdocs build -f docs/mkdocs.yml
```

构建产物输出到 `docs/site/`（已在 `.gitignore` 中忽略），可用任意静态服务器托管，例如：

```bash
cd docs/site && python3 -m http.server 8000
```

然后访问 http://127.0.0.1:8000

## 贡献指南

欢迎提交 Issue 和 Pull Request。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 开源许可

本项目采用 [Apache License 2.0](./LICENSE) 开源许可证。
