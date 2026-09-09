# AGENTS.md — Guitar Poster (interactive chart)

## What this is

`index.html` — a single self-contained interactive rebuild of a printed guitar
reference poster (moveable chords, basic chords, chord formulas, circle of
fifths, key chord tables, fretboard with scale tabs). HTML + CSS + vanilla
JS + SVG, **no build step, no dependencies**. All UI text and code comments
are in English. Visual language: vintage printed chart — paper/ink color
pair via CSS variables, thin rules, dense tables, dark header bars, no
cards/gradients. **Dark theme is the default** (`body.dark`, warm
near-black paper + cream ink); `state.theme` persists it, the THEME
seg (DARK | LIGHT) lives in the bottom dock. All colors must go through
the variables in `:root` (light) / `body.dark` (dark) — incl. `--auxdim`,
`--paperhi`, `--hov`, `--barhov`, `--shadow`; SVG text inherits
`svg text{fill:var(--ink)}`.

## Core principle

**One music model, many synced views.** Everything renders from the
`<script id="music-model">` block (pure data + pure functions, no DOM):
`CHORDS`, `SHAPES` (moveable, frets relative to the root fret on the root
string), `BASIC` (open chords, absolute frets), `SCALES`, `CIRCLE`, key
tables. Nothing musical is hardcoded in renderers. Shapes are verified
numerically (`verifyShapes()`: played notes ⊆ chord pitch classes, root on
the root string) — do not hand-draw diagrams.

## Architecture cheat sheet

- Two `<script>` blocks: `#music-model` (pure, testable) and the app
  (state + render). Model is exposed as `window.__MODEL`, app as `window.__APP`.
- App state (persisted in `localStorage` key `guitar-poster-v1`):
  `keyPc`, `keyMode`, `root` (moveable transposition), `display`
  (`deg|note|int`, **degrees-first by design**), `sel {root,type}`,
  `scale`, `center` (local center — **visual marker only**, ring + chip),
  `cofMode`, `filter`, `fretView` (`scale|notes`), `fretOpen` (dock state),
  `theme` (`dark|light`, **dark by default**).
- `renderAll()` re-renders every section from state; hover never re-renders
  (cross-highlight is done by toggling `.xhl` on cached `[data-pc]` elements).
- Bottom dock (`.dock-wrap`, `position:sticky; bottom:0`): the fretboard
  panel (collapsible via `#fretToggle`, persisted as `fretOpen`) plus the
  global controls (SHOW / KEY / LOCAL CENTER / THEME) — always visible while
  scrolling. The fretboard bar has a view tab `SCALE | NOTES` (NOTES = the
  old all-notes neck, lives in the same `#fretSvg`); scale tabs + formula +
  filter are hidden in NOTES view. Scale tabs all keep their right border
  (`margin-right:-1px` collapse) so the border shows before the extra-group
  gap after LOCRAN.
- Degrees display rules: chord tones read against the chord root (with
  per-chord overrides for ♯5/♭5/♭♭7 via `CHORDS[t].ovr`), scale tones against
  the key tonic (per-scale maps `SCALE_LABELS[scaleId]`, e.g. ♯4 in Lydian).
  The label follows the mark's resolved filter kind (in SCALE view a note
  that is also a chord tone still reads as a scale degree). The local center
  never rewrites labels — marking only.
- Moveable diagrams: `SHAPES[t][col].f` = relative frets `[s6..s1]`, -1 =
  muted; `barre:[fromStr,toStr,rel]`. Base fret = `rootFret(pc, rootString)`.
- Diagram grids are compact: the top line sits right above the highest played
  fret (`firstRow = min(used frets)`, capped at rel 0) and there are always
  **4 rows minimum** (5 only when the shape really spans 5 frets).
- Fretboard section hosts the scales: 10 tabs under the bar (7 modes of major
  + Harmonic Minor / Gypsy / Acoustic), the scale formula sits in the black
  bar (`#fretScaleHdr`). `selectKey` keeps the plain scale of the mode
  (ionian ↔ aeolian) but never stomps an exotic choice. The panel itself
  lives in the bottom dock.
- Circle of fifths: three clickable rings — outer = major chord, middle =
  its relative minor, inner = its vii° diminished (click selects the chord);
  hub = selected key. All three rings follow the label mode
  `names (C / Am / B°) | romans | functions` relative to the selected key.
  **The wheel highlights one thing at a time**: a selected dim chord
  suppresses the key-ring highlight, and `selectKey` clears a dim selection
  (it becomes the tonic triad). Selected ring labels get their contrast via
  inline `style.fill` (presentation attributes would lose to CSS rules).
- Chord shape note math: `pc = (TUNING[i] + base + rel) % 12`,
  `base = (rootPc - TUNING[6-rootStr]) mod 12`.
- Horizontal necks (fretboard, notes view) draw **string 1 on top**, string 6
  at the bottom (tab/poster convention): row = `strY0 + (5 - i) * strGap` for
  string index i (0 = low E). Vertical chord diagrams keep string 6 on the
  left.

## Verifying changes

1. Syntax-check both inline scripts:

   ```bash
   python3 -c "import re;src=open('index.html').read();\
   ss=re.findall(r'<script[^>]*>\n(.*?)\n</script>',src,re.S);\
   [open(f'/tmp/opencode/s{i}.js','w').write(s) for i,s in enumerate(ss)]" \
   && node --check /tmp/opencode/s0.js && node --check /tmp/opencode/s1.js
   ```

2. Smoke tests + screenshots (self-contained):

   ```bash
   tests/run_tests.sh
   ```

   - `tests/inject_tests.py` generates `tmp/index-test.html` (69 assertions,
     PASS/FAIL panel top-left; the test script **resets persisted state**
     before asserting) and `tmp/index-scenario.html` (C major → V → G7 →
     local center on ♭7) from `index.html` into `tmp/` (gitignored).
   - Then headless Firefox captures `tmp/gp-test.png`, `tmp/gp-scenario.png`,
     `tmp/gp-default.png`.
   - **Read `tmp/gp-test.png` and check every line is PASS.**
     `document.title` also becomes `TESTS n/m`.

### Firefox on this machine is a SNAP

- The `--profile <dir>` directory must **already exist** (hence `mkdir -p`).
- Input/output paths must be **absolute and under `$HOME`** — the project dir
  works; `/tmp` does **not** (snap-private tmp namespace).
- Use `--no-remote --headless --window-size=WxH --screenshot OUT file://...`.
- For deterministic screenshots the test pages freeze CSS transitions
  (`*{transition:none!important}`) and finish animations
  (`document.getAnimations().forEach(a => a.finish())`).

## Conventions

- `tmp/` is gitignored: scratch pages, screenshots, extracted scripts.
- Reusable test code lives in `tests/`.
- Do not commit unless explicitly asked.
- Keyboard: ←/→ change key, D/N/I switch degrees/notes/intervals, 1–7 select
  the diatonic chord of the current key, Esc clears the local center.
