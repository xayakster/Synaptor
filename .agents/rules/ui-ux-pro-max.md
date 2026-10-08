# UI/UX Pro Max Design Intelligence Rules

**Source:** `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill.git` (Commit: `1a2c459b35f26116fd165b0a0f30597f252749ff`)

## Core Design Principles

1. **Accessibility by Default (CRITICAL)**:
   - Minimum WCAG AA color contrast (4.5:1 for normal text, 3:1 for large text & UI elements).
   - Visible focus indicators (`:focus-visible`). Never remove focus outlines without accessible custom styling.
   - All interactive elements must have a minimum touch target size of **44×44px** on mobile.
   - Descriptive `aria-label` or visually hidden text for icon-only buttons.

2. **Typography & Font Pairings**:
   - Minimum body text size of **16px** with `line-height: 1.5`.
   - Use curated font pairings (e.g. Inter + Outfit, Plus Jakarta Sans + JetBrains Mono).
   - Use responsive typography scales (`clamp()`).

3. **Color Palettes & Semantic Tokens**:
   - Use semantic CSS variables/tokens (`--bg-primary`, `--text-primary`, `--accent`, `--border`) instead of raw hardcoded hex in component files.
   - Avoid harsh `#000000` on `#FFFFFF`; use refined neutrals (`#0F172A`, `#1E293B`).

4. **Interaction States & Motion**:
   - Provide visual feedback for every state: default, `:hover`, `:active`, `:focus-visible`, `:disabled`, and loading spinners.
   - Support `prefers-reduced-motion` media queries.

5. **Local Catalog Querying**:
   - When choosing styles, palettes, font pairings, or component patterns, query the local catalog:
     ```bash
     python .agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain>
     ```
