#!/usr/bin/env python3
"""PreToolUse hook: only the qa agent may write under tests/.

Blocks Write/Edit on tests/ in the project and in sibling Dev worktrees
(../wt-*/tests/) unless the call comes from the qa agent. Exit 2 blocks the call.
"""
import json
import os
import sys

data = json.load(sys.stdin)
file_path = (data.get("tool_input") or {}).get("file_path")
if not file_path:
    sys.exit(0)

cwd = data.get("cwd") or os.getcwd()
project = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or cwd)
target = os.path.realpath(os.path.join(cwd, file_path))

roots = [project]
parent = os.path.dirname(project)
rel_parent = os.path.relpath(target, parent).split(os.sep)
if rel_parent[0].startswith("wt-"):
    roots.append(os.path.join(parent, rel_parent[0]))

in_tests = any(
    os.path.relpath(target, root).split(os.sep)[0] == "tests" for root in roots
)
if in_tests and data.get("agent_type") != "qa":
    who = data.get("agent_type") or "the main session"
    print(
        f"Blocked: tests/ is owned by QA and {who} may not edit {file_path}. "
        "Delegate the change to the qa agent, or report the problem in your handoff.",
        file=sys.stderr,
    )
    sys.exit(2)
