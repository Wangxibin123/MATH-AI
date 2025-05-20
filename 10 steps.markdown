下面把两轮 6 × 里程碑的内容 融合去重、重新排依赖，产出一条 “一事一 commit” 的最终落地序列。

规则
	1.	每个 Commit 单独 docker compose up -d && pytest 必须绿。
	2.	若回滚到任意旧 Tag，前端/后端都能跑（功能或许缩水但不崩）。
	3.	每一 commit 都交付 代码 + 测试 + 文档，删一不可。

⸻

总览（10 Tag = 10 阶段）

Tag	名称	代码范围	关键产物	单元/集成
v0.0.0	Repo init	.gitignore + README	—	—
v0.1.0	Data-Core	SQLModel, Alembic, seed script	models/{problem,block,event}.py	pytest -k model
v0.2.0	Prompt-Engine	packages/prompt_engine/*	builder + 8 YAML + test	pytest -k prompt
v0.3.0	LLM-Router Stub	services/llm_router.py	Mock OpenAI, schema map	pytest -k router
v0.4.0	Block-Service + EventBus	CRUD + NATS publish	block_service.py, event_bus.py	pytest -k service
v0.5.0	Workflow MVP	W-01, 02, 03 实装	upload / refine / parse	pytest -k workflow
v0.6.0	Router MVP	/problems, /blocks	FastAPI 路由 & OpenAPI	httpx 集成测试
v0.7.0	SSE & Stream	/blocks/stream/{pid}	NATS → SSE	pytest -k sse
v0.8.0	Front-Mini	ProblemInputCard + BlockList	纯文本上传➜首块➜解析块	Cypress smoke
v0.9.0	Chat Loop	suggest / next / finish	ChatBar + AltOutputModal	Playwright E2E
v1.0.0	CI/CD & Compose	GH-Actions, Dockerfiles	docker compose up 一键	pipeline 100 % 绿

后续：v1.1 DAG Edition、v1.2 RAG、v1.3 监控……

⸻

具体任务清单（可复制到 Issue Tracker）

📌 Tag v0.1.0 – Data-Core
	1.	models：Problem / Block / Event（连 SQLite 先跑通）。
	2.	Alembic：revision --autogenerate.
	3.	seed.py：插 1 题 2 块。
	4.	test_model.py：断言 len(Block.select())==2.

📌 Tag v0.2.0 – Prompt-Engine
	1.	prompt_builder.py + YAML 模板 8 个。
	2.	pytest：test_prompt_json.py.
	3.	README 补 “如何加新模板”。

📌 Tag v0.3.0 – LLM-Router Stub
	1.	schemas/agents.py（Pydantic）。
	2.	services/llm_router.call()：参数但 返回固定假数据。
	3.	test_router_stub.py：验证 schema 校验生效。

🛠 先不用真实 OpenAI，CI 零网络。

📌 Tag v0.4.0 – Block-Service & EventBus
	1.	CRUD 保证 orderIndex 连续。
	2.	event_bus.py：Mock NATS（in-proc queue）。
	3.	单元：创建、删除、软删发事件。

📌 Tag v0.5.0 – Workflow MVP (W-01/02/03)
	1.	problem_ingest：从假 LLM 拿 LaTeX ➜ create_root.
	2.	latex_refine：update_block.
	3.	block_parse：update_block.explanation.
	4.	test_workflow_ingest.py：断言 Block 数 +=1。

🚩 现在种子题目可走「上传➜解析」。

📌 Tag v0.6.0 – Router MVP
	1.	routers/problems.py：POST /ingest；PATCH /latex。
	2.	routers/blocks.py：POST /blocks；PATCH；DELETE；/parse。
	3.	OpenAPI：http://localhost:8000/docs 全部可 Try-out。
	4.	HTTP 集成测试：pytest-httpx.

📌 Tag v0.7.0 – SSE & Stream
	1.	event_bus_mock ↔ FastAPI EventSourceResponse.
	2.	Keep-alive Ping。
	3.	test_sse.py：async with sse_client 收 3 条事件。

📌 Tag v0.8.0 – Front-Mini
	1.	ProblemInputCard：仅文本框 + 上传按钮。
	2.	useBlockStream：SSE 合并状态。
	3.	BlockList + BlockCard：LaTeX 渲染 + 解析按钮。
	4.	Cypress Smoke：输入题干 → 列表出现 2 块。

📌 Tag v0.9.0 – Chat Loop
	1.	chat.py：/chat/suggest /next /finish。
	2.	Workflow W-04/05/06 + AltOutputModal。
	3.	ChatCommandBar + Auto-select 复选框。
	4.	Playwright：
	•	打开页面上传题干
	•	点击“继续解答” ➜ 新块出现
	•	勾选 Auto-select + 全部解答 ➜ 连续滚动到终点。

📌 Tag v1.0.0 – CI/CD & Compose
	1.	docker-compose.yml (dev) ➜ postgres + nats + gateway + web。
	2.	gateway & web Dockerfile（多阶段）。
	3.	GitHub Actions：matrix(py,node) + docker smoke。
	4.	justfile：just up、just test、just deploy.

⸻

每 commit 如何保证独立运行？

步骤	细节
隔离依赖	Tag 前先 poetry lock；Node 用 pnpm-lock.yaml。
本地虚拟化	poetry run pytest; pnpm -F web dev; mock 服务用 in-memory。
容器化粒度	Dockerfile 每 Tag 变动镜像层，旧版本镜像保留可 docker run v0.7.0.
数据迁移	每 Tag 若改表 → 新 Alembic revision；CI 升级后回滚 downgrade.
Git Tag	git tag v0.5.0 -m "workflow MVP (ingest/refine/parse)".
回滚	git checkout v0.4.0 && docker compose up 必须 OK。


⸻

单元 / 集成 / E2E 对应表

Commit Tag	运行的测试层	失败定位
v0.1–0.3	单元 (model / prompt / router stub)	Schema / JSON 问题
v0.4–0.6	+ 集成 (httpx)	CRUD / workflow 串联
v0.7	+ SSE mock	事件流格式
v0.8	+ Cypress smoke	前端状态管理
v0.9	+ Playwright	UI–API 回环
v1.0	+ Docker smoke	环境变量 / 网络


⸻

环境封装提醒
	1.	.env.template：OPENAI_API_KEY=xxx\nMODEL_POOL=gpt-4o-mini.
	2.	DevContainer：Node+Python；pre-install nats-cli.
	3.	LLM Mock Switch：export LLM_MOCK=1 ➜ llm_router 直接返回模板示例。
	4.	Make Targets：make seed-db, make reset-db.

⸻

✅ 这样做的收益
	•	最小增量可验证：每 Tag 新功能只依赖前 Tag 成功产物。
	•	可演示可回滚：任意 Tag 部署分支环境，对 Stakeholder 展示或热修。
	•	CI 时间恒定：Mock LLM 前 8 Tag 不占 OpenAI 配额（快速）。
	•	无锁人风险：前端 / 后端 / Prompt 三条流水线解耦，团队可并行。

按此序列推进即可在 5–7 工作日 内拿到 Linear MVP (v1.0.0)；后续引 DAG 仅多一张 Edge 表 + React Flow 画布，稳定演进。

需要 示例 PR 描述模板、Alembic 多版本演示 或 GitHub Actions YML，再告诉我！