# Design direction

Decision document for issue #37. It sets the direction for issues #38, #39, #40, and #41 before any code is written. Each section picks one option. Rejected options get one line each.

Author: design-direction agent. Date: 2026-08-19.

## The governing idea

The site is a finding aid, not a dashboard. Every screen must answer three questions in this order: what is this record, what proof do we hold, and how sure are we. Design decisions that make the archive look more complete than it is are wrong, even when they look better.

Two facts from the data drive almost everything below.

The evidence is thin and uneven. 137 of 138 publications carry evidence, but 118 of them carry exactly one item, and only three carry ten. Of 182 evidence entries, 107 are `metadata_only` — a Danky catalog citation with no publishable image. So the common case is one text-only citation card, not a gallery of clippings. A grid layout designed for the three rich records will make the other 135 look empty. Design for the single-card case first and let the rich records use the same components repeated.

The narrative is concentrated. 81 events cover 1840s–2020s, but 26 sit in the 1930s and 35 in the 1930s–1940s. 13 story threads exist; 5 of them are 1930s–1940s Newark. The timeline must show that concentration honestly rather than smoothing it.

## 1. Evidence galleries on publication detail pages

**Direction: an "evidence" section built from one card component with three rights variants, laid out in a single-column stack on mobile and a two-column stack on desktop. Not a masonry gallery, not a lightbox-first grid.**

The section sits directly under the historical notes and above the related-publications section on `publication.html`. Heading: "Evidence we hold". A one-line count sits under it in mono type: "1 item — catalog entry only" or "10 items — 4 published in full, 3 cited clips, 3 citation only". State the shape of the holdings before the reader scrolls.

One card component, `.evidence-card`, with a rights variant class. Every card carries the same four rows in the same order: the visual slot (or its absence), the caption, the citation, and the provenance line (`source`, `date`, and a source link when `url` exists). Constant order is what lets a reader compare cards.

**publishable and publishable_with_credit — full view.** The card shows the image at full card width, capped at 70vh tall, `object-fit: contain` on an ink-950 field so a tall newspaper page does not get cropped. Click or Enter opens a full-view overlay at natural resolution. The overlay is a simple focus-trapped dialog with a close button, Escape to close, and the caption and citation repeated below the image, because an image that leaves its citation behind is a rights problem, not just a design problem. `publishable_with_credit` renders identically but the citation line is required, never truncated, and never collapsed behind a toggle.

**crop_first — cited clip card.** These are newspapers.com pages that may only appear as a crop. The card renders the crop inside a visible frame: a 1px accent-tinted border with a small mono label reading "clip". Under the image, in mono at 11px, uppercase-off (sentence case), the line "Cropped detail. Full page not reproduced." Then the citation. No click-to-expand and no overlay for this variant — expanding a crop invites us to ship the full page later by accident, so the component simply cannot do it. If `cropPlan` text exists in the rights manifest it becomes the alt-text seed, not visible body copy.

**metadata_only — citation card, no image.** This is the majority case, so it must look deliberate rather than broken. No grey placeholder box, no image icon, no "no image available" apology. The card becomes a typographic object: the citation text set in DM Sans at 18–20px as the primary content, with a hairline rule above and below, on ink-800. A mono label reads "citation only". Under the citation, one plain sentence explains the rule in the reader's terms: "The source is a printed bibliography. We quote it; we do not reproduce the page." A card that carries only a citation is still evidence, and giving the citation the full width of the card between two rules says so.

**unlisted** renders as a `metadata_only` card with the label "rights unreviewed" and no citation body. It is a visible gap, which is correct — the data dictionary calls `unlisted` a gap to close, not a publish status.

**Caption and citation treatment.** Caption in DM Sans 15px paper-100, one to two lines, describing what the reader is looking at. Citation in mono 11px paper-300, never italic, never truncated with an ellipsis, selectable so a researcher can copy it. Provenance line last: source name, date, and, when a `url` exists, a text link reading "view at source" with `target="_blank" rel="noopener noreferrer"`. Accent orange is reserved for the rights label and the source link. It never tints the image itself.

**Accessibility, baked in.** Every image element requires a non-empty `alt` attribute sourced from a new `altText` field on the evidence object; issue #43 fills that field, and the renderer must skip rendering an image whose `altText` is missing rather than emit an empty alt. That makes a missing alt a visible bug instead of a silent accessibility failure. Cards are `<figure>` with `<figcaption>`; the citation is `<cite>`. Expandable cards are `<button>` elements, reachable by Tab, with a visible accent focus ring at 2px offset — no `outline: none` anywhere in this component. The overlay returns focus to the card that opened it. All labels pass 4.5:1 against their background: paper-300 (#d1cdc5) on ink-800 passes; accent (#ff4d00) on ink-800 does not reach 4.5:1 at small sizes, so accent is used for 11px labels only when paired with a non-color cue (the border, the label word itself), never as the only signal of rights status.

Rejected: a masonry or justified gallery — it would make 118 single-item records look like errors. Rejected: a lightbox library — a new dependency for a feature four records need. Rejected: color-only rights badges — fails colorblind readers and gives no meaning to a screen reader.

