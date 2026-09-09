# AGENTS.md — Guitar Poster (interactive chart)

## What this is

`index.html` — a single self-contained interactive rebuild of a printed guitar
reference poster (moveable chords, basic chords, chord formulas, circle of
fifths, key chord tables, fretboard, scales). HTML + CSS + vanilla JS + SVG,
**no build step, no dependencies**. All UI text and code comments are in
English. Visual language: vintage printed chart — off-white paper (`--paper`),
thin black rules, dense tables, black header bars, no cards/gradients.

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
  `scale`, `center` (local harmonic center), `cofMode`, `filter`.
- `renderAll()` re-renders every section from state; hover never re-renders
  (cross-highlight is done by toggling `.xhl` on cached `[data-pc]` elements).
- Degrees display rules: chord tones read against the chord root (with
  per-chord overrides for ♯5/♭5/♭♭7 via `CHORDS[t].ovr`), scale tones against
  the key tonic (per-scale maps `SCALE_LABELS[scaleId]`, e.g. ♯4 in Lydian),
  local center overrides both.
- Moveable diagrams: `SHAPES[t][col].f` = relative frets `[s6..s1]`, -1 =
  muted; `barre:[fromStr,toStr,rel]`. Base fret = `rootFret(pc, rootString)`.
- Circle of fifths: annulus paths, outer = major keys, middle = relative
  minors, innermost text = vii° of each major key; ring label mode
  `names | romans | functions` relative to the selected key.
- Chord shape note math: `pc = (TUNING[i] + base + rel) % 12`,
  `base = (rootPc - TUNING[6-rootStr]) mod 12`.

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

   - `tests/inject_tests.py` generates `tmp/index-test.html` (assertions,
     PASS/FAIL panel top-left) and `tmp/index-scenario.html` (a musical
     scenario) from `index.html` into `tmp/` (gitignored).
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
