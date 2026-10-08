#!/usr/bin/env python3
"""
Universal Lifecycle Hook Handler for .agents
Handles SessionStart, UserPromptSubmit, PreCompact, and PreToolUse
Compatible with Claude Code, Cursor, Copilot CLI, Gemini, and Antigravity.
"""

import sys
import os
import json

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def get_plugin_root():
    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return os.environ["CLAUDE_PLUGIN_ROOT"]
    if os.environ.get("CURSOR_PLUGIN_ROOT"):
        return os.environ["CURSOR_PLUGIN_ROOT"]
    # Fallback to current script directory parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def format_output(context_text: str, event_name: str = "SessionStart"):
    if os.environ.get("CURSOR_PLUGIN_ROOT"):
        return json.dumps({"additional_context": context_text}, indent=2)
    elif os.environ.get("CLAUDE_PLUGIN_ROOT") and not os.environ.get("COPILOT_CLI"):
        return json.dumps({
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": context_text
            }
        }, indent=2)
    else:
        return json.dumps({"additionalContext": context_text}, indent=2)

def handle_session_start(plugin_root: str):
    contexts = []
    
    # 1. Superpowers skill if present
    sp_path = os.path.join(plugin_root, "skills", "using-superpowers", "SKILL.md")
    if os.path.exists(sp_path):
        try:
            with open(sp_path, "r", encoding="utf-8", errors="ignore") as f:
                sp_content = f.read()
            contexts.append(f"<EXTREMELY_IMPORTANT>\nYou have superpowers.\n\n**Below is the full content of your 'superpowers:using-superpowers' skill:**\n\n{sp_content}\n</EXTREMELY_IMPORTANT>")
        except Exception:
            pass
            
    # 2. Planning with files if active plan exists in workspace
    for plan_candidate in ["task_plan.md", os.path.join(".agents", "plans", "task_plan.md")]:
        if os.path.exists(plan_candidate):
            try:
                with open(plan_candidate, "r", encoding="utf-8", errors="ignore") as f:
                    plan_content = f.read()
                contexts.append(f"<PLANNING_WITH_FILES_ACTIVE_PLAN>\nActive Task Plan detected on disk ({plan_candidate}):\n\n{plan_content}\n</PLANNING_WITH_FILES_ACTIVE_PLAN>")
                break
            except Exception:
                pass
                
    if contexts:
        full_text = "\n\n".join(contexts)
        print(format_output(full_text, "SessionStart"))
    else:
        print("{}")

def handle_user_prompt_submit():
    # If task_plan.md exists, inject concise active state
    for plan_candidate in ["task_plan.md", os.path.join(".agents", "plans", "task_plan.md")]:
        if os.path.exists(plan_candidate):
            try:
                with open(plan_candidate, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                # Extract first 50 lines / active checklist
                summary = "".join(lines[:60])
                text = f"<ACTIVE_PLAN_CONTEXT>\n{summary}\n</ACTIVE_PLAN_CONTEXT>"
                print(format_output(text, "UserPromptSubmit"))
                return
            except Exception:
                pass
    print("{}")

def main():
    event = sys.argv[1] if len(sys.argv) > 1 else "session-start"
    plugin_root = get_plugin_root()
    
    if event in ["session-start", "SessionStart"]:
        handle_session_start(plugin_root)
    elif event in ["user-prompt-submit", "UserPromptSubmit"]:
        handle_user_prompt_submit()
    elif event in ["pre-compact", "PreCompact"]:
        # Verify plan is synced
        print("{}")
    else:
        print("{}")

if __name__ == "__main__":
    main()
