from pathlib import Path
import yaml
from typing import List, Dict, Any
import json # For the __main__ test block

PROMPT_DIR = Path(__file__).parent / "prompts"

def load_template(agent: str, variant: str = "default") -> Dict[str, str]:
    fp = PROMPT_DIR / agent / f"{variant}.yaml"
    if not fp.exists():
        raise FileNotFoundError(f"Prompt template not found at: {fp}")
    try:
        return yaml.safe_load(fp.read_text(encoding="utf-8"))
    except Exception as e:
        raise IOError(f"Error loading or parsing YAML template: {fp}\n{e}") from e

def build_prompt(agent: str, ctx: Dict[str, Any], variant: str = "default") -> List[Dict[str, str]]:
    """
    参数:
      agent   —— 例如 'block_parse'
      ctx     —— 占位符字典，如 {'rawLatex': 'x^2'}
      variant —— 默认 'default'，未来可放几何 / rag 之类扩展
    返回:
      List[dict]  可直接送入 openai.ChatCompletion
    """
    tpl = load_template(agent, variant)

    # Ensure required keys exist in template
    if "system" not in tpl or "scene" not in tpl:
        raise ValueError(f"Template for agent '{agent}' variant '{variant}' is missing 'system' or 'scene' key.")

    # ① Check for optional {{maxLen}} injection (before formatting)
    # Use double braces {{maxLen}} specifically for this check as per user doc
    max_len_placeholder = "{{maxLen}}" 
    if max_len_placeholder in tpl.get("scene", "") and "maxLen" not in ctx:
        ctx["maxLen"] = 1000 # Default value
        # We need to remove the placeholder from the template string 
        # if it won't be replaced by format(), otherwise format() might complain 
        # depending on the Python version and exact string content.
        # However, removing it might alter intended structure if not careful.
        # A safer approach if {{maxLen}} is ONLY for this check:
        # tpl["scene"] = tpl["scene"].replace(max_len_placeholder, str(ctx["maxLen"]))
        # Let's assume for now that if {{maxLen}} is present, it WILL be in ctx after this.
        # If not, format() will handle it (or raise error if it looks like {maxLen}).

    # ② Format the scene using single-braced placeholders {placeholder}
    try:
        scene = tpl["scene"].format(**ctx)
    except KeyError as e:
        missing_key = e.args[0]
        raise KeyError(f"Context ('ctx') is missing required placeholder key '{missing_key}' for agent '{agent}'.") from None
    except Exception as e:
        # Catch other potential formatting errors
        raise ValueError(f"Error formatting scene for agent '{agent}' with provided context: {e}") from e

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