## 2. Timelines

### Per-title timeline on the detail page

**Direction: a horizontal spine with a founded marker, a ceased marker, and dated event markers between them, rendered as inline SVG with an HTML list fallback beneath it.**

The spine spans the publication's own lifespan, not the archive's full 1840–2026 range, so an eight-year weekly does not render as a dot. Founded and ceased are the two anchor marks — a filled accent circle at founded, a hollow circle with a cross-bar at ceased. Active titles end the spine with an open arrow and the label "still publishing". Events from `events.json` whose `publicationIds` include this title appear as tick marks on the spine, with the year under each tick. Hover or focus reveals the event title; click scrolls to the matching entry in the list below.

The list below the spine is the real content, not a fallback afterthought. It is an ordered `<ol>` of date, title, and description. Screen reader users get the whole timeline as a list; the SVG carries `role="img"` and an `aria-label` summarizing the span. This is also what renders when a title has one event or none.

**Confidence encoding.** `high` events render as a solid tick and normal body text. `medium` events render as a hollow tick with a dashed connector, and the list entry carries a mono label "medium confidence" plus a short footnote line naming what is unresolved. 11 of 81 events are medium, so this is a real and visible condition, not an edge case. Never hide a medium event and never render it identically to a high one.

**Conflicts.** The editorial memo lists nine unresolved conflicts, several of them dates — the Landscape start year, the Echo founding year, the Newark Herald 1932 folding against Volume 11 in 1938. Where a date is contested, the marker renders as a bracketed range rather than a point, and a footnote states both readings and their sources. A conflict note component, `.conflict-note`, is shared by the detail page, the timeline, and the story pages: a hairline-bordered block on ink-800 with a mono heading "unsettled" and the competing readings in plain sentences. Do not average conflicting dates. Do not pick one silently.

Rejected: a vertical timeline — it wastes horizontal space that lifespan encoding needs. Rejected: a charting library — the whole spine is under 60 lines of hand-written SVG.

### The upgraded decade timeline (issue #39)

**Direction: keep the existing decade bar chart, but split each bar into stacked segments and add an incident row beneath the axis.**

Each decade bar becomes two stacked segments: foundings in accent, foldings in a muted paper-300 tint at 40% opacity. Stacking, not grouping, keeps the existing bar rhythm and the existing hover behavior. Below the axis sits a thin incident row — one small mark per event in that decade, using the same solid/hollow confidence encoding as the per-title timeline. The 1930s will tower over everything with 26 events. That is the truth of the reading base and the memo says so plainly; the design should let it show rather than normalize it away.

The existing `window.njbp.filterByDecade()` hook stays. Clicking a bar still filters the database. Clicking the incident row for a decade scrolls to a decade event list rather than filtering, so the two interactions never fight.

A legend is required, in mono, sentence case, with shape and fill cues described in words. Keyboard users tab across decades; each decade is one tab stop, with arrow keys moving between decades, and the tooltip content also lives in an `aria-live` region so it is announced.

Rejected: separate charts for foundings and foldings — two charts hide the relationship between launch and closure. Rejected: a continuous year-by-year axis — the data has too many null and approximate years to justify year precision.

## 3. Era and story pages

**Direction: one template, `story.html`, driven by `?id=story-00N`, plus one index page, `stories.html`, that groups the 13 threads by era. No page per story, no page per era.**

This matches the existing routing convention exactly — `publication.html?id=X` already works this way — and it keeps the zero-build promise. `stories.html` is the "era" experience: the 13 threads laid out under era headings (1860s–1900s through 1980s–1990s), each thread shown as a card with title, era, a one-sentence pull from the thread text, the count of linked events and publications, and a strength label where one exists. Story-013 is marked weak in the data and must carry a visible "thinly sourced" label on the index, not only on its own page. The memo is explicit that this thread must not lead.

**Reading experience on a story page.** Single column, measure capped at 68 characters, the display face for the thread title, DM Sans at 18px/1.7 for the body. This is the one place on the site that should read like an essay rather than a record. Dark background stays, but body text moves to paper-50 for the long-read passage to buy contrast.

**Inline clippings.** Clippings interrupt the narrative at full measure width, never floated, never wrapped by text. A clipping in a story is the same `.evidence-card` component from the detail page, rendered at a wider size with the caption promoted to a slightly larger size. The three rights variants behave identically to the detail page — a `metadata_only` source inside a story becomes a set-out citation block, which reads naturally as a pull quote and requires no special case. Reusing the component means the rights rules can never drift apart between two pages.

**Navigation between story, publication, and timeline.** Three fixed relationships, all bidirectional.

A story page ends with "publications in this thread" — cards linking to `publication.html?id=N` for each id in `publicationIds`. A story page also carries an inline chronology built from its `eventIds`, using the same spine component as the per-title timeline, scoped to the story's era. Each event in that chronology links to the publication it belongs to when `publicationIds` is populated (73 of 81 events are).

A publication detail page gains a "part of these threads" block whenever the title appears in any story's `publicationIds`. Title 16 appears in four threads and title 9 in three, so this block must handle multiples cleanly — a simple list of story links, not a carousel.

