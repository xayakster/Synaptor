# /mantis-scan Workflow

Run an end-to-end security campaign to analyze threat models, identify vulnerabilities, and generate verified patches.

**Source:** `https://github.com/google/mantis.git`

## Trigger
- User invokes `/mantis-scan`, `/mantis-launch`, or requests comprehensive security vulnerability auditing.

## Execution Steps

1. **Preflight Verification**:
   - Check environment configuration and tool dependencies:
     ```bash
     python .agents/tools/mantis/configure.py --preflight
     ```

2. **Structural Symbol Indexing & Taint Mapping**:
   - Map untrusted inputs (HTTP params, headers, CLI arguments, file descriptors) to sensitive sinks (database queries, system exec, file write, reflection).

3. **Threat Model Formulation**:
   - Extract attacker capabilities, trust boundary crossings, and security invariant definitions.

4. **Vulnerability Verification & Reporting**:
   - For any suspected vulnerability, verify the call path and invariant failure.
   - Propose minimal, non-breaking remediation patches.
