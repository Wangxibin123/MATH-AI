下面把 Math Copilot 整个产品在"和大模型对话"这一层需要落地的 工作流 (workflow) 与 Prompt 族 (prompt family) 全部拆解；最终给出两张核心表格：
	1.	⊕ 工作流清单：哪些功能必须写成可复用 workflow——包含触发条件、子步骤、依赖服务。
	2.	⊕ Prompt 适配矩阵：每个 workflow 里需要准备多少「同质但不同场景」的 Prompt 模板（即 prompt variant），并说明变体出现的 分界条件（如输入模态、题型、上下文深度等）。

⸻

## 1. 工作流总览 (Workflow Overview)

| #    | Workflow (Dir Path Suggestion) | 触发对象                | 主要子步骤                                     | 关键依赖                                     | 终态输出             |
| :--- | :----------------------------- | :---------------------- | :--------------------------------------------- | :------------------------------------------- | :------------------- |
| W-01 | `workflow/problem_ingest.py`   | 上传题目 (图 / 文 / 音) | ① 多模态转文本+LaTeX<br>② 初步题型分类<br>③ 生成首 Block | OpenAI GPT-4o vision，PaddleOCR 备用        | rawLatex, Block#1    |
| W-02 | `workflow/latex_refine.py`   | 题干手动改动后保存      | ① LaTeX 纠错<br>② optionally 重新分类            | GPT-4o-Turbo                                 | 规范化 LaTeX         |
| W-03 | `workflow/block_parse.py`    | Block 解析              | ① 逻辑解释<br>② (可选) 产出子块                   | GPT-4o / DeepSeek-v2                         | explanation / 子块   |
| W-04 | `workflow/suggest_next.py`   | 💡提示思路             | ① RAG 检索<br>② 可行性排序                      | GPT-4o + 向量库                              | suggestions[]        |
| W-05 | `workflow/next_step.py`      | ▶️继续解答            | ① 选思路<br>② 推导一步<br>③ 写新块                 | 同 W-04                                      | Block 新节点         |
| W-06 | `workflow/solve_to_end.py`   | ✅全部解答             | ① 循环 W-05<br>② 终点检测                        | LLM-router & Auto-select                     | terminal path        |
| W-07 | `workflow/summarize.py`      | 📄总结                 | ① 历史事件聚合<br>② 层次摘要                     | GPT-4o mini                                  | summary              |
| W-08 | `workflow/answer_parse.py`   | 🖼/📋答案导入          | ① 图/文 → LaTeX<br>② 拆步为块                    | GPT-4o vision                                | 新路径 Blocks        |
| W-09 | `workflow/candidates.py`     | /llm/candidates API     | ① 多模型并发<br>② 打分归一<br>③ 返回 altOutputs     | GPT-4o / DeepSeek-v2 / Claude / Gemini…        | altOutputs           |
| W-10 | `workflow/dag_collapse.py`   | ⊖ 折叠/展开            | ① 递归标记 hidden<br>② 重算布局                  | React-Flow，本地 (非 LLM)                    | DAG 状态             |
| W-11 | `workflow/rag_search.py`     | Suggest/Rerank 时      | ① 向量召回<br>② 句向量 rerank                    | Milvus, SBERT (非 LLM)                       | contexts[]           |

**备注**: W-10 (DAG 操作) 和 W-11 (RAG 搜索) 本身不直接调用 LLM，但它们的结果或状态会影响其他 LLM 相关工作流的上下文构建，特别是 Prompt variant 的选择（例如，RAG 检索的结果会进入 Prompt；DAG 的折叠状态可能决定上下文裁剪策略）。

⸻

## 2. Prompt 适配矩阵 (Prompt Adaptation Matrix)

每一行代表一个核心 Agent (通常对应一个 function-name 或主要 workflow)；每一列代表一个决定是否需要独立 Prompt 变体的情景维度。
交叉单元格给出建议的变体数量（1 = 单一模板即可；2+ = 建议为该维度下的不同情况编写独立的模板）。