The decade timeline gains, per decade, a link to the stories whose era overlaps that decade. That closes the triangle: timeline to story, story to publication, publication back to timeline.

Breadcrumbs on both new pages, in mono, sentence case: "Archive / Stories / The one-man newspaper of Saddle River". Skip-to-content link on every page. Heading order strictly h1 then h2 then h3 with no levels skipped, because these pages are the ones a screen reader user will navigate by heading.

Rejected: an infinite-scroll narrative across all 13 threads — it destroys deep linking and makes citation impossible. Rejected: a scrollytelling treatment with pinned images — heavy, fragile without a build step, and tonally wrong for the subject.

## 4. Map view (issue #41)

**Recommendation: skip. Build a geography panel instead.**

The reasoning is in the distribution. 138 publications spread across 46 city values, one of them null. Newark holds 40 — 29 percent of the archive. Paramus holds 10, and the memo warns that the Paramus attribution for the two consumer magazines is unconfirmed by any masthead. Trenton holds 9. After that the tail is 5 and below, mostly 1 and 2. A New Jersey map of this data is one large dot over Newark and a scatter of single dots that a reader cannot click reliably at state zoom.

The cost is real for a site with no build step. A map means Leaflet from a CDN, a tile provider with its own terms and attribution requirements, and a geocoding step to turn 46 free-text city strings into coordinates that would then need to live in the data as a new field with its own accuracy problems. It also means an interaction that is hard to make keyboard-accessible and near-impossible to make screen-reader-equivalent, on a project where accessibility is a launch gate. A map would add the most dependency and the most accessibility risk of any item on this list while answering a question — where were these papers — that one sorted bar chart answers better.

The replacement is a geography panel on the index page, next to the decade timeline: cities ranked by publication count, drawn as horizontal bars reusing the existing `.timeline-bar` treatment and the existing city filter. Newark's dominance reads instantly and correctly. Each bar is a link into the archive filtered by that city, which is the action a reader actually wants. Cities with unconfirmed attribution can carry a footnote marker, which a map pin cannot do gracefully.

Revisit the decision only if two things change: city-level evidence density rises so a map pin has something to open, and neighborhood-level addresses appear (the archive already holds one — 130 W. Kinney St., Newark). A Newark street map of newspaper addresses would be a genuinely different and better artifact than a state map of city dots. That is a later project, not this redesign.

## 5. What does not change

State this explicitly so #38 through #41 do not drift.

The palette does not change. ink-950 through ink-600, paper-50 through paper-300, accent #ff4d00 with its hover and light variants. No new colors are introduced. The confidence and rights encodings use shape, fill, border, and words — not new hues.

The type has changed once, and only once: Fraunces is out (see section 4). One display face for headings and display, DM Sans for body and for quoted text, system mono for labels, filters, citations, and provenance. Three families, one Google Fonts request, no more.

The architecture does not change. No build step, no bundler, no framework, no npm. Tailwind stays on the CDN with the same inline config block copied into the new pages. New JavaScript follows the existing IIFE pattern with no imports and no modules, and communicates through the existing `window.njbp` surface. New files are expected to be `docs/js/evidence.js`, `docs/js/story.js`, and `docs/js/stories.js`, plus edits to `publication.js` and `timeline.js`.

The data flow does not change. Pipeline writes `data/*.json`, the frontend reads `docs/data/*.json`, and the evidence array stays generated — never hand-edited, per the data dictionary. The one schema addition this direction requires is `altText` on the evidence object, filled by issue #43.

The existing pages keep their structure. `index.html` gains the geography panel and the upgraded timeline but keeps its section order. `archive.html` is untouched by this direction. `publication.html` gains the evidence section, the per-title timeline, and the threads block; the existing bio, mission, metadata, people, tags, and archive sections stay where they are.

The conventions do not change. Sentence case for every heading, label, button, and legend, including in the new components. External links carry `target="_blank" rel="noopener noreferrer"`. Client-side routing by query param, not one file per record.

## Accessibility as a gate, not a pass

Four checks block launch on any page this direction touches.

Every evidence image has non-empty alt text, and the renderer refuses to emit an image without it. Every interactive element — evidence card, timeline marker, decade bar, city bar — is reachable by Tab, operable by Enter and Space, and shows a visible accent focus ring; nothing anywhere sets `outline: none` without a replacement. Every chart and timeline has a text equivalent in the DOM that is not visually hidden guesswork but the real list the sighted reader also sees. Every text and label pair meets 4.5:1, with accent used as a supporting cue rather than the sole carrier of meaning.

## Material language: wood and fabric

Addendum to the direction above. Date: 2026-08-19. Nothing in sections 1–5 is repealed. The components, the layouts, the evidence rules, and the accessibility gate all stand. This section replaces one clause only: section 5 said the palette does not change. It changes now, and the change is a rotation of hue and warmth, not a new structure. Every token below maps one-to-one onto an existing token, so no component needs new markup.

### The idea

