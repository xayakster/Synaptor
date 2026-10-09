# Brag Video Generation Safety & Privacy Rules

**Upstream:** `https://github.com/latent-spaces/brag.git`  
**Applies To:** Video generation, demo scripting, screen recordings, and media rendering workflows

---

## 🔒 Mandatory Safety & Privacy Guidelines

### 1. Zero External Uploading / Publishing Invariant
- Video generation, storyboard creation, and rendering **MUST** run strictly on the local machine.
- The agent **MUST NEVER** upload, publish, stream, or transmit video files, code clips, audio voiceovers, or project assets to any remote video hosting service, cloud storage, or social media platform without explicit, unambiguous user confirmation.

### 2. Secret & Sensitive Data Scrubbing
- Before generating storyboards or code highlight slides, the agent **MUST** verify that no confidential information is exposed.
- Never include in video slides:
  - API keys, tokens, or private secrets.
  - Internal proprietary endpoints, private IP addresses, or unmasked auth tokens.
  - Personal identifiable information (PII) or uncommitted sensitive files.

### 3. Explicit User Confirmation Before Heavy Rendering
- Video rendering with FFmpeg or Remotion is CPU/GPU-intensive.
- The agent **MUST** present the narrative script and scene outline to the user first, and only initiate full MP4 video encoding upon user request.

### 4. Git Hygiene & Artifact Isolation
- All video output files, intermediate frame caches, and audio files must reside in `brag-out/` or `.brag-cache/`.
- Video media files **MUST NEVER** be checked into git repositories.