| Agent / 维度         | 输入模态 (图/文/音) | 题型 (极限/解析几何/概率…) | 上下文深度 (≤5 块 / >5 块) | RAG 命中 (有/无) | Auto-select (on/off) | 总需模板数 (估算) |
| :------------------- | :------------------: | :-----------------------: | :----------------------: | :--------------: | :------------------: | :----------------: |
| `problem_ingest`     | 3                    | 1                         | 1                        | —                | —                    | 3                  |
| `latex_refine`       | 1                    | 1                         | 1                        | —                | —                    | 1                  |
| `block_parse`        | 1                    | 2 (常规 vs 几何图)        | 1                        | —                | —                    | 2                  |
| `suggest_next_moves` | 1                    | 3 (代数/几何/统计)        | 2                        | 2                | —                    | 12 (1×3×2×2)       |
| `solve_next_step`    | 1                    | 3                         | 2                        | 2                | 2                    | 24 (1×3×2×2×2)     |
| `solve_to_end`       | 1                    | (复用 `solve_next_step`)  | (复用 `solve_next_step`) | (复用 `solve_next_step`) | (复用 `solve_next_step`) | 24 (循环复用)    |
| `summarize_history`  | 1                    | 1                         | 2 (短/长)                | —                | —                    | 2                  |
| `answer_to_steps`    | 3 (图/文/Latex)      | 2 (选择题/解答题)         | 1                        | —                | —                    | 6                  |
| `candidates` (评估)  | 1                    | 1                         | 1                        | —                | —                    | 1 (非生成 Prompt)  |

### 2.1 维度解释

| 维度         | 为什么要拆分出不同 Prompt 变体？                             | 触发条件示例                                      |
| :----------- | :----------------------------------------------------------- | :------------------------------------------------ |
| 输入模态     | 图片/文本/语音的前置处理不同；图示题目需要 vision tokens       | 用户上传的是试卷截图 vs 纯 LaTeX 文本             |
| 题型         | 不同题型（如高考的解析几何与概率统计）的解题思路、常用公式、关键定理差异大；针对性的提示词能提升效果 | 用户输入"抛物线焦点"相关内容，触发几何专用模板    |
| 上下文深度   | 上下文过长时，为控制 token 数量和保持模型注意力，应进行截断或让模型仅关注最近 n 步 | 当前解题路径中的 Block 数量 > 5                   |
| RAG 命中     | 当从向量库中召回相关参考资料时，应在 Prompt 中提示模型"你可以参考以下资料…"，若无召回则省略此部分 | `contexts[]` 数组长度 > 0 (即 RAG 找到了内容)   |
| Auto-select  | 决定是否在提示中明确要求模型「输出 top-k 并给出评估分数」或「仅需给出最佳的一步推导」 | `solve_next_step` 或 `solve_to_end` 工作流中的 `auto` 参数状态 |

### 2.2 Prompt 模板层级结构

一个完整的 Prompt 通常由以下几个部分动态组合而成：

1.  **System Prompt (系统级提示)**: 每个 Agent 通常有一个固定的 System Prompt，定义其角色和高级指令。
2.  **Scene Prompt (场景化提示)**: 根据上述五个维度的具体组合，从预定义的模板库中选择一个场景化 Prompt。这些模板可以存储在如 `prompts/{agent_name}/` 目录下，通过文件名或元数据来区分不同场景。
3.  **Few-shot 示例 (可选)**: 根据题型或特定场景，动态地从示例库中挑选并插入若干高质量的 Few-shot 示例，以引导模型输出更符合期望的格式和内容。
4.  **User Content (用户实时内容)**: 将用户当前的输入（如题干 LaTeX、已完成的解题步骤、RAG 检索到的上下文等）实时拼接到 Prompt 中。
5.  **Function Schema (函数调用定义)**: 如果使用 OpenAI Function Calling 或类似机制，还需要提供 JSON Schema 来定义期望模型输出的结构。

