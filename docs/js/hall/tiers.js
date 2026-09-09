// History hall — the two named quality tiers and how the hall chooses between
// them. No Three.js and no layout: this module owns the policy, and the caller
// owns everything the policy changes.
//
// Standard is the full hall. Simplified lowers the device pixel ratio, halves
// the painted face pool, drops the optional fill light, and turns a flat leaf
// instead of a bending one. The hall has no shadows, so shadows are not in this
// ladder.

// The painted face pool is the other thing a tier changes, and its two sizes
// live with the pool itself, in sheets.js, as FACE_POOL_SIZES.
export const TIERS = {
  standard: { pixelRatio: 2, fill: true, bend: true },
  simplified: { pixelRatio: 1.25, fill: false, bend: false }
};

// Frame intervals are judged only while the hall is actually moving; an idle
// hall draws nothing and would otherwise report one enormous interval. A window
// of samples is judged by its median, and the two thresholds are far enough
// apart, over enough windows, that the tier cannot oscillate between them.
export const SAMPLE_WINDOW = 30;
export const SLOW_MS = 20;
export const FAST_MS = 13;
export const WINDOWS_TO_SIMPLIFY = 2;
export const WINDOWS_TO_RESTORE = 4;

/**
 * @param {object} options
 * @param {(settings: object, tier: string) => void} options.apply put the tier
 *   into effect: pixel ratio, pool size, fill light, page bend.
 * @param {HTMLButtonElement} [options.toggle] the visible "Simplified view" control
 * @param {HTMLElement} [options.note] where the current setting is explained
 * @param {(text: string) => void} [options.announce] polite live announcement
 * @param {(target, type, handler) => void} [options.listen] the hall's counted listener
 */
export function createTiers(options) {
  const { apply, toggle = null, note = null } = options;
  const announce = options.announce || (() => {});
  const listen = options.listen || ((target, type, handler) => target.addEventListener(type, handler));

  let tier = 'standard';
  let pinned = null;          // set once the visitor chooses for themselves
  let slowWindows = 0;
  let fastWindows = 0;
  let intervals = [];

  function describe() {
    if (!toggle) return;
    const simplified = tier === 'simplified';
    toggle.setAttribute('aria-pressed', String(simplified));
    if (!note) return;
    const how = pinned ? 'You chose this view.'
      : simplified ? 'Chosen automatically to keep movement smooth.' : 'Full detail.';
    note.textContent = simplified
      ? `Simplified view. Fewer painted sheets and plainer light. ${how}`
      : `Standard view. ${how}`;
  }

  function set(next, { say = true } = {}) {
    tier = next;
    apply(TIERS[next], next);
    describe();
    if (say && !pinned && next === 'simplified') {
      announce('Simplified view, to keep movement smooth. You can choose the standard view in the hall controls.');
    }
  }

  if (toggle) {
    listen(toggle, 'click', () => {
      // Pressing the control pins the choice. Measurement never overrides a
      // visitor who has said what they want.
      pinned = tier === 'simplified' ? 'standard' : 'simplified';
      slowWindows = 0;
      fastWindows = 0;
      intervals = [];
      set(pinned, { say: false });
    });
    describe();
  }

  return {
    get tier() { return tier; },
    get pinned() { return pinned; },
    /** Put the current tier into effect again, after a resize or a view change. */
    reapply() { apply(TIERS[tier], tier); },
    set,
    /**
     * One frame interval measured while something was moving. Idle frames must
     * not be passed in: they are not a measurement of anything.
     */
    sample(ms) {
      if (pinned) return;
      intervals.push(ms);
      if (intervals.length < SAMPLE_WINDOW) return;
      intervals.sort((a, b) => a - b);
      const median = intervals[Math.floor(SAMPLE_WINDOW / 2)];
      intervals = [];
      if (median > SLOW_MS) { slowWindows += 1; fastWindows = 0; } else if (median < FAST_MS) { fastWindows += 1; slowWindows = 0; } else { slowWindows = 0; fastWindows = 0; }
      if (tier === 'standard' && slowWindows >= WINDOWS_TO_SIMPLIFY) {
        slowWindows = 0;
        set('simplified');
      } else if (tier === 'simplified' && fastWindows >= WINDOWS_TO_RESTORE) {
        fastWindows = 0;
        set('standard');
      }
    }
  };
}
