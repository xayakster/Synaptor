# /ui-ux-pro-max Workflow

Search design intelligence, generate color palettes, select font pairings, and audit UX guidelines for web, mobile, and desktop.

**Source:** `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git`

## Trigger
- User invokes `/ui-ux-pro-max`, `/design-system`, or asks to design, style, or review UI/UX interfaces.

## Instructions

1. **Design System & Visual Direction**:
   - Query design system for a product domain:
     ```bash
     python .agents/skills/ui-ux-pro-max/scripts/search.py "saas dashboard" --design-system
     ```

2. **Domain-Specific Queries**:
   - Typography: `python .agents/skills/ui-ux-pro-max/scripts/search.py "modern tech" --domain typography`
   - Colors: `python .agents/skills/ui-ux-pro-max/scripts/search.py "fintech trust" --domain color`
   - UX Guidelines: `python .agents/skills/ui-ux-pro-max/scripts/search.py "form validation" --domain ux`
   - Animation / Motion: `python .agents/skills/ui-ux-pro-max/scripts/search.py "card reveal" --domain motion`
   - Stack-specific patterns: `python .agents/skills/ui-ux-pro-max/scripts/search.py "react" --stack react`

3. **Apply & Verify**:
   - Use returned semantic tokens, typography scales, and UX rules to implement high-quality interfaces.