⸻

## 3. Prompt 模板管理策略

建议的目录结构示例：

```
prompts/
 ├─ problem_ingest/
 │   ├─ img.yaml
 │   ├─ text.yaml
 │   └─ audio.yaml
 ├─ block_parse/
 │   ├─ default.yaml
 │   └─ geometry.yaml
 ├─ suggest_next_moves/
 │   ├─ algebra_short_rag.yaml
 │   ├─ algebra_short_no_rag.yaml
 │   ├─ algebra_long_rag.yaml
 │   ├─ algebra_long_no_rag.yaml
 │   ├─ geometry_short_rag.yaml
 │   └─ ... (以此类推，覆盖所有维度组合)
 └─ ... (其他 Agent 的 Prompt 模板)
```

*   **命名约定**: 可以使用 `agentName_type_depth_rag_auto.yaml` 这样的命名方式，其中某些维度对于特定 Agent 可能不存在。
*   **回落机制 (Fallback)**: 如果某个特定的维度组合没有精确匹配的模板文件，系统应能回落到一个该 Agent 的 `default.yaml` 或更通用的模板。
*   **模板引擎**: 模板文件内部可以使用如 `{{placeholder}}` 这样的占位符（类似 Jinja2 或 Handlebars 语法），由 `PromptBuilder` 在运行时动态填充具体内容。
*   **内容格式**: YAML 文件可以很好地组织 Prompt 的不同部分 (e.g., `system_message`, `user_message_template`)。

⸻

## 4. Prompt Builder 核心代码骨架

```python
import yaml
import os
from typing import List, Dict, Any

PROMPTS_DIR = "prompts" # 定义模板存放的根目录

def load_yaml_or_fallback(agent: str, meta: Dict[str, str]) -> Dict[str, str]:
    """根据 meta 信息构造文件名并加载 YAML 模板，失败则回落到 default.
       更复杂的场景可能需要更精细的回落逻辑。
    """
    # 构建一个基础文件名，例如：algebra_short_rag_on
    # 注意：不是所有 meta key 都会参与文件名构造，取决于该 agent 的维度
    # 例如，problem_ingest 主要看 modality
    # suggest_next_moves 主要看 type, depth, rag
    
    # 简化版 key 构造逻辑 (需要根据实际 agent 维度细化)
    parts = [meta.get('type', 'default')]
    if 'depth' in meta: # 假设 depth, rag, auto 对很多 agent 通用
        parts.append(meta['depth'])
    if 'rag' in meta:
        parts.append('rag' if meta['rag'] == 'yes' else 'no_rag')
    if meta.get('auto') == 'on':
        parts.append('auto_on')
    
    filename_parts = [p for p in parts if p] # 过滤掉 None 或空字符串
    specific_filename = "_".join(filename_parts) + ".yaml"
    
    # problem_ingest 特殊处理 modality
    if agent == 'problem_ingest' and 'modality' in meta:
        specific_filename = meta['modality'] + ".yaml"
    elif agent == 'block_parse' and 'type' in meta and meta['type'] == 'geometry':
         specific_filename = "geometry.yaml"

    filepath = os.path.join(PROMPTS_DIR, agent, specific_filename)
    default_filepath = os.path.join(PROMPTS_DIR, agent, "default.yaml")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: Specific prompt template '{filepath}' not found. Falling back to default.")
        with open(default_filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading prompt template: {e}")
        # 在实际应用中，这里可能需要更健壮的错误处理，比如返回一个安全的空模板或抛出异常
        return {"system": "Error: System prompt missing.", "scene": "Error: Scene prompt missing."}

def build_prompt_messages(agent: str, meta: Dict[str, str], context_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    构建发送给 LLM 的 messages 列表。

    Args:
        agent: Agent 名称，用于定位模板目录。
        meta: 描述当前情景的元数据字典，用于选择正确的 Prompt 变体。
              例如: {
                  'modality': 'img'|'text'|'audio', (for problem_ingest)
                  'type': 'geometry'|'algebra'|'stats', (for suggest_next_moves, solve_next_step)
                  'depth': 'short'|'long',
                  'rag': 'yes'|'no',
                  'auto': 'on'|'off' (for solve_next_step when in solve_to_end)
              }
        context_data: 包含所有需要注入到 Prompt 模板中的动态内容。
                      例如: {'problem_brief': '...', 'path_tail': '...', 'rawLatex': '...', ...}

    Returns:
        A list of message dictionaries, e.g.,
        [{"role":"system","content":"..."}, {"role":"user","content":"..."}]
    """
    template_content = load_yaml_or_fallback(agent, meta)
    
    system_prompt = template_content.get("system", "")
    scene_template = template_content.get("scene", "") # Scene template from YAML
    
    # 使用 context_data 填充 scene_template 中的占位符
    # 注意: 要确保 context_data 包含了 scene_template 中所有需要的 key
    # 可以使用更安全的格式化方法，比如 string.Template 或 Jinja2
    try:
        user_content = scene_template.format(**context_data)
    except KeyError as e:
        print(f"Warning: Missing key '{e}' in context_data for scene template. Check template and context.")
        user_content = scene_template # 或者进行其他错误处理

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_content:
        messages.append({"role": "user", "content": user_content})
        
    # 此处还可以根据需要添加 few-shot examples 到 messages 中
    # few_shot_examples = load_few_shot_examples(agent, meta) 
    # messages.extend(few_shot_examples) # before the final user message or interleaved

    return messages

```

