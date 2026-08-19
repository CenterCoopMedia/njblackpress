# AI slop prohibitions

Hard rules for this project. Date: 2026-08-19. These patterns are the visual fingerprint of an AI-generated interface. They are banned on every page, in every component, for every future contributor — human or agent.

A tell is an unspecified default, not a banned color or component in the abstract. The failure is reaching for a pattern because it is what a model auto-completes to, not because the pattern is inherently wrong. This project has already made deliberate typography and color choices in `DESIGN_DIRECTION.md`. Those choices stay. What follows is the list of defaults that must never leak back in.

## The list

**Eyebrow text.** A small all-caps kicker label sitting above a heading ("ARCHIVE", "MISSION STATEMENT", "PUBLICATION DETAILS"). Delete it or fold its words into the heading itself. If a section needs a label, use a `.rail-wood` bar with the label sitting at the rail's edge, not floating above the heading as a separate line.

**Italic hero titles.** Italicizing a word inside a large display headline for emphasis ("Historical *highlights*", "Contemporary *voices*", "*ARCHIVE*"). Use weight, color from the palette, or a rail-wood underline for emphasis instead. Italics stay only where they carry real grammatical meaning: publication titles in running text, foreign-language phrases, `<cite>` elements.

**Status pills and badges.** A bordered, padded, uppercase capsule reading "status: active" or similar. Set status as plain text within the sentence that already carries it — e.g., the lifespan line: "1968–1974" already implies ceased; "1941–present" already implies active. Where a status word is still needed, it is inline text with no border, no pill background, no separate visual container.

**Serif type.** Updated 2026-08-19 on Joe's ruling: there is no serif face on this site. Fraunces is removed, and no serif replaces it. The display face is a bold newspaper grotesque (see section 4 of `DESIGN_DIRECTION.md`); the body face is DM Sans; labels, filters, citations, and provenance are system mono. Three families, one Google Fonts request. The only use of a serif that could ever be justified is setting quoted archival material — a scanned motto, a transcribed masthead line — and even that needs a decision on the record before it ships. Running prose, captions, and UI chrome never leave DM Sans, and the display face never carries a paragraph.

