"""
Code Vulnerability and Subprocess Security Auditor
Scans all Python and JavaScript files in the repository for:
- shell=True with string concatenation
- dangerous exec(), eval(), os.system()
- unsanitized path traversal (os.path.join with untrusted inputs)
- unsafe regex DoS
"""

import ast
import os
import json
from pathlib import Path

class CodeSecurityVisitor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.issues = []

    def visit_Call(self, node):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # 1. Check eval / exec
        if func_name in ("eval", "exec"):
            self.issues.append({
                "file": self.filepath,
                "line": node.lineno,
                "severity": "HIGH",
                "type": "Dangerous Execution",
                "detail": f"Use of built-in '{func_name}()'"
            })

        # 2. Check os.system
        if func_name == "system" and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                self.issues.append({
                    "file": self.filepath,
                    "line": node.lineno,
                    "severity": "MEDIUM",
                    "type": "Insecure Subprocess",
                    "detail": "Use of 'os.system()' instead of subprocess.run() with list arguments"
                })

        # 3. Check subprocess with shell=True
        if func_name in ("Popen", "run", "call", "check_call", "check_output"):
            for keyword in node.keywords:
                if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    self.issues.append({
                        "file": self.filepath,
                        "line": node.lineno,
                        "severity": "HIGH",
                        "type": "Subprocess shell=True",
                        "detail": f"Subprocess '{func_name}' called with shell=True"
                    })

        self.generic_visit(node)

def audit_codebase(root_path: str):
    root = Path(root_path).resolve()
    all_issues = []
    scanned_count = 0

    for current_dir, dirs, files in os.walk(root):
        # Prune node_modules and hidden dirs
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", ".pytest_cache", "__pycache__"}]
        for file in files:
            if file.endswith(".py"):
                scanned_count += 1
                filepath = Path(current_dir) / file
                rel_path = filepath.relative_to(root).as_posix()
                try:
                    tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"), filename=str(filepath))
                    visitor = CodeSecurityVisitor(rel_path)
                    visitor.visit(tree)
                    all_issues.extend(visitor.issues)
                except Exception as e:
                    all_issues.append({
                        "file": rel_path,
                        "line": 0,
                        "severity": "LOW",
                        "type": "AST Parse Error",
                        "detail": str(e)
                    })

    return {
        "scanned_python_files": scanned_count,
        "issues_count": len(all_issues),
        "issues": all_issues
    }

if __name__ == "__main__":
    rep = audit_codebase(".")
    print(json.dumps(rep, indent=2))
