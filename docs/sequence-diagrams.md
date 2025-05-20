下面是一份可直接放入 docs/sequence-diagrams.md 的完整工作流时序集合（Mermaid + 解释）。我把所有与数据/状态变更相关的操作都列成 12 个核心场景，并在每段下加了 流程验证要点，方便你在单元测试或 Postman 测试时逐项核对。

⸻

目录
	1.	题目上传（problem_ingest）
	2.	题干 LaTeX 手动修改（latex_refine）
	3.	节点切换（node_select）
	4.	块编辑（block_edit）
	5.	块删除（block_delete，级联）
	6.	块解析（block_parse）
	7.	提示思路（suggest_next_moves）
	8.	继续解答（solve_next_step，手动模式）
	9.	继续解答（solve_next_step，Auto-select = false + 候选挑选）
	10.	全部解答（solve_to_end，Auto-select = true）
	11.	总结（summarize_history）
	12.	解析答案导入（answer_to_steps）

⸻

0 通用图例

```mermaid
sequenceDiagram
  participant U as User
  participant FE as Frontend
  participant GW as Gateway
  participant L as LLM-Router
  participant B as Block-Service
  participant D as DAG-Service
  participant E as Event-Bus
```

⸻

1. 题目上传（problem_ingest）

```mermaid
sequenceDiagram
  U->>FE: 拖拽图片 / 语音 / LaTeX
  FE->>GW: POST /problems/ingest  {file/latex}
  GW->>L:  agent=problem_ingest
  L-->>GW: {rawLatex, firstStep}
  GW->>B:  create root & block#1
  B->>E:   publish block_create
  B-->>D:  insert edge(root→#1) & create DagState
  D-->>FE: WS 题干 & block#1 & DAG 布局
  GW-->>FE: HTTP 200
```

**验证要点**

| 检查     | 期望                                        |
| :------- | :------------------------------------------ |
| Event 表 | upload, model_call, block_create 三条       |
| DagState | currentNode = block#1                     |
| Frontend | BlockList 出现首块；DagCanvas 显示根–#1 |

⸻

2. 题干 LaTeX 手动修改（latex_refine）

```mermaid
sequenceDiagram
  U->>FE: 在题干编辑器修改并点击保存
  FE->>GW: PATCH /problems/{id}/latex {latex}
  GW->>L:  agent=latex_refine
  L-->>GW: {latex_refined}
  GW->>B:  update root.latex
  B->>E:   publish edit
  B-->>D:  (无 DAG 变更)
  E-->>FE:  WS push edit
```

**要点**: 只改題幹文本，不改 DAG；如果需重新解析则前端再发 /blocks/:id/parse。

⸻

3. 节点切换（node_select）

```mermaid
sequenceDiagram
  U->>FE: 点击节点 #7
  FE->>GW: PATCH /dag/current/7
  GW->>D:  update DagState.currentNode
  D->>E:   publish node_select
  D-->>FE: WS 发送 新 data2 (路径 root→…→#7)
```

**要点**: data2 刷新 UI；data1/data3 不改。

⸻

4. 块编辑（block_edit）

```mermaid
sequenceDiagram
  U->>FE: 在 BlockCard#5 内编辑 LaTeX
  FE->>GW: PATCH /blocks/5 {latex}
  GW->>B:  update block#5
  B->>E:   publish block_edit
  E-->>FE:  WS 更新块
```

⸻

5. 块删除（block_delete 级联）

```mermaid
sequenceDiagram
  U->>FE: 点击块 #4 的🗑
  FE->>GW: DELETE /blocks/4
  GW->>B:  mark #4 及子孙 state=deleted
  B->>E:   publish block_delete {ids:[4,5,6]}
  B-->>D:  soft-delete edges
  alt currentNode 被删除?
    D->>DagState: 回溯到最近存活父
  end
  D-->>FE: WS 刷新 data2 + DAG
```

⸻

6. 块解析（block_parse）

```mermaid
sequenceDiagram
  U->>FE: 点击 #3 的🪄解析
  FE->>GW: POST /blocks/3/parse
  GW->>L:  agent=block_parse (prompt = latex#3)
  L-->>GW: {explanation, children?}
  GW->>B:  create child block #3a
  B->>E:   publish model_call + block_create
  B-->>D:  edge(3→3a)
  D-->>FE: WS push #3a
```

⸻

7. 提示思路（suggest_next_moves）

```mermaid
sequenceDiagram
  U->>FE: 点击 💡提示思路
  FE->>GW: POST /chat/suggest {promptDraft}
  GW->>L:  agent=suggest_next_moves
  L-->>GW: {suggestions[]}
  GW-->>FE: HTTP 200 suggestions
  FE->>U:  弹出 modal/side-panel
```

**要点**: 不写块、不动 DAG，不触发 block_create。

⸻

8. 继续解答（solve_next_step，Manual 模式）

```mermaid
sequenceDiagram
  U->>FE: 选中一条思路并点击 ▶️继续
  FE->>GW: POST /chat/next {latexSuggestion}
  GW->>L:  agent=solve_next_step
  L-->>GW: {latex,explanation}
  GW->>B:  create new block #k
  B->>E:   publish model_call + block_create
  B-->>D:  edge(curr→k)
  D->>DagState: currentNode = k
  D-->>FE: WS push 新块 & DAG 更新
```