⸻

## 5. 示例：`suggest_next_moves` Agent 的两套模板对比

**`prompts/suggest_next_moves/algebra_short_rag.yaml`**

```yaml
system: |
  你是一位擅长高考代数的教练，请仅输出**下一步可能的 LaTeX 公式**数组，
  不要解释，不要加文字。
scene: |
  题目摘要：
  {{problem_brief}}

  已完成步骤（最近 {{path_tail_length}} 步）：
  {{path_tail}}

  可参考资料：
  {{rag_context}}

  要求：给出 3–5 个可行的下一步公式（LaTeX），按从易到难排序。
```

**`prompts/suggest_next_moves/geometry_long_no_rag.yaml`**

```yaml
system: |
  你是一位精通高中平面几何与立体几何的专家，任务是基于当前完整的题目和解题路径，
  提供 3 条具有启发性的、不同方向的下一步推导公式。
  请只输出 LaTeX 公式，每个公式一行。
scene: |
  题目全文：
  {{rawLatex}}

  当前解题路径（已完成 {{actual_depth}} 步，显示最近 {{path_tail_length}} 步）：
  {{path_tail}}

  请考虑辅助线构造、向量法、坐标系建立、面积法、体积法、投影变换、等角代换等几何常用思路，
  输出 3 条具有方向性的下一步推导公式（纯 LaTeX）。
```

⸻

## 6. 工作流 ↔ Prompt 变体对照表 (总结)

| Workflow (W-ID)        | 核心调用的 Agent     | 预计需覆盖的 Prompt Variant 数 (来自矩阵) |
| :--------------------- | :------------------- | :---------------------------------------- |
| W-01 `problem_ingest`  | `problem_ingest`     | 3                                         |
| W-02 `latex_refine`    | `latex_refine`       | 1                                         |
| W-03 `block_parse`     | `block_parse`        | 2                                         |
| W-04 `suggest_next`    | `suggest_next_moves` | 12                                        |
| W-05 `next_step`       | `solve_next_step`    | 24                                        |
| W-06 `solve_to_end`    | `solve_next_step`    | 24 (复用 `solve_next_step` 的变体)        |
| W-07 `summarize`       | `summarize_history`  | 2                                         |
| W-08 `answer_parse`    | `answer_to_steps`    | 6                                         |
| W-09 `candidates`      | (内部逻辑，非Agent)  | 1 (指评估逻辑，非生成 Prompt)             |

⸻