The reading room, not the scanner. The site currently looks like a scan bed: neutral black, cold noise, a signal-orange marker. That reads as digitization, and digitization is a process, not a subject. The subject is a physical press and a physical archive. Headlines in these papers from the 1880s through the 1940s were printed from wood type. The surviving copies live in wooden card cabinets and cloth-bound volumes on library shelves. The interface should be the furniture that holds the evidence, not the machine that copied it.

Two materials, two jobs, and they never trade places.

**Wood is structure.** Everything that frames, separates, supports, or bounds is wood: rules, card edges, section dividers, the timeline rail, button borders, the outer edge of the focus ring. Wood is warm, dark, and load-bearing. It sits under the evidence and never on top of it.

**Fabric is surface.** Everything a reader's eye rests on is cloth: page grounds, card fields, the long-read column of a story page. Fabric is woven, matte, and slightly irregular. It replaces the current uniform digital grain.

**Ink is content.** The evidence itself — images, citations, quoted text — is ink on the cloth. It gets no material treatment at all. This is the rule that keeps the whole thing out of theme-park territory: we style the furniture, never the document.

### 1. Color tokens

The palette rotates from neutral-cold to warm-brown. Wood tones take over the `ink` roles. Textile tones take over the `paper` roles. Both keep the same scale numbering, so existing class names can be swapped one token at a time.

Add this block to the Tailwind inline config in `index.html`, `archive.html`, `publication.html`, and both new pages. Keep `ink`, `paper`, and `accent` defined as aliases during the migration, then delete them at the end.

```js
colors: {
  // wood — structure, grounds, frames
  walnut: {
    950: '#0b0806',  // deepest ground (was ink-950)
    900: '#14100b',  // page ground   (was ink-900)
    800: '#1e1811',  // raised band   (was ink-800)
    700: '#2b2318',  // card field    (was ink-700)
    600: '#3b3122',  // hairline rule (was ink-600)
  },
  oak: {
    500: '#6b563c',  // wood rail, mid grain
    400: '#8a7252',  // rail highlight edge
    300: '#a89179',  // rail top light, decorative only
  },
  // textile — surfaces and text
  linen: {
    50:  '#faf7f0',  // long-read body text (was paper-50)
    100: '#f3eee2',  // default body text   (was paper-100)
    200: '#e3dccc',  // secondary text      (was paper-200)
    300: '#cdc4b1',  // mono labels         (was paper-300)
  },
  thread: {
    400: '#a89c85',  // muted meta text, stitch lines
    500: '#7d7261',  // non-text strokes only, never body copy
  },
  // stain — the accent
  stain: {
    DEFAULT: '#e2662b',  // burnt sienna / wood stain
    light:   '#f0854a',  // accent text on walnut-700 and lighter grounds
    deep:    '#8f3a14',  // hover, pressed, and accent text on linen fields
  },
}
```

**The accent decision: warm it.** `#ff4d00` is retired. The replacement is `#e2662b`, a burnt sienna that reads as wood stain and as the red-brown of oxidized newsprint ink. The reason is not mood. `#ff4d00` is a safety-equipment orange; it is the loudest thing on any screen it appears on, which is why the direction above kept having to fence it off from the evidence. `#e2662b` sits inside the material family, so it can do its job — mark a rights label, a link, a founded marker — without out-shouting a scanned front page. It also fixes a live contrast problem: `#ff4d00` measured 4.65:1 on the old card ground and failed outright on `ink-600`, which is exactly why section 1 had to restrict it to 11px labels paired with a non-color cue. The `stain` ramp solves that with three stops instead of a rule.

Use `stain.DEFAULT` for text and links on `walnut-950`, `walnut-900`, and `walnut-800`. Use `stain.light` for accent text on `walnut-700` and `walnut-600`. Use `stain.deep` for accent text on any linen field, and for hover and pressed states on dark grounds. Non-text marks — the founded circle, a bar fill, a 1px frame — may use `stain.DEFAULT` on any ground in the set, since the bar for non-text is 3:1 and it clears that everywhere.

**Contrast, measured.** All ratios below are computed WCAG 2.1 relative luminance, not estimates.

Body and label pairs, all AA at normal size:

| Text | Ground | Ratio |
|---|---|---|
| linen-100 `#f3eee2` | walnut-900 `#14100b` | 16.36:1 |
| linen-100 `#f3eee2` | walnut-800 `#1e1811` | 15.19:1 |
| linen-200 `#e3dccc` | walnut-700 `#2b2318` | 11.34:1 |
| linen-300 `#cdc4b1` | walnut-700 `#2b2318` | 8.94:1 |
| linen-300 `#cdc4b1` | walnut-600 `#3b3122` | 7.36:1 |
| linen-50 `#faf7f0` | walnut-900 `#14100b` | 17.70:1 |
| thread-400 `#a89c85` | walnut-900 `#14100b` | 7.00:1 |
| thread-400 `#a89c85` | walnut-700 `#2b2318` | 5.72:1 |

Accent pairs:

