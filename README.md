# Math Copilot v0.4

Math Copilot 是一个旨在辅助用户解决数学问题的智能助手。它结合了先进的大语言模型（LLM）、图数据库以及事件驱动的微服务架构，提供一个交互式的、步骤化的解题环境。

## 目录

- [项目总览](#项目总览)
- [体系架构](#体系架构)
- [核心数据模型](#核心数据模型)
- [主要工作流（时序图）](#主要工作流时序图)
- [技术栈](#技术栈)
- [目录结构](#目录结构)
- [本地开发设置](#本地开发设置)
- [开发计划与顺序](#开发计划与顺序)

## 项目总览

Math Copilot 旨在成为一个单页应用 (Next.js) + Python 微后端 (FastAPI + event-sourcing) 的组合，利用 OpenAI 等全云模型栈，并通过图数据库（如 Neo4j 或基于表的边关系）管理解题步骤的 DAG (有向无环图)。

**关键数据集:**
*   `data1`：Event 表，记录所有用户动作和系统事件。
*   `data2`：当前可见路径块 (从 `DagState.currentNode` 可追溯到根节点的路径)。
*   `data3`：完整的 Block + Edge DAG 结构。
*   `DagState.currentNode`：当前用户选中的解题步骤节点。

## 体系架构

```mermaid
flowchart LR
    %% ========= Frontend =========
    subgraph FE["🖥️  Frontend (Next.js SPA)\nType-safe RPC + WebSocket"]
        P[ProblemInputCard]
        BL(BlockList)
        BC(BlockCard)
        DC(DagCanvas)
        CB(ChatCommandBar)
        MOD(AltOutputModal)
    end
    FE -- tRPC/REST --> GW

    %% ========= Backend Core =========
    subgraph BE["🛠️  Backend Core (FastAPI)"]
        GW[API Gateway\nAuth + Rate-limit]
        BSV(Block-Service):::serv
        DSV(DAG-Service):::serv
        LSV(LLM-Router):::serv
        EVB(Event-Bus):::serv
    end

    %% ========= Storage =========
    SQL[(PostgreSQL<br/>Problems / Blocks / Events / DagState)]
    Neo[(Neo4j or Edge-table)]
    VEC[(Milvus RAG-索引)] %% RAG 索引为独立模块，不直接耦合核心模型

    %% ========= LLM Cluster =========
    subgraph LLM["☁️  OpenAI / Anthropic / Google AI"]
        GPT4o[[gpt-4o]]
        GPT4[[gpt-4-turbo]]
        DSK[[deepseek-v2-67b]]
        GMI[[gemini-1.5-pro]]
        CLD[[claude-3-opus]]
    end

    %% ========= Arrows =========
    GW -. Pub/Sub .-> EVB
    GW --> BSV & DSV & LSV
    BSV --> SQL
    DSV --> SQL & Neo
    LSV -->|fan-out| GPT4o & GPT4 & DSK & GMI & CLD
    DSV -- WS stream --> FE
    EVB -- CDC/SSE --> FE
    SQL --> VEC

    classDef serv fill:#fdf6b2,stroke:#d97706,stroke-width:1px;
```

**组件职责简述:** (详细内容参考项目设计文档 `docs/arch.md`)
*   **API Gateway (FastAPI)**: 入口，鉴权，限流，路由，错误处理。
*   **LLM-Router**: 解析 Agent/Prompt，并发调用多模型/Workflow，合并结果。
*   **Block-Service**: 解题步骤 (Block) 的 CRUD, LaTeX 预渲染, 状态管理。
*   **DAG-Service**: 管理 Block 间的关系 (Edge), 维护 `DagState.currentNode`, 计算 `data2`, 推送流数据给前端。
*   **Event-Bus (Kafka/NATS/etc.)**: 记录 Event, 将变更事件推送给前端。
*   **Milvus**: 存储题库向量，供 `suggest_next_moves` (RAG) 检索 (作为独立模块)。

## 核心数据模型

数据模型定义位于 `apps/gateway/schemas/core_models.py` (使用 Pydantic)。

*   **`Problem`**: 题目信息 (LaTeX, 图片/音频链接等)。
*   **`Block`**: 单个解题步骤 (LaTeX, HTML, 作者, 状态, 是否终点, 模型备选输出 `altOutputs` 等)。
*   **`Event`**: 系统事件记录 (类型, 载荷, 时间戳)。
*   **`DagState`**: 当前问题的 DAG 状态 (如 `currentNode`)。
*   **`Edge`**: (若不用原生图数据库) 显式定义 Block 间的父子关系。

详情请参考设计文档中的 DDL 或 Pydantic 模型代码。

## 主要工作流（时序图）

以下列出部分核心工作流。完整的时序图集合位于 `docs/sequence-diagrams.md`。

1.  **题目上传 (problem_ingest)**: 用户上传题目，系统处理，生成首个解题步骤。
2.  **题干 LaTeX 手动修改 (latex_refine)**: 用户修改题目 LaTeX。
3.  **节点切换 (node_select)**: 用户在 DAG 图上选择不同步骤。
4.  **块编辑 (block_edit)**: 用户编辑某个解题步骤的内容。
5.  **块删除 (block_delete, 级联)**: 删除步骤及其所有后续步骤。
6.  **块解析 (block_parse)**: 请求对某个步骤进行详细解释。
7.  **提示思路 (suggest_next_moves)**: 请求下一步的解题建议。
8.  **继续解答 (solve_next_step, 手动/自动)**: 执行下一步解题。
9.  **全部解答 (solve_to_end)**: 自动完成所有解题步骤。
10. **解析答案导入 (answer_to_steps)**: 上传答案，系统解析为步骤。

每个工作流的详细时序图（Mermaid 格式）和验证要点均在 `docs/sequence-diagrams.md` 中有详细描述。这些时序图是理解系统动态行为和进行测试的关键。

## 技术栈

*   **前端**: Next.js (React)
*   **后端**: Python, FastAPI
*   **数据库**: PostgreSQL (核心数据), Neo4j/Edge-Table (DAG), Milvus (RAG 索引)
*   **LLM**: OpenAI API, Anthropic, Google AI 等
*   **消息队列/事件总线**: Kafka/NATS (可选，或 FastAPI Background Tasks/StreamingResponse 初期替代)
*   **UI 库**: Tailwind CSS + shadcn/ui (或其他 React UI Kit)
*   **部署**: Docker, Kubernetes (可选)

## 目录结构

```
math-copilot/
├─ apps/
│  ├─ web/                       # Next.js 前端
│  │  ├─ components/
│  │  ├─ pages/
│  │  └─ lib/api.ts              # tRPC client or similar
│  └─ gateway/                   # FastAPI 后端
│     ├─ main.py
│     ├─ routers/                # API 路由
│     ├─ services/               # 业务逻辑服务
│     └─ schemas/                # Pydantic 数据模型 (e.g., core_models.py)
├─ packages/
│  ├─ llm_workflows/            # LLM 调用流程
│  └─ ui-kit/                   # (如果共享 UI 组件)
├─ infra/
│  ├─ docker-compose.yml        # 本地开发环境编排
│  ├─ Dockerfile.gw
│  ├─ Dockerfile.web
│  └─ k8s-manifests/            # (可选) Kubernetes 部署文件
└─ docs/
   ├─ openapi.yaml              # API 规范
   ├─ prompt-templates.md
   ├─ arch.md                   # 架构设计文档
   └─ sequence-diagrams.md      # 核心工作流时序图
```

## 本地开发设置

1.  **安装 Docker Desktop**：确保你的机器上安装并运行了 Docker。
2.  **克隆仓库**：`git clone <repository-url>`
3.  **配置环境变量**：可能需要创建 `.env` 文件来存储 API 密钥等敏感信息（参考 `.env.example` - 如果有）。
4.  **启动依赖服务**：
    ```bash
    cd math-copilot/infra
    docker-compose up -d # 这会后台启动 PostgreSQL, Neo4j (如果配置了) 等
    ```
5.  **后端 (FastAPI Gateway)**：
    *   创建并激活 Python 虚拟环境。
    *   安装依赖：`pip install -r apps/gateway/requirements.txt` (需要创建此文件)。
    *   运行数据库迁移 (如果使用 Alembic)：`alembic upgrade head`。
    *   启动服务：`uvicorn apps.gateway.main:app --reload` (通常在 `apps/gateway` 目录下运行)。
6.  **前端 (Next.js Web)**：
    *   安装依赖：`cd apps/web && npm install` (或 `yarn install`)。
    *   启动服务：`npm run dev` (或 `yarn dev`)。

具体命令可能需要根据项目实际配置调整。

## 开发计划与顺序

以下是一个建议的迭代开发顺序，侧重于逐步构建核心功能并尽早获得反馈。你可以根据实际情况调整优先级。

**阶段 0: 项目初始化与基础设置**
*   [ ] Git 仓库初始化。
*   [ ] 完善 `infra/docker-compose.yml` 启动 PostgreSQL (Neo4j/Milvus 初期可选)。
*   [ ] FastAPI (gateway) 项目骨架创建。
*   [ ] Next.js (web) 项目骨架创建。
*   [ ] 实现 `apps/gateway/schemas/core_models.py` 中定义的 Pydantic 模型。
*   [ ] 选择并集成 ORM (如 SQLModel)，配置数据库连接，并执行首次数据库迁移生成表。
*   [ ] 为 Pydantic 模型编写基础单元测试。

**阶段 1: 核心功能 - 题目上传与展示 (对应时序图 #1)**
*   **目标**：实现用户上传题目（LaTeX/图片），后端处理，生成根 Block 和首个步骤 Block，存入数据库，并通过 WebSocket 推送给前端展示。
*   **后端**:
    *   [ ] `/problems/ingest` API Endpoint。
    *   [ ] `problem_ingest` Agent 基础实现 (初期可 mock LLM 响应)。
    *   [ ] `Block-Service`: 创建 Problem, Root Block, First Step Block。
    *   [ ] `Event-Bus`: 基础事件发布 (如 `block_create`)。
    *   [ ] `DAG-Service`: 创建 `DagState`，记录 Block 间关系 (root -> first step)，处理到 PostgreSQL。
    *   [ ] WebSocket 基础搭建，用于推送 `data2` (当前路径) 和 DAG 结构给前端。
*   **前端**:
    *   [ ] `ProblemInputCard` 组件 UI 及基本交互。
    *   [ ] `BlockList` 和 `BlockCard` 组件用于展示题目和首步骤。
    *   [ ] `DagCanvas` (使用 React Flow) 基础搭建，能展示根节点和首步骤节点。
    *   [ ] WebSocket 客户端，接收并展示实时更新。

**阶段 2: Block 基本操作与 DAG 交互 (对应时序图 #3, #4, #5)**
*   **目标**：实现用户对解题步骤的编辑、删除以及在 DAG 图上切换当前选中节点。
*   **后端**:
    *   [ ] `/blocks/{id}` (PATCH for edit, DELETE for delete) API Endpoints。
    *   [ ] `/dag/current/{nodeId}` (PATCH) API Endpoint。
    *   [ ] `Block-Service`: 更新/软删除 Block 逻辑。
    *   [ ] `DAG-Service`: 更新 `DagState.currentNode`，处理 Block 删除对 DAG 的影响 (级联软删，父节点回溯)。
    *   [ ] 完善 WebSocket 推送，确保 `data2` 和 DAG 视图正确更新。
*   **前端**:
    *   [ ] `BlockCard`: 编辑、删除按钮及交互。
    *   [ ] `DagCanvas`: 节点点击事件处理，调用后端切换 `currentNode`，高亮当前路径。
    *   [ ] 处理 Block 删除后前端视图的正确刷新。

**阶段 3: LLM 驱动的单步智能操作 (对应时序图 #2, #6, #7, #8)**
*   **目标**：集成 LLM 实现对题干的优化、对步骤的解析、解题思路建议以及手动的下一步解答。
*   **后端**:
    *   [ ] 实现 `LLM-Router` 及 `fanout_call` 基础 (即使初期只调用单模型)。
    *   [ ] 实现 `latex_refine`, `block_parse`, `suggest_next_moves`, `solve_next_step` Agents 的 Prompt 和后端逻辑。
    *   [ ] `/problems/{id}/latex` (PATCH for refine), `/blocks/{id}/parse` (POST), `/chat/suggest` (POST), `/chat/next` (POST) API Endpoints。
*   **前端**:
    *   [ ] 题干编辑后触发 `latex_refine`。
    *   [ ] `BlockCard` 添加"解析"按钮触发 `block_parse`。
    *   [ ] `ChatCommandBar` UI 及基本交互，实现"提示思路"、"下一步"按钮。
    *   [ ] 弹窗或侧边栏展示 `suggest_next_moves` 的结果。

**阶段 4: 多模型支持与自动化工作流 (对应时序图 #9, #10)**
*   **目标**：实现多模型候选输出、用户选择，以及"全部解答"的自动化流程。
*   **后端**:
    *   [ ] 完善 `LLM-Router` 的 `fanout_call` 支持多模型并发。
    *   [ ] `/llm/candidates` API Endpoint。
    *   [ ] `/chat/finish` API Endpoint 及 `workflow_solve_to_end` 实现。
    *   [ ] `Block.altOutputs` 存储和 `Block.modelUsed` 记录。
*   **前端**:
    *   [ ] `AltOutputModal` 组件，展示多模型候选并允许用户选择。
    *   [ ] `ChatCommandBar` 中"全部解答"按钮及 `Auto-select` Checkbox 逻辑。

**阶段 5: 辅助功能与高级特性 (对应时序图 #11, #12 及其他)**
*   **目标**：实现历史总结、答案解析导入等，并完善系统。
*   **后端 & 前端**:
    *   [ ] `summarize_history` Agent 和对应 API/UI。
    *   [ ] `answer_to_steps` Agent 和对应 API/UI (包括图片/音频处理)。
    *   [ ] `Block.isTerminal` 逻辑及其在前端的标记。
    *   [ ] (高级) 成本监控、埋点等。

**快速见效的建议**:
*   **从"阶段 1: 题目上传与展示"入手**。这是最有价值的第一个端到端流程，能让你快速看到实际效果，并验证整个技术栈的基本连通性。
*   之后，可以考虑先做 **"阶段 2"** 中的 **"节点切换 (时序图 #3)"** 和 **"块编辑 (时序图 #4)"**，这些交互相对简单，能丰富 DAG 的可用性。

请将此 README.md 内容保存到你的项目根目录下。这个开发计划提供了一个清晰的路径，你可以根据自己的进度和理解程度来调整每个阶段投入的时间和具体实现顺序。祝你开发顺利！