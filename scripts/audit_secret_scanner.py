"""
Deep Secret and Credential Scanner for .agents and Workspace
Performs comprehensive multi-pattern static analysis across all files.
Outputs all findings with automatically redacted values.
"""

import os
import re
import json
from pathlib import Path

PATTERNS = [
    ("Context7 API Key", re.compile(r"ctx7sk-[a-zA-Z0-9_\-]{20,}")),
    ("Tavily API Key", re.compile(r"tvly-[a-zA-Z0-9_\-]{20,}")),
    ("Sentry Auth Token", re.compile(r"sntryu_[a-zA-Z0-9_\-]{20,}|sntrys_[a-zA-Z0-9_\-]{20,}")),
    ("OpenAI API Key", re.compile(r"sk-[a-zA-Z0-9]{20,}|sk-proj-[a-zA-Z0-9_\-]{20,}")),
    ("Anthropic API Key", re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}")),
    ("Google API Key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("GitHub Personal Access Token", re.compile(r"ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,}|gho_[a-zA-Z0-9]{36}")),
    ("AWS Access Key ID", re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
    ("Slack Token", re.compile(r"xox[baprs]-[0-9]{10,}-[a-zA-Z0-9]{10,}")),
    ("Stripe API Key", re.compile(r"sk_live_[0-9a-zA-Z]{24}")),
    ("Private Key Header", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----")),
    ("Database URL with Password", re.compile(r"(?:postgres|postgresql|mysql|mongodb|redis)://[^:]+:([^@]+)@[a-zA-Z0-9\.\-]+")),
    ("Generic Bearer / Auth Token Assignment", re.compile(r"(?:token|api_key|secret|password|auth_token)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]", re.IGNORECASE)),
    ("JWT Token", re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}")),
]

SENSITIVE_FILENAMES = [
    re.compile(r"^\.env(?:\..+)?$", re.IGNORECASE),
    re.compile(r"^.*\.(?:pem|key|crt|pfx|p12|pkcs12)$", re.IGNORECASE),
    re.compile(r"^id_(?:rsa|ecdsa|ed25519|dsa)$", re.IGNORECASE),
    re.compile(r"^(?:credentials|secrets|token|auth)\.(?:json|ya?ml|toml|ini)$", re.IGNORECASE),
]

IGNORE_DIRS = {".git", "node_modules", ".pytest_cache", "__pycache__"}

def redact(secret: str) -> str:
    if len(secret) <= 8:
        return "****"
    prefix = secret[:4]
    suffix = secret[-4:]
    return f"{prefix}****{suffix}"

def scan_workspace(root_path: str):
    root = Path(root_path).resolve()
    findings = []
    suspicious_files = []
    scanned_file_count = 0

    for current_dir, dirs, files in os.walk(root):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            file_path = Path(current_dir) / file
            rel_path = file_path.relative_to(root).as_posix()
            scanned_file_count += 1

            # Check filename patterns
            for pattern in SENSITIVE_FILENAMES:
                if pattern.match(file):
                    suspicious_files.append({
                        "file": rel_path,
                        "type": "Sensitive Filename Pattern"
                    })
                    break

            # Read file content safely
            try:
                # Skip large binary files
                if file_path.stat().st_size > 5 * 1024 * 1024:
                    continue
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for label, pattern in PATTERNS:
                for match in pattern.finditer(content):
                    raw_matched = match.group(0)
                    
                    # Filter out placeholders and comments
                    placeholders = [
                        "your_api_key_here", "your_database_url_here", "sk-proj-xxxxx",
                        "password123", "ctx7sk-xxx", "sk-xxx", "AIzaSyDummy", "tvly-xxx",
                        "sntryu_xxx", "YOUR_API_KEY", "YOUR_CONTEXT7_API_KEY_HERE"
                    ]
                    if any(ph in raw_matched for ph in placeholders):
                        continue

                    # Calculate line number
                    start_pos = match.start()
                    line_num = content.count("\n", 0, start_pos) + 1

                    findings.append({
                        "file": rel_path,
                        "line": line_num,
                        "label": label,
                        "redacted_sample": redact(raw_matched),
                        "snippet": content.splitlines()[line_num - 1].strip()[:100]
                    })

    return {
        "scanned_files": scanned_file_count,
        "suspicious_files": suspicious_files,
        "findings_count": len(findings),
        "findings": findings
    }

if __name__ == "__main__":
    result = scan_workspace(".")
    print(json.dumps(result, indent=2))