| Text | Ground | Ratio |
|---|---|---|
| stain `#e2662b` | walnut-950 `#0b0806` | 5.87:1 |
| stain `#e2662b` | walnut-900 `#14100b` | 5.56:1 |
| stain `#e2662b` | walnut-800 `#1e1811` | 5.17:1 |
| stain-light `#f0854a` | walnut-700 `#2b2318` | 6.02:1 |
| stain-light `#f0854a` | walnut-600 `#3b3122` | 4.95:1 |
| stain-deep `#8f3a14` | linen-100 `#f3eee2` | 6.52:1 |
| stain-deep `#8f3a14` | linen-200 `#e3dccc` | 5.52:1 |
| walnut-900 `#14100b` | stain `#e2662b` (fill) | 5.56:1 |

Three tokens are non-text only, and review must enforce it. `oak-500` at 2.73:1 on `walnut-900` and `oak-400` at 4.16:1 are rail and grain strokes; they never carry a word. `oak-300` and `thread-500` are strokes and stitch lines, never body copy. Any pull request that sets `color: oak-*` on running text fails the accessibility gate.

### 2. Texture recipes

No image files. Nothing here loads a byte. Every texture is a layered gradient or the existing SVG turbulence, and every one sits on a surface that already carries a solid `background-color` underneath. If the gradients fail to paint, the page is still a legible warm dark ground with light text.

Keep them subtle. The target is a difference you notice when you turn it off, not one you notice when you turn it on. Every alpha value below is deliberate. If a texture reads as a pattern from arm's length, it is wrong.

**Woven linen ground.** This replaces the current full-screen noise overlay. Two orthogonal repeating gradients at a 3px period build a warp and a weft. A slow radial gradient adds the uneven light of a room. The old turbulence stays but drops to a third of its weight and gains a warm blend, so it reads as fiber rather than sensor noise.

```css
.surface-woven {
  background-color: #14100b;
  background-image:
    /* weft */ repeating-linear-gradient(0deg,
      rgba(232, 224, 208, 0.014) 0px, rgba(232, 224, 208, 0.014) 1px,
      transparent 1px, transparent 3px),
    /* warp */ repeating-linear-gradient(90deg,
      rgba(232, 224, 208, 0.010) 0px, rgba(232, 224, 208, 0.010) 1px,
      transparent 1px, transparent 3px),
    /* room light */ radial-gradient(120% 80% at 50% 0%,
      rgba(138, 114, 82, 0.10) 0%, transparent 60%);
  background-attachment: fixed, fixed, fixed;
}
```

The grain overlay div in the body stays, with three edits. Opacity drops from `0.20` to `0.07`. `mix-blend-mode` changes from `overlay` to `soft-light`. The SVG `baseFrequency` rises from `0.65` to `0.9`, so the grain is finer than the weave and does not beat against it.

**Cloth card surface.** Book cloth is a diagonal weave with a raised nap that catches light along its top edge. Two 45-degree gradients give the weave. A 1px inset highlight on top and a 1px inset shadow on the bottom give the nap. No outer `box-shadow` — cards sit in the furniture, they do not float above it.

```css
.surface-cloth {
  background-color: #2b2318;
  background-image:
    repeating-linear-gradient(45deg,
      rgba(243, 238, 226, 0.012) 0px, rgba(243, 238, 226, 0.012) 1px,
      transparent 1px, transparent 4px),
    repeating-linear-gradient(-45deg,
      rgba(11, 8, 6, 0.16) 0px, rgba(11, 8, 6, 0.16) 1px,
      transparent 1px, transparent 4px);
  box-shadow:
    inset 0 1px 0 rgba(168, 145, 121, 0.10),
    inset 0 -1px 0 rgba(11, 8, 6, 0.45);
}
```

**Wood rail.** The rail is the site's one piece of visible furniture. It is a 3px horizontal bar used under section headings, as the timeline axis, and as the top edge of a raised band. The grain comes from hard color stops at irregular percentages, which is what stops it from reading as a repeating pattern. Do not raise it above 4px. A rail thick enough to show grain is a rail thick enough to look like a texture swatch.

```css
.rail-wood {
  height: 3px;
  border: 0;
  background-image:
    linear-gradient(180deg,
      #a89179 0%, #8a7252 35%, #6b563c 36%,
      #6b563c 72%, #3b3122 73%, #2b2318 100%),
    linear-gradient(90deg,
      #6b563c 0%, #5e4b34 17%, #6b563c 18%, #6b563c 41%, #5a4830 42%,
      #6b563c 43%, #6b563c 78%, #604d36 79%, #6b563c 100%);
  background-blend-mode: multiply;
}
```

Where a 3px rail is too heavy, use a 1px hairline at `walnut-600` (`#3b3122`). That hairline is the default separator across the site and replaces every current `border-white/10`.

**Thread underline.** Links in body copy do not get a solid underline. They get a stitched one: a dotted 2px underline in `thread-400` at 3px offset. It reads as running stitch at text size and stays a real `text-decoration`, so screen readers and forced-colors mode still see a link.

```css
.link-thread {
  text-decoration: underline;
  text-decoration-style: dotted;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
  text-decoration-color: #a89c85;
}
.link-thread:hover { text-decoration-color: #e2662b; }
```

**Stitched divider.** Between major sections, a dashed 1px `thread-500` line at 6px dash length, centered, with 2rem of space above and below. Use it sparingly — one per section boundary at most.

