---
name: mantis-security-audit
description: >-
  Autonomous security auditing, threat modeling, vulnerability discovery, invariant verification, and patch synthesis toolkit based on Google Mantis.
---

# Mantis Security Audit Suite

**Upstream:** `https://github.com/google/mantis.git` (Commit: `db071ca1375d3112c3240a6b9a8cf633a69a2a91`)

## Overview

Mantis provides an autonomous security verification architecture designed to identify, reproduce, and synthesize verifiable fixes for security vulnerabilities in codebases.

## Core Capabilities

1. **Threat Model Extraction & Schema Grounding**:
   - Identifies untrusted entry points, data flows, trust boundaries, and authorization contexts.
2. **Structural Indexing & Symbol Graphing**:
   - Analyzes AST and call graphs to map tainted paths from sources to sinks.
3. **Reproducer & Invariant Validation**:
   - Constructs isolated reproductions of suspected bugs to eliminate false positives.
4. **Patch Synthesis & Regression Proofs**:
   - Generates minimal surgical patches and verifies that the threat invariant is resolved without breaking functionality.

## Usage

### 1. Configuration & Preflight
Run preflight verification before any audit campaign:
```bash
python .agents/tools/mantis/configure.py --preflight --show
```

### 2. Launching Codebase Security Scan
```bash
python .agents/tools/mantis/launch.py . --preflight-only
```

### 3. MCP Server Integration
Mantis can also run as an MCP server providing structural analysis tools:
```bash
python .agents/tools/mantis/mcp_server.py
```
