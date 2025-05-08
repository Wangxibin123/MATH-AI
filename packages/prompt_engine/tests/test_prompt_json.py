import json
import pytest
from pathlib import Path # For checking template placeholders

# Adjusted import to reflect the new structure if tests are run from math-copilot root
# and packages/__init__.py makes `packages` a package.
# If packages/prompt_engine is directly on PYTHONPATH, `from prompt_engine import build_prompt` would work.
# Assuming tests will be run in a way that `packages` is discoverable (e.g. `python -m pytest` from root)
from packages.prompt_engine import build_prompt 

AGENTS = [
    "problem_ingest", "latex_refine", "block_parse",
    "suggest_next_moves", "solve_next_step", "solve_to_end",
    "summarize_history", "answer_to_steps", "candidates"
]

# Define the base directory for prompts, relative to this test file or a known anchor.
# Assuming this test file is in packages/prompt_engine/tests/
# and prompts are in packages/prompt_engine/prompts/
PROMPTS_ROOT_DIR = Path(__file__).parent.parent / "prompts"

# Master context dictionary that includes all possible keys any default template might use.
# This ensures that if a template uses a key, it's available.
MASTER_CTX = {
    "raw_text": "设函数 f(x)=x^2, g(x) = sin(x).求 f(g(x)) 在 x=0 处的导数。",
    "rawLatex": "\\int x^2 dx",
    "currentLatex": "\\frac{d}{dx} (x^2) = 2x",
    "recent_steps": "[{'latex': 'x^2+1=y'}, {'latex': 'y-1=x^2'}]", # Represent as string if YAML expects string
    "chosen_suggestion": "\\text{Let } u = x^2",
    "suggest_source": "user_input_or_RAG",
    "history_brief": "- Step 1: Initial setup done.\n- Step 2: Applied L'Hopital\'s rule.",
    "all_steps": "[{'latex': 'Step 1 ...', 'explanation': '...'}, {'latex': 'Step 2 ...', 'explanation': '...'}]",
    "answer_raw": "The final solution is x=5 after several algebraic manipulations.",
    "candidate": "\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1",
    "maxLen": 150 # Explicitly provide for summarize_history, though builder has a default
}

# Define minimal, agent-specific contexts for more precise testing.
# These should only contain keys that the specific default.yaml *actually uses*.
# This requires inspecting each default.yaml file.
AGENT_SPECIFIC_CTX = {
    "problem_ingest": {"raw_text": MASTER_CTX["raw_text"]},
    "latex_refine": {"rawLatex": MASTER_CTX["rawLatex"]},
    "block_parse": {"currentLatex": MASTER_CTX["currentLatex"]},
    "suggest_next_moves": {"recent_steps": MASTER_CTX["recent_steps"], "rawLatex": MASTER_CTX["rawLatex"]},
    "solve_next_step": {
        "rawLatex": MASTER_CTX["rawLatex"],
        "suggest_source": MASTER_CTX["suggest_source"],
        "chosen_suggestion": MASTER_CTX["chosen_suggestion"],
        "history_brief": MASTER_CTX["history_brief"]
    },
    "solve_to_end": {"rawLatex": MASTER_CTX["rawLatex"]},
    "summarize_history": {
        "rawLatex": MASTER_CTX["rawLatex"],
        "all_steps": MASTER_CTX["all_steps"],
        "maxLen": MASTER_CTX["maxLen"] # Test with explicit maxLen
    },
    "answer_to_steps": {"answer_raw": MASTER_CTX["answer_raw"]},
    "candidates": {"candidate": MASTER_CTX["candidate"]},
}

@pytest.mark.parametrize("agent", AGENTS)
def test_build_prompt_structure_and_placeholders(agent):
    specific_ctx = AGENT_SPECIFIC_CTX[agent].copy()

    # Load the actual template to check its placeholders (optional, for advanced validation)
    # template_path = PROMPTS_ROOT_DIR / agent / "default.yaml"
    # if not template_path.exists():
    #     pytest.fail(f"Template file not found for agent {agent}: {template_path}")
    # template_content = template_path.read_text(encoding='utf-8')

    msgs = build_prompt(agent, ctx=specific_ctx, variant="default")
    
    assert isinstance(msgs, list), f"build_prompt for {agent} should return a list"
    assert len(msgs) == 2, f"build_prompt for {agent} should return two messages (system, user)"
    
    system_msg = msgs[0]
    user_msg = msgs[1]

    assert system_msg.get("role") == "system", f"System message role missing or incorrect for {agent}"
    assert isinstance(system_msg.get("content"), str), f"System message content missing or not a string for {agent}"
    assert len(system_msg["content"].strip()) > 0, f"System message content for {agent} should not be empty"

    assert user_msg.get("role") == "user", f"User message role missing or incorrect for {agent}"
    assert isinstance(user_msg.get("content"), str), f"User message content missing or not a string for {agent}"
    assert len(user_msg["content"].strip()) > 0, f"User message content for {agent} should not be empty (after formatting)"
    
    # Check that all placeholders in the specific_ctx were used and no {{...}} are left
    # This implies that the scene template correctly used all provided ctx keys.
    if "{{" in user_msg["content"] or "}}" in user_msg["content"]:
        # Try to find which placeholder might be unresolved
        import re
        unresolved = re.findall(r"{{(.*?)}}", user_msg["content"])
        if unresolved:
            pytest.fail(f"Unresolved placeholders {unresolved} in user content for agent '{agent}'. User content: {user_msg['content'][:500]}...")

    # print(f"\nSuccessfully built prompt for agent: {agent}")
    # print(json.dumps(msgs, ensure_ascii=False, indent=2)) # For manual inspection

# Test for the CLI example in prompt_builder.py
def test_cli_example_problem_ingest():
    test_ctx = {"raw_text": "CLI test: f(x)=x^3"}
    msgs = build_prompt("problem_ingest", test_ctx)
    assert msgs[0]["role"] == "system"
    assert "CLI test: f(x)=x^3" in msgs[1]["content"]

# Test for summarize_history default maxLen (if not provided in ctx)
def test_summarize_history_default_max_len():
    ctx_no_max_len = {
        "rawLatex": MASTER_CTX["rawLatex"],
        "all_steps": MASTER_CTX["all_steps"]
    }
    msgs = build_prompt("summarize_history", ctx=ctx_no_max_len) # maxLen should default to 1000
    assert "{{maxLen}}" not in msgs[1]["content"]
    # Check if default was applied; this requires knowing the template structure or the builder's logic.
    # Since builder applies it to ctx, this test is more about builder logic.
    # The actual value might not be in the final string if the template doesn't directly use it like {{maxLen}} for some reason
    # but it was used to format a string that might have a length constraint.
    # A more direct test would be to check the `ctx` object inside `build_prompt` or if `format` raises error.
    # For now, ensuring no placeholder is left is good. 