# Mantis Security Review & Isolation Standards

**Source:** `https://github.com/google/mantis.git` (Commit: `db071ca1375d3112c3240a6b9a8cf633a69a2a91`)

## Security Audit Principles

1. **Isolation & Safety First**:
   - Never execute untrusted or autonomously generated reproducers on production machines or networks with sensitive credential access.
   - Use sandboxed execution (`static-only`, containerized, or virtualized) when verifying potential exploits.

2. **Responsible Disclosure & Verification**:
   - AI models can hallucinate vulnerability findings or generate incorrect exploit claims.
   - Every vulnerability report MUST contain a verifiable threat model, invariant violation proof, and trace from source to sink.
   - Never mass-file unverified AI-generated security reports.

3. **Verifiable Patch Invariants**:
   - Security patches must address the root cause at the trust boundary (e.g. input validation, parameterized queries, canonical path checking, safe type coercion).
   - Patches must include a regression test ensuring both the exploit vector is closed and legitimate functionality continues to operate.
