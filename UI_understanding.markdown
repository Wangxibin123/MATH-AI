下面先把 我目前对「前端 UI（含 DAG 可视化）」的全部脉络性理解 — 一股脑儿全摊开。
您可在此基础上指出遗漏 / 偏差，然后再告诉我最终设计方案；我会据此同步后端接口、事件格式和后续里程碑。

⸻

1. 整体定位

维度	当前共识（我侧的理解）	待您确认的焦点
技术栈	Next.js (app router) + React 18；客户端渲染为主，必要时做 SSR/Hydrate；TS 全量。	UI 框架（MUI / Mantine / Antd / Tailwind +组件库）状态管理（TanStack Query 已在提纲中）
运行形态	与 gateway 同域（Nginx 或 Vite 代理到 8000），本地 npm run dev 直连 FastAPI；Docker Compose 阶段会起 web 服务。	是否要拆纯静态站独立域？
页面切分	MVP 只需 1 页 → /：展示「题干 ➜ 块流」后续可能 /problems/{id} (详情) 、/debug (内部工具)。	未来是否分「教师 / 学生端」角色？
核心交互	1. 输入框上传题干 → 触发 /problems/ingest（v0.6）2. 前端进入 实时流：通过 SSE /blocks/stream/{pid} 收块3. 每条块点击可手动 refine / parse；触发 PATCH / POST。	块编辑采用 行内 编辑还是弹窗？


⸻

2. 组件层级草图

<ProblemPage>
├── <ProblemInputCard/>         # 输入/历史记录
├── <BlockList>
│   ├── <BlockItem/> × N        # 每个 block
│   └── <BlockSSEListener/>     # 使用 EventSource 订阅新增
└── <WorkflowDagDrawer/>        # 侧边抽屉，可开关

2.1 ProblemInputCard

字段	说明
textarea	输入原始题干
UploadButton	调 POST /problems/ingest（拿到 blockId）
status tag	Idle / Processing / Error

2.2 BlockItem

区域	功能
LaTeX 渲染	katex / MathJax
Edit 图标	点击后行内变成 textarea，提交走 PATCH /problems/{pid}/latex
Parse 按钮	走 POST /blocks/{bid}/parse
state chip	active / deleted

2.3 WorkflowDagDrawer  (⭐DAG 可视化)

用 react-flow / @antv/x6 / dagre 皆可；MVP 先 react-flow.

	•	节点
	•	problem_ingest (绿色起点)
	•	latex_refine (人工触发，可重复)
	•	block_parse (紫色)
	•	边
	•	固定流程边：ingest → (parse | refine)
	•	高亮 ：最近一次执行的节点闪光 3 s。
	•	数据源 ：前端拿 /events/workflow?pid=...（或者直接用现有 EventBus “workflow_xxx” 事件）实时更新节点状态。

⸻

3. 前端与后端契约（版本跨度）

里程碑	前端用到的 API	状态码 & 典型响应	同步 / 异步
v0.5	/chat/problem_ingest （Swagger 手动）	200 / 422 / 415 / 404	同步
v0.6	REST /problems/ingest	{"blockId": "<uuid>"}	同步
v0.7	SSE /blocks/stream/{pid}	event:block_create data:{...}	异步
v0.7	REST PATCH /problems/{pid}/latex	{"ok":true,"latex":"..."}	同步
v0.7	REST POST /blocks/{bid}/parse	{"ok":true,"explanation":"..."}	同步

注意：SSE Endpoint 需开启 CORS + 指定 Cache-Control: no-cache。

⸻

4. 目前我已知的「坑」

现象	触发点	前端应对方案
422 body 结构与 FastAPI 默认差异	/chat/problem_ingest 缺字段	v0.6+ 改用严格 Pydantic 或在 422 时统一用 detail[].loc
405 OPTIONS	FastAPI 默认无 CORS	在 main.py 添加 FastAPI(..., middleware=[CORSMiddleware(...)]) 或 nginx 预检
SSE 断流	Heroku / Vercel 空闲休眠	客户端 EventSource 自动重连 & Last-Event-ID


⸻