**Purple/indigo gradient everything.** Violet, indigo, or purple as a primary or accent color, especially in a gradient. This project uses the wood/fabric palette (`walnut`, `oak`, `linen`, `thread`, `stain`) with `stain` (#e2662b, burnt sienna) as the only accent. No purple appears anywhere, gradient or solid.

**Gradient text and gradient buttons.** `background-clip: text` rainbow or two-tone gradients on headings or CTA buttons. All fills in this project are solid. No gradient text, ever.

**Glassmorphism cards.** Frosted-glass translucent panels with blur and a light border, floating above a background. This project's cards sit in the furniture (`.surface-cloth` on `walnut-700`, a hairline border, no outer shadow, no blur, no translucency).

**Emoji as bullets or icons.** Rocket, sparkle, checkmark, or lock emoji standing in for a real icon or a list marker. No emoji anywhere in UI chrome. If an icon is needed, it is a plain SVG or none at all — this project's icon language is currently text and rules, not pictograms.

**Rounded-2xl + shadow on every card.** A single large border-radius token (`rounded-2xl`, `rounded-3xl`) plus a soft drop shadow applied uniformly to every card on the page. This project's cards are square-cornered or minimally rounded (`rounded-sm` at most on small chips), with no outer box-shadow — see `.surface-cloth`, which uses only inset highlights, never an outer shadow implying the card floats.

**Centered hero + pill CTA formula.** A centered headline, a subhead, and one or two pill-shaped buttons, stacked and center-aligned, as the entire hero. This site's hero is left-aligned editorial copy with a rail-wood accent, not a centered marketing block.

**Three/four-feature-card rows.** A `grid-cols-3` or `grid-cols-4` row of identical icon-topped cards ("comprehensive," "seamless," "powerful") used to describe abstract features rather than actual archive content. This site has no abstract feature-marketing section at all; every card on the page represents a real publication, evidence item, or data point.

**Sparkle/rocket/checkmark icon spam.** Decorative icons used purely for visual filler rather than to communicate state. Any icon that appears must be load-bearing — indicating a real status, a real link type, or a real action — never decoration.

**Hype microcopy.** "Transform," "supercharge," "unleash," "seamlessly," "comprehensive," "cutting-edge," and similar filler adjectives applied to the archive itself. Copy describes what a record actually is and what proof it holds, per the governing idea in `DESIGN_DIRECTION.md` — "what is this record, what proof do we hold, how sure are we." No promotional language about the site or the tool.

**Dark-mode-default with neon accents.** A permanently dark theme paired with a glowing, saturated accent color and colored box-shadow/text-shadow "glow" effects. This site is dark by deliberate design choice (the reading-room material language), but the accent (`stain`) is a muted burnt sienna with no glow, no neon, and `.type-impression` text-shadow is restricted to display headings 32px and above, weight 700+, per the accessibility caveat already in `DESIGN_DIRECTION.md`.

**Bento grids.** An asymmetric grid of variously sized tiles arranged for visual variety rather than to reflect the actual shape of the data. This site's grids (evidence cards, publication cards) use one consistent card size and a predictable column count, because the point is comparability between records, not visual novelty.

**Floating blob backgrounds.** Soft, colorful, animated or static blob/mesh shapes behind hero or section content. Banned outright — no blobs, no mesh gradients, no aurora backgrounds, anywhere.

**Fake testimonial cards.** Quote-plus-avatar-plus-name cards used as social proof for a tool or product. Not applicable to an archive with no product to sell, and not to be added.

**Cursor-following effects.** Glow, particles, or elements that track mouse position. None on this site. The only motion permitted is the 180ms rail-reveal on button hover already specified in `DESIGN_DIRECTION.md`.

**Uniform 8px-radius sameness / animation spam.** Every interactive element getting the same hover scale-up, fade-in-on-scroll, or radius token regardless of what it is. Motion in this project is used only to communicate state (the rail reveal on hover, the focus ring), never as decoration, and it respects `prefers-reduced-motion`.

**Untouched shadcn/Tailwind defaults.** Reusing `bg-card`, default `--primary`, default `--radius`, or the stock slate/zinc gray scale without overriding it. This project already overrides every color token through the wood/fabric palette; no component may fall back to an unstyled default.

## What stays (documented exceptions)

- **One bold grotesque display face** — headings, card titles, statistic numerals, and the drop cap. Not a "serif" exception, because it is not a serif; it is the wood-type-poster reference documented in `DESIGN_DIRECTION.md` section 4.
- **Italic on quoted archival material** — a mission statement or masthead motto is a quotation, so it may set italic in DM Sans. This is not an "italic hero title" violation. Italic on a heading, a hero word, a nav link hover, or a UI label still is.
- **Dark background** — a deliberate material choice (the reading room, not the scanner), not the AI "permanent dark mode" default, because it comes with a specific warm palette and documented contrast ratios, not an unstyled `bg-black`.
- **Mono, uppercase, tracking-wide labels used as functional UI chrome** — filter labels, provenance lines, rights labels — stay, because they are load-bearing metadata, not decorative eyebrow text sitting above a heading for atmosphere. The distinguishing test: does the label sit inside the component it describes (a filter group, a citation line) or does it float above a heading as an unnecessary preamble? The former is fine; the latter is prohibited.

## Sources

- [AI Design Slop: Why AI-Generated UI Looks Generic — and the Fix — SmoothUI](https://smoothui.dev/blog/ai-design-slop)
- [AI Slop Fonts and Gradients: The Tells That Give Away AI Design — 925 Studios](https://www.925studios.co/blog/ai-slop-design-tells)
- [AI Slop Design: Why AI-Generated UI Looks Generic (Fix Guide 2026) — VibeCodeKit](https://vibecodekit.dev/ai-slop-design)
- [Unslop UI: Kill the AI Design Tells — Claude Code Playbooks](https://www.claudecodehq.com/playbooks/unslop-ui)
- [AI Design Slop: 16 Patterns That Out Your App as Vibe-Coded — Developers Digest](https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it)
- [Why Your AI Keeps Building the Same Purple Gradient Website](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)
