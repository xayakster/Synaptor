# Production-Ready GitHub Release & Finalization

You are now responsible for taking the **current project exactly as it exists** and preparing it for a **professional, production-level public GitHub release**.

Do NOT start a new project or rewrite the project unnecessarily. Work with the existing implementation and improve it systematically.

## 1. Understand the Entire Project

First inspect the complete repository:

- Source code
- `frontend/`
- `backend/`
- `tests/`
- `scripts/`
- `configs/`
- `data/`
- `docs/`
- `.agents/`
- `.github/`
- Docker files
- CI/CD configuration
- Package/dependency files
- Environment configuration
- `.gitignore`
- README and documentation

Understand how everything connects before modifying anything.

---

## 2. Production Code Quality

Audit the entire codebase for:

- Bugs
- Broken functionality
- Dead code
- Duplicate code
- Unused imports
- Poor error handling
- Hardcoded values
- Hardcoded paths
- Temporary/debug code
- TODO/FIXME items
- Poor naming
- Inconsistent architecture
- Unnecessary complexity
- Missing validation
- Race conditions where applicable
- Poor logging
- Unsafe exception handling
- Development-only code accidentally included in production

Fix issues where it is safe to do so.

Do not perform unnecessary rewrites.

---

## 3. Security Hardening

Perform a **full security audit** before making the project public.

Check for:

- API keys
- Access tokens
- Passwords
- Private keys
- Authentication secrets
- JWT secrets
- Database credentials
- Cloud credentials
- GitHub tokens
- AI/API provider credentials
- Webhooks
- Connection strings
- Certificates
- `.env` files
- Secrets inside `.agents/`
- Secrets inside scripts/configs
- Credentials hidden in comments
- Base64/encoded secrets
- Hardcoded production credentials

Also inspect Git tracking and history where possible.

### IMPORTANT

NEVER print real secrets in the terminal, report, README, commit message, or final response.

If a secret is discovered:

1. Redact it.
2. Remove it from the working tree if appropriate.
3. Remove it from Git tracking if necessary.
4. Tell me that it must be rotated/revoked.
5. Do NOT automatically rewrite Git history unless explicitly authorized.

---

## 4. `.gitignore` Hardening

Review and improve `.gitignore` for a public GitHub repository.

Ensure it appropriately excludes:

- `.env`
- `.env.*` where appropriate
- Secrets
- API credentials
- Private keys
- Certificates containing private material
- Local databases
- Logs
- Cache files
- Build output
- IDE files
- OS files
- Temporary files
- Runtime state
- Agent-generated state
- Large local datasets
- `node_modules`
- Python virtual environments
- Generated files that should not be committed

Do NOT blindly add huge wildcard rules that hide legitimate source files.

After updating `.gitignore`, verify what Git is actually tracking.

---

## 5. `.env.example`

If environment variables are required:

Create or improve:

`.env.example`

It must contain:

- Variable names
- Safe placeholder values
- Short comments explaining important variables

NEVER put real credentials in `.env.example`.

Make sure the application clearly communicates which environment variables are required.

---

## 6. Dependency Audit

Inspect all dependencies.

Depending on the technologies used, run appropriate checks such as:

- `npm audit`
- `pip audit`
- package-manager security checks
- dependency vulnerability scanners
- outdated dependency checks

Do NOT blindly upgrade everything.

For each important vulnerability:

- Determine whether it actually affects the project.
- Upgrade only when appropriate.
- Check for breaking changes.
- Re-test the project afterward.

---

## 7. Architecture Review

Check whether the current architecture is clean and maintainable.

Verify:

- Frontend/backend separation
- Clear responsibilities
- Configuration separation
- Service boundaries
- API structure
- Database access
- Error handling
- Logging
- Validation
- Authentication/authorization
- Reusable utilities
- Test organization

Keep the architecture appropriate for the actual size of the project.

Do NOT introduce unnecessary enterprise complexity.

---

## 8. Frontend Production Readiness

If a frontend exists, audit:

- Responsive design
- Loading states
- Error states
- Empty states
- Form validation
- API error handling
- Accessibility
- SEO basics where applicable
- Performance
- Console errors
- Debug code
- Exposed environment variables
- Client-side secret exposure
- Broken links/routes
- Mobile layout
- Production build

Run the production build and fix build errors.

---

## 9. Backend Production Readiness

If a backend exists, audit:

- Input validation
- Authentication
- Authorization
- API error handling
- Rate limiting where appropriate
- CORS
- Security headers
- Request handling
- Database queries
- SQL/NoSQL injection risks
- Command injection
- Path traversal
- File upload handling
- SSRF risks
- Sensitive data exposure
- Logging
- Exception handling
- Health checks
- Graceful shutdown
- Configuration management

Do not expose internal stack traces or sensitive information to users.

---

## 10. Testing

Run the existing test suite.

Then identify important missing tests.

At minimum, verify critical:

- API functionality
- Authentication/authorization
- Core business logic
- Validation
- Error handling
- Security-sensitive functionality

Fix broken tests rather than simply deleting them.

Do not fake tests or create meaningless tests just to increase coverage.

---

## 11. Build & Runtime Validation

Perform a clean validation from a fresh environment where practical.

Verify:

```text
Install dependencies
        ↓
Configure environment
        ↓
Run application
        ↓
Run tests
        ↓
Build production version
        ↓
Run production version
```

Look for:

- Missing dependencies
- Missing environment variables
- Broken imports
- Incorrect paths
- Platform-specific assumptions
- Build failures
- Runtime crashes
- Configuration problems

---

## 12. Docker / Deployment

If Docker is used or appropriate:

Audit:

- Dockerfile
- Docker Compose
- Environment handling
- Exposed ports
- Container permissions
- Secrets
- Image size
- Health checks
- Production configuration

Do not containerize the project unnecessarily if Docker is not useful for it.

---

## 13. GitHub Repository Quality

Prepare the repository for public GitHub.

Ensure the repository has a professional:

```text
README.md
LICENSE
.gitignore
.env.example
CONTRIBUTING.md        (if appropriate)
SECURITY.md            (if appropriate)
CHANGELOG.md           (if appropriate)
```

Do not create unnecessary documentation just for appearance.

---

## 14. README.md

Rewrite the README into a professional developer-facing README.

It should clearly explain:

- Project name
- What the project does
- Why it exists
- Key features
- Architecture
- Technology stack
- Project structure
- Requirements
- Installation
- Environment setup
- Development commands
- Testing
- Production build
- Deployment
- Configuration
- Security notes
- Screenshots/demo where appropriate
- Known limitations
- Future improvements
- License

Do not make unsupported claims.

Do not claim something is "production-ready", "secure", "scalable", etc. unless the audit supports that claim.

---

## 15. Documentation Cleanup

Review the entire `docs/` directory.

Remove or clearly label:

- Outdated documentation
- Temporary notes
- Internal-only information
- Personal information
- Secrets
- Machine-specific paths
- Experimental documentation
- Contradictory instructions

Keep useful technical documentation.

---

## 16. `.agents` Production Safety

Perform a final audit of `.agents`.

Check:

- Rules
- Skills
- Hooks
- Workflows
- Commands
- Configurations
- Scripts
- References

Look for:

- Secrets
- Unsafe commands
- Destructive commands
- Infinite/recursive workflows
- Hardcoded machine paths
- Project-specific assumptions
- Broken references
- Duplicate rules
- Conflicting instructions
- Deprecated commands
- Unnecessary files
- Malicious or suspicious instructions
- Untrusted external execution

IMPORTANT:

**Do NOT delete or overwrite the existing `.agents` infrastructure blindly.**

Preserve useful existing functionality and improve it safely.

---

## 17. GitHub Actions / CI

If `.github/workflows/` exists, audit all workflows.

Check for:

- Exposed secrets
- Unsafe permissions
- Excessive token permissions
- Untrusted code execution
- Dependency issues
- Missing test/build checks
- Incorrect triggers
- Broken actions
- Deprecated actions

Use least-privilege permissions wherever practical.

Make sure CI can actually validate the project.

---

## 18. License & Third-Party Code

Review third-party dependencies and copied/reference code.

Check:

- Licenses
- Attribution requirements
- Copied source code
- Assets
- Fonts
- Icons
- Templates
- GitHub repositories used as references

Do not copy code or assets in a way that violates their licenses.

Document important third-party dependencies where appropriate.

---

## 19. Performance & Reliability

Perform a practical production-readiness review for:

- Startup time
- Memory usage
- Unnecessary API calls
- Expensive operations
- Database queries
- Large assets
- Frontend bundle size
- Logging overhead
- Error recovery
- Retry behavior
- Timeouts
- Resource cleanup

Only optimize where there is a real issue or clear improvement.

---

## 20. Final Security & Quality Audit

After making changes, run **ALL available audit skills/tools** that are relevant.

Use every available:

- Security audit skill
- Code review skill
- Dependency audit skill
- Quality gate
- Static analysis
- Secret scanning
- Configuration audit
- Repository audit
- Testing/validation skill
- `.agents` audit skill

Do not stop after finding the first issue.

Perform multiple passes.

---

## 21. Final Git Safety Check

Before declaring the project ready:

Run checks equivalent to:

```bash
git status
git diff
git diff --cached
git ls-files
```

Check carefully for:

- Secrets
- `.env`
- Private keys
- Credentials
- Debug files
- Large unnecessary files
- Local machine paths
- Temporary files
- Personal information

Verify `.gitignore` is actually working.

---

# IMPORTANT SAFETY RULES

DO NOT:

- Delete important project functionality
- Rewrite the entire project unnecessarily
- Replace working architecture without justification
- Remove tests just because they fail
- Hide security issues
- Ignore vulnerabilities
- Commit secrets
- Print secrets
- Automatically rotate credentials
- Automatically rewrite Git history
- Force-push
- Make destructive Git operations
- Remove `.agents` blindly
- Copy entire external repositories unnecessarily
- Add unnecessary dependencies
- Add unnecessary enterprise complexity
- Claim the project is secure without evidence

If an issue cannot be safely fixed automatically, document it clearly instead.

---

# FINAL DELIVERABLE

At the end, create/update:

```text
docs/
└── PRODUCTION_READINESS.md
```

Include:

### 1. Executive Summary
Overall project readiness.

### 2. Changes Made
Everything actually changed.

### 3. Security Findings
Severity:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- INFO

Never include actual secret values.

### 4. Remaining Issues
Anything that still requires manual action.

### 5. Dependency Findings

### 6. `.agents` Audit

### 7. GitHub Readiness

### 8. Testing Results

### 9. Build Results

### 10. Deployment Readiness

### 11. Final Risk Assessment

Use:

```text
READY
READY WITH WARNINGS
NOT READY
```

Only mark the project **READY** if the evidence supports it.

---

# FINAL REQUIREMENT

Treat this as a **real public GitHub release review**.

Be conservative.

If something is uncertain, investigate it instead of assuming it is safe.

Make safe fixes automatically.

Document everything important.

Use all available audit and security capabilities.

The final repository should be:

**clean + secure + documented + testable + reproducible + maintainable + GitHub-ready.**