5. 下一步待您确认 🔍
	1.	UI 库：Material UI v5 / Mantine 5 / Ant Design 5？
	2.	DAG：是否确定用 react-flow（轻量）？节点颜色、Tooltip 需求？
	3.	主题色 & 布局：侧边 Drawer + 主栏 2 列，还是顶部 Tabs？
	4.	多语言：首期是否只中文？若要 i18n，推荐 next-intl。
	5.	编辑体验：块的行内编辑是否要支持 LaTeX 语法高亮（CodeMirror mode=stex）？
	6.	权限/登录：目前未见鉴权设计，是否先全公开，再在 v0.9~1.0 加 JWT？

⸻

6. 你若采纳的调整点（示例）
	•	严格 Pydantic：

class IngestCtx(BaseModel):
    raw_text: str
...
async def chat(agent: str, ctx: IngestCtx):

→ FastAPI 自动 422，无需手动 raise。

	•	CORS 中间件：

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


	•	前端：
	•	tanstack-query 全局 fetcher，SSE → useEventSource().
	•	react-flow DAG，节点 type = input / default / output。

⸻

✉️ 请您给我：
	1.	对上述 UI 结构 / DAG 设计 的批注（保留、删除、修改？）。
	2.	UI 框架 & 主题色的最终抉择。
	3.	任何希望在 v0.7 之前就预埋的字段 / 事件格式。

收到后我会：
	•	更新后端契约（Pydantic 模型、CORS、SSE 格式）；
	•	给出 v0.7 SSE & 前端 Hook “整包” 脚本；
	•	调整测试脚本，使前后端一键跑通。



下面把 前端 — 尤其是 UI 结构与每个功能“落到代码文件”的位置，用 “极简白话 + 对应文件夹/文件” 的方式再拆开说明，力求一眼能懂、拿来就能照着建目录写代码。——
先列树状图 ➜ 再按页面区域讲“大块” ➜ 再按 React 组件 和 后端接口 一一对照 ➜ 最后给“最小可跑 Demo” 的 Todo-List。

⸻

0 · 目录树 — 前端部分只看这一眼