## 7. 构建顺序建议 (LLM Prompt Engineering)

这是一个不包含具体日期，但有先后顺序的建议，用于逐步构建和优化 Prompt 系统：

1.  **基础框架搭建**: 实现 `PromptBuilder` 的核心逻辑 (如 `build_prompt_messages` 和 `load_yaml_or_fallback`)。为每个 Agent 创建一个最基础的 `default.yaml` 模板，确保主流程能跑通。
2.  **单模态与核心场景验证**: 首先确保纯文本输入 (`modality='text'`) 的核心工作流能正常工作，例如 W-01 (文本题目上传), W-04 (`suggest_next_moves` 的基础版), W-05 (`solve_next_step` 的基础版)。这是最快见到效果的路径。
3.  **多模态能力补齐**: 逐步为 `problem_ingest` (W-01) 和 `answer_to_steps` (W-08) 补充处理图片 (`modality='img'`) 和音频 (`modality='audio'`) 的 Prompt 变体。这可能需要与多模态模型 (如 GPT-4o Vision) 对接。
4.  **题型维度扩展**: 针对 `block_parse`, `suggest_next_moves`, `solve_next_step`，优先实现对主要题型（如代数、几何）的 Prompt 变体。其他细分题型可以后续补充。测试不同题型下，模型是否能理解特定领域的术语和常用解法。
5.  **上下文深度处理**: 为需要长上下文的 Agent (如 `suggest_next_moves`, `solve_next_step`) 实现根据 `depth` (short/long) 自动切换不同 Prompt 变体的逻辑。这可能涉及到对输入上下文进行截断或摘要的策略，并在 Prompt 中给予不同指示。调整 `token window` 相关的参数。
6.  **RAG 集成与 Prompt 适配**: 在向量数据库和 RAG 检索流程 (W-11) 实现后，为 `suggest_next_moves` 和 `solve_next_step` 等 Agent 增加 `rag='yes'` 和 `rag='no'` 的 Prompt 分支。当 RAG 命中时，在 Prompt 中明确引导模型参考提供的资料。
7.  **Auto-select 语义优化**: 针对 `solve_next_step` (在 W-06 `solve_to_end` 中被循环调用时，通常 `auto='on'`)，优化其 Prompt 变体，使其在 `auto='on'` 时更倾向于直接输出最佳的一步，而不是输出多个候选或评估分数。
8.  **多模型 Router 与 `candidates` 工作流 (W-09)**: 在 `LLM-Router` 的 `fanout_call` 功能完善后，主要调整的是调用逻辑和 `meta` 参数的传递，通常不需要为 `candidates` 这个评估流程本身增加新的生成类 Prompt 模板。
9.  **持续迭代与 A/B 测试**: Prompt Engineering 是一个持续优化的过程。建立评估指标，对不同的 Prompt 变体进行 A/B 测试，根据效果不断调整。

⸻

**最后提示**

*   **模板即代码**: 将 Prompt 模板（如 YAML 文件）视为代码的一部分进行管理。使用版本控制 (Git)，方便追踪变更、回滚和进行 A/B 测试分支。
*   **复用与模块化**: `solve_to_end` 工作流不应创建全新的 Prompt 模板集，而是应复用 `solve_next_step` 的模板，通过在循环中调整 `meta` (如 `auto='on'`) 来控制其行为。
*   **性能与成本考量**: 虽然 Prompt 变体可能很多，但在运行时，`PromptBuilder` 应确保只加载和格式化当前场景命中的那一个模板。避免将所有可能的文本片段都塞在同一个 LLM 请求中，这会严重影响性能和成本。
*   **Few-shot 示例库**: 考虑建立一个按题型、难度等分类的 Few-shot 示例库，`PromptBuilder` 可以根据 `meta` 动态选择合适的示例注入到 Prompt 中，以进一步提升模型表现。

如需我 给出任意一套完整模板示例文件 或 `PromptBuilder` 的完整 Python 实现，请直接告诉我！ 