# Agent Reach Safe Internet Policy

**Source:** `https://github.com/Panniantong/Agent-Reach.git` (Commit: `94f06c1969dfc1834001269d79d3ad0972d9dee6`)

## Internet Research & Channel Access Protocol

1. **Read-Only Operations**:
   - Agent Reach is strictly intended for **fetching and analyzing** external information (discussions, issues, papers, documentation, transcripts).
   - Never perform unconfirmed write operations (posting, liking, commenting, deleting).

2. **Credential Boundaries & Privacy**:
   - Never hardcode secrets, API keys, session tokens, or browser cookies in repository files or prompt logs.
   - Use environment variables (e.g. `EXA_API_KEY`, `TWITTER_BEARER_TOKEN`, `REDDIT_CLIENT_ID`) or local uncommitted `.env` files.
   - Run `agent-reach doctor --json` to diagnose available backends before querying external services.

3. **Rate Limiting & Politeness**:
   - Respect rate limits and robots.txt policies of external platforms.
   - Prefer structured API backends (e.g. Exa, official APIs) over aggressive web scraping.
