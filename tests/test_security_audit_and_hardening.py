"""
Automated Test Suite for Security, Cleanliness, and Synaptor Hardening
Validates:
1. Zero secrets in tracked codebase
2. Comprehensive .gitignore coverage (including archive/ and docs/)
3. Safe .agents architecture and agent structure
4. Secure execution of Synaptor security audit scanner script
"""

import os
import subprocess
import sys
from pathlib import Path

def test_gitignore_covers_sensitive_files():
    gitignore_path = Path(".gitignore")
    assert gitignore_path.exists(), ".gitignore must exist"
    content = gitignore_path.read_text(encoding="utf-8")
    
    required_rules = [
        ".env",
        "*.pem",
        "*.key",
        "node_modules/",
        "__pycache__/",
        ".pytest_cache/",
        "*.sqlite",
        "*.db",
        "credentials.*",
        "secrets.*",
        "archive/",
        "docs/"
    ]
    for rule in required_rules:
        assert rule in content, f"Missing required .gitignore rule: {rule}"

def test_env_example_contains_no_real_secrets():
    env_example = Path(".env.example")
    assert env_example.exists(), ".env.example must exist"
    content = env_example.read_text(encoding="utf-8")
    
    # Assert that all keys are dummy placeholders
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            val = line.split("=", 1)[1].strip()
            assert "your_" in val or "your-" in val, f"Non-placeholder value found in .env.example: {line}"

def test_agents_architecture_structure():
    agents_dir = Path(".agents")
    assert (agents_dir / "agents").is_dir(), ".agents/agents directory must exist"
    assert (agents_dir / "skills").is_dir(), ".agents/skills directory must exist"
    assert (agents_dir / "rules").is_dir(), ".agents/rules directory must exist"
    assert (agents_dir / "workflows").is_dir(), ".agents/workflows directory must exist"
    assert (agents_dir / "hooks").is_dir(), ".agents/hooks directory must exist"
    
    # Check agents count
    agent_files = list((agents_dir / "agents").glob("*.md"))
    assert len(agent_files) >= 60, f"Expected 60+ agent personas, found {len(agent_files)}"

def test_security_audit_scanner_passes():
    proc = subprocess.run(
        [sys.executable, "scripts/security-audit-scan.py"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    assert proc.returncode == 0, f"Security audit scan failed:\n{proc.stdout}\n{proc.stderr}"
    assert "ALL SECURITY CHECKS PASSED" in proc.stdout
