from pathlib import Path
import yaml
import json # For the __main__ test block

PROMPT_DIR = Path(__file__).parent / "prompts"

def load_template(agent: str, variant: str = "default") -> dict:
    fp = PROMPT_DIR / agent / f"{variant}.yaml"
    # Robust check: if variant is not default and not found, try default
    if not fp.exists() and variant != "default":
        default_fp = PROMPT_DIR / agent / "default.yaml"
        if default_fp.exists():
            # print(f"Warning: Prompt template for agent '{agent}', variant '{variant}' not found at {fp}. Falling back to 'default.yaml'.")
            fp = default_fp
        else:
            raise FileNotFoundError(f"Prompt template not found for agent '{agent}': neither variant '{variant}' ({fp.name}) nor default.yaml ({default_fp.name}) exists in {PROMPT_DIR / agent}")
    elif not fp.exists() and variant == "default":
        raise FileNotFoundError(f"Default prompt template not found for agent '{agent}': {fp} does not exist.")
    
    try:
        return yaml.safe_load(fp.read_text(encoding='utf-8'))
    except Exception as e:
        # Catching generic Exception but providing specific context
        raise ValueError(f"Error loading or parsing YAML template {fp}: {e}")

def build_prompt(agent: str, ctx: dict, variant: str = "default") -> list:
    """
    参数:
      agent   —— 例如 'block_parse'
      ctx     —— 占位符字典，如 {'rawLatex': 'x^2'}
      variant —— 默认 'default'，未来可放几何 / rag 之类扩展
    返回:
      List[dict]  可直接送入 openai.ChatCompletion
    """
    tpl = load_template(agent, variant) # load_template now handles FileNotFoundError robustly

    if not isinstance(tpl, dict):
        raise ValueError(f"Loaded template for agent '{agent}', variant '{variant}' is not a dictionary. Content: {tpl}")

    if "system" not in tpl or "scene" not in tpl:
        raise ValueError(f"Template for agent '{agent}', variant '{variant}' is missing 'system' or 'scene' key. Keys found: {list(tpl.keys())}")

    # Default for {{maxLen}} if used in scene and not provided in ctx
    if "{{maxLen}}" in tpl["scene"] and "maxLen" not in ctx:
        ctx["maxLen"] = 1000                # 摘要默认 1000 字
    
    try:
        scene = tpl["scene"].format(**ctx)
    except KeyError as e:
        # Provide more context on the missing key and available keys in ctx
        raise KeyError(f"Missing placeholder {e} in context for agent '{agent}', variant '{variant}'. Scene expects it. Provided context keys: {list(ctx.keys())}. Template scene: {tpl['scene'][:200]}...")
    except Exception as e:
        raise ValueError(f"Error formatting scene for agent '{agent}', variant '{variant}' with context {list(ctx.keys())}: {e}")

    return [
        {"role": "system", "content": tpl["system"]},
        {"role": "user",   "content": scene},
    ]

# --- CLI quick test ---------------------------------------------------------
if __name__ == "__main__":
    # Ensure prompts/problem_ingest/default.yaml exists for this test
    try:
        test_ctx = {"raw_text": "已知函数 f(x)=x^2"}
        msgs = build_prompt("problem_ingest", test_ctx)
        print(json.dumps(msgs, ensure_ascii=False, indent=2))
    except FileNotFoundError as e:
        print(f"CLI Test Error: Could not find a template for 'problem_ingest'. Make sure 'prompts/problem_ingest/default.yaml' exists. Details: {e}")
    except Exception as e:
        print(f"CLI Test Error: {e}") 