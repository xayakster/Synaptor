#!/usr/bin/env python3
"""
RTK Cross-Platform Command Filter & Proxy
Source: https://github.com/rtk-ai/rtk.git

Provides instant output token filtering for AI agent command execution.
If native `rtk` binary is found on PATH, delegates directly.
Otherwise, provides built-in token compression for common CLI tools.
"""

import sys
import os
import shutil
import subprocess
import re

def filter_git_status(output: str) -> str:
    lines = output.splitlines()
    filtered = []
    for line in lines:
        if line.startswith("On branch ") or line.startswith("Your branch is ") or "nothing to commit" in line:
            filtered.append(line)
        elif line.strip().startswith("modified:") or line.strip().startswith("new file:") or line.strip().startswith("deleted:"):
            filtered.append("  " + line.strip())
        elif line.strip() and not line.startswith("  (") and not line.startswith("Untracked files:"):
            filtered.append(line)
    return "\n".join(filtered) if filtered else output

def filter_pytest(output: str) -> str:
    lines = output.splitlines()
    filtered = []
    in_failure_block = False
    for line in lines:
        if "=== FAILURES ===" in line or "=== ERRORS ===" in line:
            in_failure_block = True
        if "=== short test summary info ===" in line:
            in_failure_block = False
        if in_failure_block or any(k in line for k in ["FAILED", "ERROR", "passed", "failed", "warnings", "=== "]):
            filtered.append(line)
    return "\n".join(filtered) if len(filtered) < len(lines) and len(filtered) > 0 else output

def general_filter(output: str, max_lines: int = 150) -> str:
    lines = output.splitlines()
    if len(lines) <= max_lines:
        return output
    head = lines[:int(max_lines * 0.6)]
    tail = lines[-int(max_lines * 0.4):]
    omitted = len(lines) - len(head) - len(tail)
    return "\n".join(head + [f"\n... [RTK: {omitted} lines omitted to save tokens. Use --raw to view full output] ...\n"] + tail)

def main():
    if len(sys.argv) < 2:
        print("Usage: rtk_filter.py [--raw] <command> [args...]")
        sys.exit(1)
    
    args = sys.argv[1:]
    raw_mode = False
    if args[0] == "--raw":
        raw_mode = True
        args = args[1:]
    
    if not args:
        print("Error: No command specified.")
        sys.exit(1)
        
    # Check if native rtk binary exists on PATH and not in raw mode
    native_rtk = shutil.which("rtk")
    if native_rtk and not raw_mode and args[0] != "rtk":
        try:
            res = subprocess.run([native_rtk] + args)
            sys.exit(res.returncode)
        except Exception:
            pass  # Fallback to python runner
            
    # Run the command directly
    try:
        proc = subprocess.run(args, capture_output=True, text=True, shell=(os.name == 'nt'))
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        returncode = proc.returncode
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        sys.exit(1)
        
    if raw_mode:
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, file=sys.stderr, end="")
        sys.exit(returncode)
        
    # Apply filters based on command
    cmd_name = os.path.basename(args[0]).lower()
    full_cmd = " ".join(args).lower()
    
    if "git" in cmd_name and "status" in full_cmd:
        filtered_stdout = filter_git_status(stdout)
    elif "pytest" in full_cmd:
        filtered_stdout = filter_pytest(stdout)
    else:
        filtered_stdout = general_filter(stdout)
        
    if filtered_stdout:
        print(filtered_stdout)
    if stderr:
        print(stderr, file=sys.stderr)
        
    sys.exit(returncode)

if __name__ == "__main__":
    main()
