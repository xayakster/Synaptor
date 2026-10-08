# Security Policy

The **Synaptor** team takes the security of our platform, agent ecosystem, and community seriously.

---

## 🔒 Supported Versions

Security updates and vulnerability patches are actively maintained for the following versions:

| Version | Supported |
| :--- | :--- |
| `3.2.x` | ✅ Supported |
| `3.1.x` | ✅ Supported |
| `< 3.1` | ❌ End of Life |

---

## 🛡️ Security Architecture & Principles

1. **Zero Secret Storage**:
   - The repository strictly prohibits committing plaintext API keys, passwords, private keys, or credentials.
   - All sensitive credentials must be loaded via local environment variables (`.env`) which are strictly excluded by `.gitignore`.
2. **Local Transport Isolation**:
   - Model Context Protocol (MCP) integrations communicate over local standard I/O (stdio) subprocesses. No unsolicited network listener ports are opened by default.
3. **Mantis Threat Modeling & Invariant Verification**:
   - Security auditing tooling operates in `static-only` sandbox mode by default to ensure safe analysis of untrusted inputs.
4. **Automated Continuous Secret Scanning**:
   - The built-in scanner `scripts/security-audit-scan.py` enforces automated static analysis to detect accidental token exposure and dangerous code constructs (`eval`, `exec`, unescaped `shell=True`).

---

## 🚨 Reporting a Vulnerability

If you discover a potential security vulnerability or secret exposure:

1. **Do NOT file a public issue** on GitHub.
2. Please report the vulnerability privately by opening a [GitHub Security Advisory](https://github.com/xayakster/Synaptor/security/advisories) or contacting the maintainers directly.
3. Include detailed steps to reproduce the issue, affected components, and potential impact.
4. Maintainers will acknowledge receipt within 48 hours and provide an estimated resolution timeline.

---

## 🔑 Credential Rotation Guidelines

If you accidentally expose a live API key or credential during local development:
1. Immediately **revoke and rotate** the key in your provider's dashboard (e.g. OpenAI, Anthropic, Context7, Tavily, Sentry).
2. Remove the secret from your local workspace files.
3. Update your `.gitignore` to ensure the file pattern is properly protected.