**Required texture opt-outs.** All the recipes must degrade. Ship this block with them.

```css
@media (prefers-contrast: more), (forced-colors: active) {
  .surface-woven, .surface-cloth { background-image: none; }
  .rail-wood { background-image: none; background-color: CanvasText; }
  .type-impression { text-shadow: none; }
  .grain-overlay { display: none; }
}
@media (prefers-reduced-transparency: reduce) {
  .grain-overlay { display: none; }
}
```

### 3. Component mapping

**The evidence card, three rights variants.** All three cards become `.surface-cloth` on `walnut-700`, with a 1px `walnut-600` hairline and no outer shadow. The material distinction between them is the frame, and the frame is the rights status made physical. `publishable` and `publishable_with_credit` get no frame at all — the image sits directly on the cloth field, edge to edge with the card's padding, because a document we may reproduce should not look contained. `crop_first` gets a 1px `stain` frame around the crop with a 4px cloth-colored inset between frame and image, so the crop reads as a mounted fragment rather than a whole page. `metadata_only`, the 107-item majority case, is where the material language earns its keep: the card becomes a bound-volume shelf label. Its citation sets in DM Sans at 19px `linen-100` between two `.rail-wood` bars at full card width, the mono rights label sits at the left end of the upper rail, and the card takes 2rem of vertical padding so it has the presence of an object instead of the emptiness of a missing image. A citation set between two wood rails looks deliberate. That is the central design problem of section 1, solved with furniture.

**The timeline bars and the per-title spine.** The decade chart's axis becomes a `.rail-wood` running the full chart width — the shelf the decades stand on. Bars rise from it in `stain` for foundings and `thread-500` at 40% opacity for foldings, which keeps the stacked encoding from section 2 unchanged. Each bar is flat-filled with a single 1px `oak-500` line down its left edge, which gives it the look of a wooden type sort standing on end without any texture inside it. The 1930s tower keeps its full height; nothing is normalized. On the per-title spine, the lifespan line is a 2px `oak-500` stroke — the rail again, at furniture scale — with the founded marker a filled `stain` circle and the ceased marker a hollow `walnut-600` circle with a cross-bar. Medium-confidence ticks stay hollow with a dashed connector, and the dash now matches the 6px stitch of the divider, so uncertainty and thread become one visual idea across the site.

**Story pages.** This is the one place where fabric takes over completely. The long-read column sits on `.surface-woven` over `walnut-900`, capped at 68 characters, body in DM Sans 18px/1.7 `linen-50` at 17.70:1. The thread title takes the letterpress treatment from section 4. Section breaks inside the essay use the stitched divider, never a rail — rails frame evidence, stitches pace prose. Inline `.evidence-card` clippings interrupt at full measure width and keep their cloth field, which now reads as a plate tipped into a book. The `metadata_only` variant inside a story becomes a set-out citation between two rails, which is already a pull quote, so no special case is needed — exactly as section 3 promised. The "publications in this thread" block at the foot of the page sits on `walnut-800` under a single wood rail.

**Buttons and filters.** Controls are wood, not fabric — a reader touches the furniture, not the cloth. Default state: transparent ground, 1px `walnut-600` border, `linen-200` mono label. Hover: border to `oak-500`, label to `linen-50`, and a 2px `.rail-wood` strip revealed along the bottom edge by an `::after` that grows from `scaleX(0)` in 180ms. That is the only motion in the material language. Active or selected: `walnut-700` cloth fill, `oak-400` border, `stain.light` label at 6.02:1. Focus: a 2px `stain` ring at 2px offset, unchanged from the existing rule and never removed. Chips in the applied-filters row take the cloth fill plus a `thread-400` dotted left edge, so an applied filter looks tacked on rather than built in, which is what it is.

### 4. Type treatment

Revised 2026-08-19. Fraunces is removed from this project. Joe's ruling: no serif display face, and no serif anywhere except quoted archival material. Everything below replaces the earlier Fraunces treatment. The `opsz`, `SOFT`, and `WONK` instructions are void — they were Fraunces axes and no replacement carries them.

**The reference is wood type, not a revival serif.** Nineteenth and early twentieth century American newspapers set their headlines from wood and metal sorts in bold grotesques — Franklin Gothic, Alternate Gothic, and their condensed relatives. That is the display language here: a bold sans with newspaper heritage, set large, tracked at or near zero, on two deliberate lines. No serif, no blackletter, no script.

**The face is not final.** Big Shoulders was implemented and rejected by Joe on sight. A specimen page renders five candidates against the real hero and a real publication card so the choice is made on evidence, not description: `docs/type-specimen.html` (temporary, not part of the site). Candidates and one-line notes:

- Libre Franklin — Franklin Gothic lineage, full 400–900 variable range, the most newspaper-native and the most conservative. Applied provisionally so the site is not broken while Joe decides.
- Archivo (wdth 125) — a grotesque drawn for print headlines with a real width axis; expanded reads squarer and more monumental than Libre Franklin but is close enough that the two compete.
- Oswald — condensed Alternate Gothic tradition; fits long publication names in less width, but tops out at 700 and reads more "web poster" than press.
- Barlow Condensed — same condensed job as Oswald with slightly rounded, industrial letterforms; the softest of the five and the least press-like.
- League Gothic — the closest to a real wood-type sort, but ships one weight only, so headings and card titles cannot differ in weight. That alone probably disqualifies it.