⸻

9. 继续解答（solve_next_step，Auto-select =false + 候选挑选）

```mermaid
sequenceDiagram
  U->>FE: 点击 ▶️继续
  FE->>GW: POST /llm/candidates {agent:"solve_next_step", models:[…]}
  GW->>L:  fan-out 多模型
  L-->>GW:  altOutputs[3]
  GW-->>FE: altOutputs
  U->>FE: 在 AltOutputModal 选择 deepseek 版本
  FE->>GW: POST /blocks  {chosenLatex}
  GW->>B:  create block
  %% (后续同上一个 `solve_next_step` 图)
  B->>E:   publish model_call + block_create %% Assume chosenLatex results in a new block
  B-->>D:  edge(curr→new_block_id) %% Assuming 'curr' is contextually known
  D->>DagState: currentNode = new_block_id
  D-->>FE: WS push 新块 & DAG 更新
```

⸻

10. 全部解答（solve_to_end，Auto-select =true）

```mermaid
sequenceDiagram
  U->>FE: 勾选 ✅Auto-select 后点「全部解答」
  FE->>GW: POST /chat/finish {auto:true}
  loop 若干轮
    GW->>L: solve_next_step
    L-->>GW: top-1 output
    GW->>B: create block
    B->>D: edge
    D->>FE: WS push
  end
  B (最后块) ->> B: set isTerminal=true
  D->>DagState: currentNode = terminal_block_id
```

⸻

11. 总结（summarize_history）

```mermaid
sequenceDiagram
  U->>FE: 点击 📄总结
  FE->>GW: POST /chat/summary
  GW->>L: agent=summarize_history (input=data1,d3)
  L-->>GW: {summary}
  GW-->>FE: HTTP 200 summary
  FE->>U: 显示侧边栏总结
```

⸻

12. 解析答案导入（answer_to_steps）

```mermaid
sequenceDiagram
  U->>FE: 上传解答图片
  FE->>GW: POST /chat/answer_parse {file}
  GW->>L: agent=answer_to_steps
  L-->>GW: {blocks[]}
  GW->>B: mark data2 blocks state=archived
  loop over new blocks
      B->>B: create_block_from_data(new_block_data)
      B->>E: publish block_create
      B->>D: add_edge_for_new_block(new_block_data)
  end
  D->>DagState: currentNode = first_new_block_id
  D-->>FE: WS 全量 refresh
```

⸻

### DAG 实时呈现与交互 —— 推荐现成工具

| 方案             | 为什么合适                                                                                                 | 关键 API / 功能                                                                                                |
| :--------------- | :--------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------- |
| React Flow (MIT) | • React 生态；• 内建缩略图、自动布局（dagre / elk）；• 节点/边类型可自定；• 2 万节点性能可接受                    | `useReactFlow()` 动态增删节点；`fitView` 居中；`onNodeClick` → PATCH /dag/current；Background + MiniMap           |
| ECharts Graph    | • 如果想用非 React 页面也可；• 力导向 / 层次布局可选；• 提供 tooltip/缩放                                        | `setOption({ series: [{type:'graph',data,links}] })`; WS 到来时 diff patch                                   |
| Cytoscape.js     | • 经典图工具；事件丰富；• 集成 dagre / cola layout；• Svelte/Vue/React 均可                                  | `cy.add()`；`cy.on('tap', 'node', ...)`                                                                       |

**推荐实践**
	1.	先用 React Flow + dagre：几乎零配置即可得正交层次图。
	2.	WebSocket 推送的节点/边 diff → `reactFlowInstance.addNodes()` / `addEdges()`。
	3.	将 `currentNode` 高亮：`setNodes(nodes => nodes.map(n=>({...n,selected:n.id===current})))`。
	4.	折叠/展开子树：用 Compound Node 或给节点加"+"/"-"句柄，递归隐藏子孙节点。

⸻

### 流式输出到 data2 的实现关键

```python
# dag_service.py
async def stream_updates(problem_id: UUID):
    async for evt in event_bus.subscribe(problem_id): # Assuming event_bus has a subscribe method
        if evt.type in {"block_create","block_delete","node_select"}:
            path = calc_current_path(problem_id)  # data2
            dag  = fetch_dag_meta(problem_id)     # for DagCanvas
            # yield sse_pack({"path": path, "dag": dag, "evt": evt}) # sse_pack needs to be defined
            # For SSE, content should be formatted like "event: message
data: JSON_STRING

"
            yield f"event: update\ndata: {json.dumps({'path': path, 'dag': dag, 'evt': evt.dict()})}\n\n"

```
**前端**: `useEventSource` 钩子实时合并 state 并刷新 React-Flow 与 BlockList，保证 `data2` 与 `currentNode` 随时同步。

⸻

### 最后提醒
	•	Mermaid 图可直接复制到 GitHub README / HackMD 预览；VS Code 插件也能渲染。
	•	所有 sequence 图均确保 事件写入 → 服务写 DB → DagState 校正 → WS 推前端 这一顺序一致。
	•	若后期出现跨标签页协同，可把 Event-Bus 替换为 Postgres LISTEN/NOTIFY 或 Y.js CRDT，同样兼容 React Flow。

如还需更多细节（布局参数、WS 协议示例、Orchestrator 测试脚本等），随时告诉我！
