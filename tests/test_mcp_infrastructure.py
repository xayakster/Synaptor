import os
import json
import subprocess
import sys
import pytest

AGENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents"))
GLOBAL_MCP_CONFIG = os.path.expanduser("~/.gemini/config/mcp_config.json")

def test_global_mcp_config_preserves_existing_and_adds_context7():
    # If global config exists (local workstation), verify all 8 servers are present
    if os.path.exists(GLOBAL_MCP_CONFIG):
        with open(GLOBAL_MCP_CONFIG, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        servers = data.get("mcpServers", {})
        assert "context7" in servers, "context7 missing from global mcpServers"
        
        # Verify all 7 pre-existing MCP servers remain intact
        existing = ["sqlite", "tavily-search", "sentry", "code-sandbox", "youtube-transcript", "evm-rpc", "sqlite-arbitrage-bot"]
        for s in existing:
            assert s in servers, f"Existing MCP server '{s}' was accidentally removed!"
    else:
        # On clean CI runner, verify portable mcp_config.json
        portable_cfg = os.path.join(AGENTS_DIR, "config", "mcp_config.json")
        assert os.path.exists(portable_cfg)
        with open(portable_cfg, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "context7" in data.get("mcpServers", {})

def test_portable_mcp_configs_and_registry():
    portable_cfg = os.path.join(AGENTS_DIR, "config", "mcp_config.json")
    assert os.path.exists(portable_cfg), "Portable .agents/config/mcp_config.json missing"
    with open(portable_cfg, "r", encoding="utf-8") as f:
        pdata = json.load(f)
    assert "context7" in pdata.get("mcpServers", {})
    
    registry = os.path.join(AGENTS_DIR, "config", "mcp_registry.json")
    assert os.path.exists(registry), "Central MCP registry missing"
    with open(registry, "r", encoding="utf-8") as f:
        rdata = json.load(f)
    server_names = [s["name"] for s in rdata.get("servers", [])]
    assert "context7" in server_names

def test_mcp_skills_and_routing_rules():
    assert os.path.exists(os.path.join(AGENTS_DIR, "skills", "documentation-lookup", "SKILL.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "documentation-lookup.md"))
    assert os.path.exists(os.path.join(AGENTS_DIR, "rules", "mcp-routing-rules.md"))

def test_mcp_health_check_execution():
    health_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "mcp-health-check.py"))
    assert os.path.exists(health_script), "mcp-health-check.py missing"
    res = subprocess.run([sys.executable, health_script], capture_output=True, text=True)
    assert res.returncode == 0, f"mcp-health-check.py failed: {res.stderr}\n{res.stdout}"
    assert "Overall Status: HEALTHY" in res.stdout
