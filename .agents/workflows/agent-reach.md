# /agent-reach Workflow

Perform multi-channel internet research across 16+ platforms (Twitter/X, Reddit, GitHub, YouTube, XiaoHongShu, Bilibili, Exa Search, Web, RSS).

**Source:** `https://github.com/Panniantong/Agent-Reach.git`

## Trigger
- User invokes `/agent-reach`, asks to research external topics across the web, or queries social/technical discussions.

## Instructions

1. **Doctor Diagnosis**:
   - Check channel availability and backend connectivity:
     ```bash
     python .agents/tools/agent_reach/cli.py doctor --json
     ```

2. **Execute Multi-Channel Research**:
   - For web & deep research: Use Exa or Web channel.
   - For developer discussions & issues: Query GitHub and Reddit.
   - For multimedia transcripts: Extract YouTube or Bilibili subtitles.
   - For Chinese social insights: XiaoHongShu / Bilibili / V2EX.

3. **Synthesize & Cite**:
   - Combine perspectives from multiple channels.
   - Provide direct source URLs and reference citations.
