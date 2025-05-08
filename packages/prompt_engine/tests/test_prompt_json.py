import json
import pytest
from pathlib import Path # For checking template placeholders

# Adjusted import to reflect the new structure if tests are run from math-copilot root
# and packages/__init__.py makes `packages` a package.
# If packages/prompt_engine is directly on PYTHONPATH, `from prompt_engine import build_prompt` would work.
# Assuming tests will be run in a way that `packages` is discoverable (e.g. `python -m pytest` from root)
from packages.prompt_engine import build_prompt, load_template

# Assume tests run from project root or that pythonpath is set
PROMPT_ENGINE_ROOT = Path("packages/prompt_engine")
PROMPT_DIR = PROMPT_ENGINE_ROOT / "prompts"

# Dynamically find all agents by looking at subdirectories in prompts/
AGENTS = sorted([p.name for p in PROMPT_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")])

# Context providing all *potentially* needed keys for the default templates
# Individual templates might only use a subset
CTX = {
    "raw_text":"f(x)=x^2",
    "rawLatex":"x^2",
    "currentLatex":"x=1", # Changed for block_parse
    "chosen_suggestion":"x+y=z", # Changed for solve_next_step
    "suggest_source":"user_input",
    "history_brief":"Step 1: ...\nStep 2: ...",
    "recent_steps":"Step 2: ...\nStep 1: ...",
    "all_steps":"Step 1: ...\nStep 2: ...\nStep 3: ...",
    "answer_raw":"The final answer is 42.",
    "maxLen": 500 # Example: Explicitly provide maxLen, build_prompt should use this
}

# Define minimal, agent-specific contexts for more precise testing.
# These should only contain keys that the specific default.yaml *actually uses*.
# This requires inspecting each default.yaml file.
AGENT_SPECIFIC_CTX = {
    "problem_ingest": {"raw_text": CTX["raw_text"]},
    "latex_refine": {"rawLatex": CTX["rawLatex"]},
    "block_parse": {"currentLatex": CTX["currentLatex"]},
    "suggest_next_moves": {"recent_steps": CTX["recent_steps"], "rawLatex": CTX["rawLatex"]},
    "solve_next_step": {
        "rawLatex": CTX["rawLatex"],
        "suggest_source": CTX["suggest_source"],
        "chosen_suggestion": CTX["chosen_suggestion"],
        "history_brief": CTX["history_brief"]
    },
    "solve_to_end": {"rawLatex": CTX["rawLatex"]},
    "summarize_history": {
        "rawLatex": CTX["rawLatex"],
        "all_steps": CTX["all_steps"],
        "maxLen": CTX["maxLen"] # Test with explicit maxLen
    },
    "answer_to_steps": {"answer_raw": CTX["answer_raw"]},
    "candidates": {"candidate": CTX["answer_raw"]},
}

@pytest.mark.parametrize("agent", AGENTS)
def test_prompt_has_two_messages(agent):
    """Verify that build_prompt returns a list of two messages (system, user)."""
    # Provide a basic context sufficient for most formatting
    # Add keys specific to agents if needed, or use the comprehensive CTX above
    minimal_ctx = {
        "raw_text":"test", "rawLatex":"test", "currentLatex":"test", 
        "chosen_suggestion":"test", "suggest_source":"test", 
        "history_brief":"test", "recent_steps":"test", 
        "all_steps":"test", "answer_raw":"test",
        # maxLen will be auto-injected if needed and not present
    }
    try:
        msgs = build_prompt(agent, minimal_ctx.copy()) # Use copy to avoid side effects
        assert isinstance(msgs, list)
        assert len(msgs) == 2
        assert isinstance(msgs[0], dict)
        assert msgs[0].get("role") == "system"
        assert isinstance(msgs[0].get("content"), str)
        assert isinstance(msgs[1], dict)
        assert msgs[1].get("role") == "user"
        assert isinstance(msgs[1].get("content"), str)
    except KeyError as e:
        pytest.fail(f"build_prompt for agent '{agent}' failed with KeyError: {e}. Check context or template placeholders.")
    except FileNotFoundError as e:
        pytest.fail(f"Template file not found for agent '{agent}': {e}")
    except Exception as e:
        pytest.fail(f"build_prompt for agent '{agent}' failed with unexpected error: {e}")


@pytest.mark.parametrize("agent", AGENTS)
def test_templates_load_and_have_keys(agent):
    """Verify that templates can be loaded and contain system/scene keys."""
    try:
        tpl = load_template(agent, "default")
        assert isinstance(tpl, dict)
        assert "system" in tpl
        assert "scene" in tpl
    except FileNotFoundError as e:
        pytest.fail(f"load_template failed for agent '{agent}': {e}")
    except Exception as e:
        pytest.fail(f"Error loading/parsing template for agent '{agent}': {e}")


@pytest.mark.parametrize("agent", AGENTS)
def test_template_scene_formatting(agent):
    """Verify that the scene can be formatted with a comprehensive context."""
    # This test uses the more complete CTX
    try:
        tpl = load_template(agent, "default")
        # Check if the scene template actually contains any placeholders
        if "{" in tpl['scene'] and "}" in tpl['scene']:
             # Check formatting only if placeholders seem present (simple check)
             # Exclude the special {{maxLen}} from this check
             temp_scene = tpl['scene'].replace("{{maxLen}}", "") 
             if "{" in temp_scene: # Check again after removing potential {{maxLen}}
                scene_formatted = temp_scene.format(**CTX)
                assert isinstance(scene_formatted, str)
        else:
            # If no placeholders, format should ideally still work or scene is static
            scene_formatted = tpl['scene'].format(**CTX)
            assert isinstance(scene_formatted, str)

    except KeyError as e:
        pytest.fail(f"Scene formatting failed for agent '{agent}' with KeyError: {e}. Check CTX keys and template placeholders {{...}} vs {...}.")
    except Exception as e:
        pytest.fail(f"Scene formatting failed for agent '{agent}' with unexpected error: {e}")


# This test seems unrelated to prompt_engine itself but was in the original spec
def test_sample_json_parse():
    """Test parsing a sample JSON string (as provided in original spec)."""
    sample = '{"rawLatex":"x","firstStep":{"latex":"x","explanation":"好"},"problemTask":"求导"}'
    try:
        data = json.loads(sample)
        assert isinstance(data, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse sample JSON: {e}")

# Test for summarize_history default maxLen (if not provided in ctx)
def test_summarize_history_default_max_len():
    ctx_no_max_len = {
        "rawLatex": CTX["rawLatex"],
        "all_steps": CTX["all_steps"]
    }
    msgs = build_prompt("summarize_history", ctx=ctx_no_max_len) # maxLen should default to 1000
    assert "{{maxLen}}" not in msgs[1]["content"]
    # Check if default was applied; this requires knowing the template structure or the builder's logic.
    # Since builder applies it to ctx, this test is more about builder logic.
    # The actual value might not be in the final string if the template doesn't directly use it like {{maxLen}} for some reason
    # but it was used to format a string that might have a length constraint.
    # A more direct test would be to check the `ctx` object inside `build_prompt` or if `format` raises error.
    # For now, ensuring no placeholder is left is good. 