Rejected outright: Big Shoulders (Joe: ugly); Anton (single weight, no range); Inter, Poppins, Montserrat, Space Grotesk (the AI-default set, banned by the prohibitions list); any serif or slab (Joe's ruling above).

**Hero sizing is a fixed rule, whatever the face.** The hero h1 sits in an 8-of-12 column, roughly 875px at the 1400px cap. It must render on exactly two lines at every width: "THE BLACK PRESS" then "ARCHIVE". Fixed breakpoint sizes cannot guarantee that across faces, so the size is fluid and capped: `font-size: clamp(1.9rem, 6vw, 4.75rem)`. Any face swap re-checks the longest line against the column before it ships.

**Weight and tracking.** Display headings set 800 (or the family's heaviest available below 900) at `tracking-normal`. Negative tracking is banned on display type: wood type is set from fixed sorts and cannot be tracked tight, and `tracking-tighter` was the single most "web" thing on the old page. Section headings set 700 at zero tracking. Mono labels keep their wide `0.12em` tracking in sentence case, because they are the modern finding-aid layer and should not pretend to be letterpress.

**Where the display face may and may not go.** Display headings, section headings, card titles, statistic numerals, the drop cap, and the loading mark. Not running prose, not captions, not filter labels, not citations, not quoted text. Running copy is DM Sans; labels and citations are system mono. A publication's own words — a mission statement, a masthead motto — set in DM Sans and may stay italic, because they are quotation, not decoration.

**Letterpress impression.** `.type-impression` survives the face change unchanged — it is a text-shadow, not a font axis, so it works on any display face. Display type gets a debossed edge. Light type pressed into cloth throws a hairline shadow below and a hairline light above; on dark grounds that is two shadows, one dark and one warm.

```css
.type-impression {
  text-shadow:
    0 1px 0 rgba(11, 8, 6, 0.55),
    0 -1px 0 rgba(168, 145, 121, 0.06);
}
```

**The accessibility caveat, and it is a hard rule.** `text-shadow` softens glyph edges and lowers effective contrast at small sizes, and WCAG measures the text color rather than the rendered edge, so an audit will not catch the damage. Apply `.type-impression` only at 32px and above, only at weight 700 or higher, and never on body copy, mono labels, citations, captions, or link text. Drop it entirely under `prefers-contrast: more` and `forced-colors: active`, in the same block as the texture opt-outs. If a heading needs the impression to look like a heading, the heading is too small.

### 5. What not to do

Six failure modes. Each one is a way this brief turns into a craft-store banner.

Do not load a woodgrain image, a paper-fiber JPEG, a burlap tile, or any raster texture. Everything here is gradients for a reason: an image texture ends up either tiling visibly or weighing more than the data files.

Do not skeuomorph. No stitching around card perimeters, no torn-paper edges, no page-curl corners, no drop shadows pretending cards are objects lying on a desk, no bevels, no fake screws or brass fittings on the rails.

Do not sepia-tone, warm-filter, tint, or vignette the archival images. Ever. These are the primary sources. A reader must be able to trust that what they see is what the scan holds. The furniture is warm; the evidence stays neutral. This is the line that separates a finding aid from a nostalgia object.

Do not lower contrast for mood. Warm and dim are not the same thing. Every ratio in section 1 is a floor, not a target, and no pull request may soften a text color toward its ground to make a screen look older. Mood comes from hue and texture, never from removing contrast.

Do not let the accent turn decorative because it is now quieter. `stain` still means one of three things: rights status, a link, or a timeline anchor. A softer accent invites sprinkling it on headings and borders for warmth. Use `oak` for warmth.

Do not add a second display face, a script face, a blackletter masthead, or a "vintage" overlay on the hero. The 1880s masthead impulse is real and it is wrong. These papers used blackletter because it was the convention of their moment; reproducing it now reads as costume, not as history.

### 6. Implementation order

Four passes, in this order. Each pass ships on its own. Do not start a pass before the previous one merges — the point of the token aliasing is that the site stays correct in between.

**Pass 1 — tokens.** Add `walnut`, `oak`, `linen`, `thread`, and `stain` to the Tailwind inline config on every page, and keep `ink`, `paper`, and `accent` defined at their old values. Nothing changes visually. Then repoint the aliases: `ink-900` to `#14100b`, `paper-100` to `#f3eee2`, `accent` to `#e2662b`, and so on down the map in section 1. The whole site shifts warm in one commit with no markup edits. Re-run the contrast table, then confirm the four accessibility gates still pass.

**Pass 2 — shared surfaces.** Add `.surface-woven`, `.surface-cloth`, `.rail-wood`, `.link-thread`, the stitched divider, and the opt-out media block to `docs/css/styles.css`. Apply `.surface-woven` to `body`. Retune the grain overlay to 0.07 soft-light at `baseFrequency` 0.9. Replace every `border-white/10` with the `walnut-600` hairline. Update the scrollbar thumb, the `::selection` color, and the `.timeline-bar:hover` glow to the stain ramp. This is the pass where the site starts to feel different, and it touches one file.

**Pass 3 — components.** In order of blast radius: buttons and filters, then the timeline bars and axis rail, then the evidence card and its three variants, then the per-title spine. Ship the `metadata_only` shelf-label card as its own commit and review it against real data before going further. 107 of 182 evidence entries render through it, so it is the highest-leverage screen in the redesign.

**Pass 4 — pages and type.** Point the Google Fonts request at the chosen display face, then apply the weight and tracking moves per heading tier and re-check the two-line hero rule. Apply `.type-impression` to display headings only. Finish with the story page's long-read treatment, which needs everything else in place before anyone can judge it.

After each pass, post the plain-English update on discussion #47.

## Global prohibitions: AI design tells

Addendum. Date: 2026-08-19. Full list and rationale: `data/research/design/AI_SLOP_PROHIBITIONS.md`. These are hard rules for every page in this project and for Woven, not suggestions to weigh against other priorities.

No eyebrow text (a small all-caps kicker line floating above a heading). No italics in hero or display titles. No status pills or badges — status is plain text inside the sentence that already carries it, such as the lifespan line. No serif anywhere — no serif display face, no serif body; the only permitted serif use is quoted archival material, if it is ever needed at all. DM Sans carries all running copy and all quotation. No purple or indigo, no gradient fills or gradient text, no glassmorphism, no emoji as icons or bullets, no uniform rounded-2xl-plus-shadow cards, no centered-hero-plus-pill-CTA formula, no three/four-feature-card marketing rows, no decorative icon spam, no hype microcopy, no glowing neon accents, no bento grids, no floating blobs, no fake testimonials, no cursor-following effects, no unstyled Tailwind/shadcn defaults.

Mono, uppercase, tracking-wide labels stay where they are load-bearing metadata inside the component they describe — a filter group, a provenance line, a rights label — never as a preamble line floating above a heading for atmosphere.

## Intuitive UI checklist (added 2026-08-19, per Joe)

Source references from Joe: uxdesigninstitute.com "How to design intuitive user interfaces" and interfacecraft.dev (paid library, principles to be folded in if access is obtained). These are working rules for every page and for Woven.

Consistency: identical visual treatment for the same element type on every page — one nav, one card grammar, one label style — so a reader's first page teaches the rest.
Simplicity: cut elements before shrinking them; every control on screen must earn its place against reader cognitive load.
Common standards: never reinvent a known interaction (search, filters, close, back). The reader's habits are part of the interface.
Feedback: every action gets a visible response — active filter chips, result counts, focus states, aria-live announcements.
Discoverability: primary functions (search, navigation) live in the fixed chrome on every page, never buried down-page.
Affordances: controls look like what they do; hit areas at least 44px on touch surfaces.
Forgiveness: every filter and state is removable in one action; deep links preserve state so nothing is lost by navigating.
Accessibility as a standard, not a mode: non-color cues, screen-reader names on all controls, reduced-motion respected, keyboard-complete.

Applied in the 2026-08-19 usability pass: nav search (discoverability), filter chips (feedback + forgiveness), "Ceased" over "Archived" (common standards), labeled filters and aria-names (accessibility), 44px event buttons on phones (affordances).

## Execution cheat sheet (added 2026-08-19, per Joe, from interfaces.dev/cheat-sheet)

Typography: woff2 only. tabular-nums on any number that changes (stat counters, results counts). 60–75ch measure on long-form text. text-wrap: balance on headings, pretty on paragraphs. Store copy in natural case, present with text-transform. Curly quotes, en dash for ranges, em dash for asides. Keep truncated text reachable (tooltip or expansion).
Color: semantic tokens only (--color-text-secondary), never primitive names in components. Accent = brand only. Dark palette is designed, not inverted. Measure contrast against the actual rendered background.
Accessibility: native button/a elements. :focus-visible styled, never bare outline:none. aria-label on every icon button. Alt text by purpose, decorative images alt="". Real labels + type + inputmode on inputs. Never block paste. Hit areas 44px touch / 40px desktop, non-overlapping. Hover styling behind @media (hover: hover). Motion inside @media (prefers-reduced-motion: no-preference). role="status" for routine updates, role="alert" for errors. Status never by color alone. Skip link first focusable; scroll-margin-top on anchored headings.
Animation: never transition: all. Pressed buttons scale 0.95–0.98, ~200ms ease-out. Transitions for interruptible actions, keyframes for one-shots. Disable transitions during theme swaps. No animating high-frequency hovers in lists.
Layout: gap between groups at least twice the gap within (8px in, 16px+ between). Logical properties (margin-inline) over left/right. No fixed dimensions on text containers.
Writing: verb-first button labels ("Save draft"). Confirmation buttons repeat the consequence. Link text names the destination, never "click here". Sentence case. Empty states orient and offer one next action. Address the reader as "you".