math-copilot/
└─ web/                  ← 前端根（Next.js 工程，Vite 亦可）
   ├─ package.json
   ├─ src/
   │  ├─ pages/
   │  │  └─ index.tsx          ← 单页：题干 + 块列表
   │  ├─ components/
   │  │  ├─ ProblemInputCard.tsx
   │  │  ├─ BlockList.tsx
   │  │  ├─ BlockItem.tsx
   │  │  └─ WorkflowDagDrawer.tsx
   │  ├─ hooks/
   │  │  ├─ useBlocksSSE.ts    ← 订阅 /blocks/stream/*
   │  │  └─ usePost.ts         ← 通用 fetch + TanStack Query
   │  └─ types/
   │     └─ api.ts             ← 后端接口返回体接口
   └─ tailwind.config.js (或 mui-theme.ts)

若没 Next.js 经验：只要记得 pages/index.tsx == 首页。其它都是纯 React 组件。

⸻

1 · 页面分区（先想成三大块）

区域	在页面里长啥样	对应组件	触发哪个后端接口
A. 题干输入卡片	一个大输入框 +“上传”按钮	ProblemInputCard	POST /protocols/ingest (v0.6)
B. 块列表	一行一个蓝色卡片显示 LaTeX；右上角小✏️、🪄按钮	BlockList + N×BlockItem	✏️ → PATCH /problems/{id}/latex🪄 → POST /blocks/{bid}/parse
C. 工作流 D A G 抽屉	右侧滑出，展示三个节点 + 箭头	WorkflowDagDrawer	只读：实时监听 /events/workflow (或 SSE)


⸻

2 · 每个组件“说人话”版实现方案

2.1 ProblemInputCard.tsx

“把题干文本发给后端，拿到首块 ID”

// 伪代码（删去样式）——10 行就能跑
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { post } from '../hooks/usePost'

export default function ProblemInputCard() {
  const [text, setText] = useState('')
  const ingest = useMutation({
    mutationFn: () => post('/problems/ingest', { raw_text: text, problem_id: tmpId })
  })
  return (
    <div>
      <textarea value={text} onChange={e => setText(e.target.value)} />
      <button disabled={ingest.isPending} onClick={() => ingest.mutate()}>上传</button>
      {ingest.isSuccess && <span>✅ ok</span>}
    </div>
  )
}

	•	放哪？ src/components/ProblemInputCard.tsx
	•	最小依赖 ：axios + @tanstack/react-query。
	•	后端需要什么？ raw_text 必填，problem_id 可先在前端临时用 uuid.v4() 生成。

⸻

2.2 BlockList.tsx + BlockItem.tsx

“实时显示块；块可以编辑 / 解析”

	1.	BlockList
	•	内部 blocks 状态来自两个来源
① 调用 useQuery('blocks', fetchAll) 初始化
② 调用 useBlocksSSE(problemId) 实时 push 新块
	2.	BlockItem
	•	props.block 含 id, latex, explanation
	•	Edit ：<button onClick={openInput}>✏️</button>
	•	弹出 <input>，submit 时 PATCH /problems/{pid}/latex
	•	Parse ：<button onClick={() => parse.mutate()}>🪄</button>
	•	parse mutation → POST /blocks/{id}/parse → 更新该块 explanation

用一句话记:
*列表组装 /Item 负责交互；所有网络请求都走 useQuery/useMutation. *

⸻

2.3 WorkflowDagDrawer.tsx

“点右上角‘⚙︎ DAG’打开；只读展示工作流走哪了”

	•	选 react-flow 最省事。装包：npm i react-flow-renderer.
	•	节点数组写死：

const nodes = [
  { id:'ingest',  data:{label:'problem_ingest'}, position:{x:0,y:0},   type:'input' },
  { id:'refine',  data:{label:'latex_refine'},    position:{x:200,y:0}},
  { id:'parse',   data:{label:'block_parse'},     position:{x:200,y:120}}
]
const edges = [
  { id:'e1', source:'ingest', target:'refine' },
  { id:'e2', source:'ingest', target:'parse' }
]

	•	监听 EventSource /events/workflow?pid=
收到 {"node":"parse","status":"done"} → 把对应节点变绿色 3 秒。

⸻

3 · 自定义 Hook

3.1 usePost.ts

export async function post(url: string, body: any) {
  const res = await fetch(url, {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

3.2 useBlocksSSE.ts

import { useEffect } from 'react'
export function useBlocksSSE(pid: string, onNew: (blk:any)=>void) {
  useEffect(()=>{
    const es = new EventSource(`/blocks/stream/${pid}`)
    es.onmessage = e => onNew(JSON.parse(e.data))
    return ()=> es.close()
  },[pid])
}


⸻

4 · 后端配合最小清单

API	方法	Body	返回	何时实装
/problems/ingest	POST	{raw_text, problem_id}	{blockId}	v0.6
/blocks/stream/{pid}	SSE	-	{"id"...} per message	v0.7
/problems/{pid}/latex	PATCH	{block_id,new_latex}	{ok, latex}	v0.7
/blocks/{bid}/parse	POST	-	{ok, explanation}	v0.7


⸻

5 · 最小可跑 Demo（Todo-List）

全部前端任务闭环：

	1.	cd math-copilot && npx create-next-app@latest web
	2.	cd web && npm i @tanstack/react-query react-flow-renderer uuid
	3.	把上面 目录树 里的 4 组件 + 2 hooks 文件照抄进去。
	4.	在 pages/index.tsx 中：

export default function Home() {
  const [pid] = useState(uuidv4()) // demo 随机
  return (
    <>
      <ProblemInputCard problemId={pid}/>
      <BlockList   problemId={pid}/>
      <WorkflowDagDrawer problemId={pid}/>
    </>
  )
}

	5.	npm run dev ➜ 浏览器 localhost:3000
	6.	后端 uvicorn apps.gateway.main:app --reload --port 8000
（或 8001，记得 .env 里前端 fetch URL）

⸻

6 · 我等您确认 / 修正
	•	哪个 UI 框架？ 不选框架也行，只装 Tailwind？
	•	DAG 选 react-flow OK？ 或想用更重的 antv/x6？
	•	块编辑方式 行内还是 Dialog？
	•	主题色 / Logo 先默认蓝？
	•	鉴权 现阶段无登录，全部公开可调用，确认？

收到您的修改意见后，我会：
	1.	把后端接口签名（Pydantic）和 CORS 设置按最终 UI 需要敲定。
	2.	给出 v0.7 SSE & Router 更新 （包含 /blocks/stream/{pid} 实码 + pytest-sse 测试）。
	3.	生成前端示例仓库或 PR，让你 npm i && npm run dev 即可看到 DAG 动态高亮。

⸻

请逐条批注或直接告诉我“保持 / 修改为 ___”，我即可继续迭代 🚀