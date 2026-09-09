#!/usr/bin/env python3
"""
Generates headless test pages from ../index.html into ../tmp/ (gitignored).

Outputs:
  tmp/index-test.html      - copy of index.html + smoke-test script (PASS/FAIL panel top-left)
  tmp/index-scenario.html  - copy of index.html + scenario script (C major -> V -> G7 -> local center)

Run tests/run_tests.sh afterwards to capture headless-Firefox screenshots.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
DST_DIR = os.path.join(ROOT, 'tmp')
os.makedirs(DST_DIR, exist_ok=True)

TEST_JS = r"""
(function(){
  document.head.insertAdjacentHTML('beforeend', '<style>*{transition:none!important}#testres{position:fixed;top:8px;left:8px;z-index:999;background:#f4f1e8;border:1px solid #191712;padding:8px 12px;font:11px monospace;color:#191712;max-width:64ch;white-space:pre-wrap}</style>');
  const out = [];
  const ok = (name, cond) => out.push((cond ? 'PASS ' : 'FAIL ') + name);
  try {
    // ---------- clean slate (ignore persisted state from previous runs) ----------
    localStorage.removeItem('guitar-poster-v1');
    const S = window.__APP.state;
    Object.assign(S, { keyPc:0, keyMode:'major', root:0, display:'deg',
      sel:{ root:0, type:'maj' }, scale:'ionian', center:null, cofMode:'names', filter:'both' });
    window.__APP.setTheme('dark');
    window.__APP.renderAll();

    // ---------- model ----------
    const errs = window.__MODEL.verifyShapes();
    ok('verifyShapes clean (' + (errs.length ? errs[0] : 'none') + ')', errs.length === 0);
    ok('rootFret C on s6 = 8', window.__MODEL.rootFret(0, 6) === 8);
    ok('rootFret A on s5 = 0', window.__MODEL.rootFret(9, 5) === 0);
    const maj = window.__MODEL.shapeNotes('maj', 'r6', 0);   // E shape at C
    ok('shapeNotes C maj r6', !!maj && maj.notes.some(n => n.str === 6 && n.fret === 8 && n.semi === 0));
    const g7 = window.__MODEL.shapeNotes('7', 'r5', 7);      // A shape at G7
    ok('G7 r5 has b7', !!g7 && g7.notes.some(n => n.semi === 10));
    ok('23 movable types', window.__MODEL.MOVABLE_ORDER.length === 23);

    // ---------- header controls ----------
    const dispBtns = [...document.querySelectorAll('#displayRow button')];
    ok('display buttons exact', JSON.stringify(dispBtns.map(b => b.textContent)) === JSON.stringify(['DEGREES','NOTES','INTERVALS']));
    ok('degrees mode default', window.__APP.state.display === 'deg');
    ok('12 key chips', document.querySelectorAll('#keyRow button').length === 12);

    // ---------- movable table ----------
    ok('23 movable rows', document.querySelectorAll('#movBody tr').length === 23);
    ok('69 movable diagrams', document.querySelectorAll('#movBody svg').length === 69);
    // no separate root chips: transposition follows the selected chord.
    // Pick F maj (basic chord, 6th letter column) -> the first movable
    // diagram (maj r6) must become F major barre at fret 1
    document.querySelector('#basicBody tr:first-child td:nth-child(7)').click();  // F maj
    const firstDots = [...document.querySelectorAll('#movBody tr:first-child td:nth-child(2) .cdot')];
    const pcs = [...new Set(firstDots.map(g => +g.dataset.pc))].sort((a, b) => a - b);
    ok('F maj r6 pcs = F A C', JSON.stringify(pcs) === JSON.stringify([0, 5, 9]));
    const barreF = document.querySelector('#movBody tr:first-child rect.barre');
    ok('F maj r6 barre at fret 1', !!barreF && barreF.getAttribute('y') !== null);
    ok('movRootLabel F', document.getElementById('movRootLabel').textContent.indexOf('F') !== -1);
    // root digit must contrast with its dot (inline style beats the svg text CSS rule)
    const rootDot = document.querySelector('#movBody .cdot[data-pc="5"]');
    ok('root digit contrasts with dot',
      getComputedStyle(rootDot.querySelector('text')).fill !==
      getComputedStyle(rootDot.querySelector('circle')).fill);

    // ---------- compact diagrams ----------
    const svgH = s => [...document.querySelectorAll(s)].map(x => x.viewBox.baseVal.height);
    ok('no 6-row diagrams left', Math.max(...svgH('#movBody svg'), ...svgH('#basicBody svg')) <= 24 + 5*23 + 8);
    ok('diagrams uniform: 4 rows base',
      Math.min(...svgH('#movBody svg'), ...svgH('#basicBody svg')) === 24 + 4*23 + 8);

    // ---------- basic chords ----------
    ok('35 basic diagrams', document.querySelectorAll('#basicBody svg').length === 35);
    const cPcs = [...new Set([...document.querySelectorAll('#basicBody tr:first-child td:nth-child(4) .cdot')]
      .map(g => +g.dataset.pc))].sort((a, b) => a - b);
    ok('basic C maj pcs', JSON.stringify(cPcs) === JSON.stringify([0, 4, 7]));
    // click a basic diagram -> selects that chord everywhere
    document.querySelector('#basicBody tr:first-child td:nth-child(2)').click();  // A maj
    ok('basic click selects A maj', S.sel.root === 9 && S.sel.type === 'maj');
    ok('formula follows sel', (document.querySelector('#formulaBody tr.on') || {dataset:{}}).dataset.ftype === 'maj');
    // back to C major for the rest of the run — the key chip alone must
    // also resolve the chord selection to the tonic triad
    [...document.querySelectorAll('#keyRow button')].find(b => b.textContent === 'C').click();
    ok('key chip resolves tonic chord', S.sel.root === 0 && S.sel.type === 'maj');

    // ---------- formula ----------
    ok('25 formula rows', document.querySelectorAll('#formulaBody tr').length === 25);
    ok('formula row maj', document.querySelector('#formulaBody tr[data-ftype="maj"] .fform').textContent === '1 3 5');
    ok('formula row dom7', document.querySelector('#formulaBody tr[data-ftype="7"] .fform').textContent === '1 3 5 \u266d7');
    ok('formula notes of C maj', document.querySelector('#formulaBody tr[data-ftype="maj"] .fnotes').textContent.trim() === 'C E G');

    // ---------- circle of fifths ----------
    ok('36 cof segments (3 rings)', document.querySelectorAll('#cofSvg .cof-seg').length === 36);
    // click G on the outer ring
    const gSeg = [...document.querySelectorAll('#cofSvg .cof-seg')]
      .find(p => p.dataset.pc === '7' && !p.classList.contains('min') && !p.classList.contains('dimg'));
    ok('cof G seg exists', !!gSeg);
    gSeg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    ok('key = G after cof click', window.__APP.state.keyPc === 7);
    // a wheel ring sets the key AND its tonic chord, so the fretboard
    // chord mode / movable root always follow
    ok('cof ring click resolves tonic triad', S.sel.root === 7 && S.sel.type === 'maj');
    ok('movable table follows wheel chord',
      document.getElementById('movRootLabel').textContent.indexOf('G') !== -1);
    ok('cof center label G', [...document.querySelectorAll('#cofSvg .cof-center-big')].some(t => t.textContent === 'G'));
    // names mode labels every ring as a chord
    ok('names mode labels chords (Em)', [...document.querySelectorAll('#cofSvg text')].some(t => t.textContent === 'Em'));
    // romans mode must reach all three rings
    [...document.querySelectorAll('#cofModeRow button')].find(b => b.textContent === 'ROMANS').click();
    const cofTexts = [...document.querySelectorAll('#cofSvg text')].map(t => t.textContent);
    ok('romans on all rings', cofTexts.includes('I') && cofTexts.includes('vi') && cofTexts.includes('vii\u00b0'));
    [...document.querySelectorAll('#cofModeRow button')].find(b => b.textContent === 'NAMES').click();
    // inner ring: clicking the diminished chord selects it
    const dimSeg = [...document.querySelectorAll('#cofSvg .cof-seg.dimg')].find(p => p.dataset.pc === '11');
    dimSeg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    ok('dim ring selects B\u00b0', S.sel.root === 11 && S.sel.type === 'dim');
    // wheel shows one selection: dim suppresses the key rings ...
    ok('dim sel suppresses key rings',
      !document.querySelector('#cofSvg .cof-seg.on:not(.dimg)') &&
      !!document.querySelector('#cofSvg .cof-seg.dimg.on'));
    // ... and the dim label stays readable on the dark wedge
    // (inline style.fill must beat the .cof-dim2 CSS rule)
    const dimLbls = [...document.querySelectorAll('#cofSvg .cof-dim2')];
    const selLbl = dimLbls.find(t => t.style.fill.indexOf('selfg') !== -1);
    ok('selected dim label has inline fill', !!selLbl);
    ok('selected dim label readable',
      !!selLbl && getComputedStyle(selLbl).fill !==
      getComputedStyle(dimLbls.find(t => t !== selLbl)).fill);
    // picking a key clears the dim selection (becomes the tonic triad)
    const cMaj = [...document.querySelectorAll('#cofSvg .cof-seg')]
      .find(p => p.dataset.pc === '0' && !p.classList.contains('min') && !p.classList.contains('dimg'));
    cMaj.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    ok('major sel clears dim', S.sel.root === 0 && S.sel.type === 'maj' &&
      !document.querySelector('#cofSvg .cof-seg.dimg.on'));
    ok('major ring highlighted', !!document.querySelector('#cofSvg .cof-seg.on:not(.dimg)'));

    // ---------- key chord tables sync (C major, press V) ----------
    [...document.querySelectorAll('#keyRow button')].find(b => b.textContent === 'C').click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: '5', bubbles: true }));
    ok('key 5 selects G7', window.__APP.state.sel.root === 7 && window.__APP.state.sel.type === '7');
    ok('formula now dom7', document.querySelector('#formulaBody tr.on').dataset.ftype === '7');
    // fretboard: chord tone marks exist for G7
    ok('fretboard chordt marks', document.querySelectorAll('#fretSvg .g-mark.chordt').length >= 8);
    // string 1 must be on top: labels read E B G D A E from top to bottom
    const slbls = [...document.querySelectorAll('#fretSvg .g-slbl')]
      .sort((a, b) => a.getAttribute('y') - b.getAttribute('y'))
      .map(t => t.textContent);
    ok('string 1 on top (E B G D A E)', JSON.stringify(slbls) === JSON.stringify(['E','B','G','D','A','E']));
    // degree labels read against the chord root G
    const chordB7 = [...document.querySelectorAll('#fretSvg .g-mark.chordt text')].find(t => t.textContent === '\u266d7');
    ok('fretboard shows b7 on chord tone', !!chordB7);

    // ---------- local center ----------
    window.__APP.toggleCenter(7);   // center on G = V of C major
    ok('center chip G = V', document.getElementById('centerChip').textContent.indexOf('V') !== -1);
    window.__APP.toggleCenter(5);   // center on F = IV of C major
    ok('center chip F = IV', document.getElementById('centerChip').textContent.indexOf('IV') !== -1);
    // the center must stay visible in every filter: in CHORD mode a
    // non-chord-tone center appears as a plain dotted mark with the ring
    window.__APP.toggleCenter(9);   // A: scale tone, not a G7 chord tone
    [...document.querySelectorAll('#fretFilterRow button')].find(b => b.textContent === 'CHORD').click();
    ok('center visible in chord filter',
      [...document.querySelectorAll('#fretSvg .g-mark.plain')].some(g => g.querySelector('.cring')));
    [...document.querySelectorAll('#fretFilterRow button')].find(b => b.textContent === 'BOTH').click();
    // the center is a marker only: scale tones must keep their scale degrees
    // (C stays 1, A stays 6 — the old center override mislabelled them 7 and 4)
    const scaleTexts = [...document.querySelectorAll('#fretSvg .g-mark.scale text')].map(t => t.textContent);
    ok('center does not corrupt scale labels', scaleTexts.includes('1') && scaleTexts.includes('6'));
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    ok('esc clears center', S.center === null);

    // ---------- display modes ----------
    dispBtns.find(b => b.textContent === 'NOTES').click();
    ok('notes mode on fretboard', [...document.querySelectorAll('#fretSvg .g-mark text')].every(t => /^[A-G\u266d]$/.test(t.textContent)));
    dispBtns.find(b => b.textContent === 'INTERVALS').click();
    ok('intervals mode on fretboard', [...document.querySelectorAll('#fretSvg .g-mark text')].some(t => t.textContent === 'P5'));
    dispBtns.find(b => b.textContent === 'DEGREES').click();

    // ---------- sticky dock: fretboard + controls ----------
    ok('key + center docked, show/theme in header',
      document.querySelectorAll('.dock-controls .ctrl-block').length === 2 &&
      !!document.querySelector('header.top #displayRow') &&
      !!document.querySelector('header.top #themeRow') &&
      !document.querySelector('#dockWrap #displayRow'));
    ok('settings spoiler closed by default', S.settingsOpen === false &&
      !document.getElementById('hdrSet').classList.contains('open'));
    document.getElementById('settingsToggle').click();
    ok('settings spoiler opens', S.settingsOpen === true &&
      document.getElementById('hdrSet').classList.contains('open'));
    document.getElementById('settingsToggle').click();
    ok('settings spoiler closes again', S.settingsOpen === false &&
      !document.getElementById('hdrSet').classList.contains('open'));
    document.getElementById('fretToggle').click();
    ok('fretboard collapses', document.getElementById('fretSec').classList.contains('closed') && S.fretOpen === false);
    document.getElementById('fretToggle').click();
    ok('fretboard expands again', !document.getElementById('fretSec').classList.contains('closed') && S.fretOpen === true);
    // NOTES view lives on a fretboard tab now
    [...document.querySelectorAll('#fretViewRow button')].find(b => b.textContent === 'NOTES').click();
    ok('notes view on fretboard tab', S.fretView === 'notes' &&
      document.querySelectorAll('#fretSvg .g-mark').length >= 60);
    ok('notes view hides scale tabs', document.getElementById('scaleTabs').hidden === true);
    [...document.querySelectorAll('#fretViewRow button')].find(b => b.textContent === 'SCALE').click();
    ok('back to scale view', S.fretView === 'scale' && document.getElementById('scaleTabs').hidden === false);
    // every scale tab keeps its right border (before the extra-group gap too)
    const tabBtns = [...document.querySelectorAll('#scaleTabs button')];
    ok('right border on every scale tab (LOCRAN too)',
      tabBtns.every(b => parseFloat(getComputedStyle(b).borderRightWidth) === 1));

    // ---------- theme (dark by default) ----------
    ok('theme seg buttons', JSON.stringify([...document.querySelectorAll('#themeRow button')].map(b => b.textContent)) === JSON.stringify(['DARK','LIGHT']));
    ok('dark theme on after reset', document.body.classList.contains('dark') && S.theme === 'dark');
    ok('dark palette active', getComputedStyle(document.body).getPropertyValue('--selbg').trim() === '#d6cfbc');
    [...document.querySelectorAll('#themeRow button')].find(b => b.textContent === 'LIGHT').click();
    ok('light theme toggle', !document.body.classList.contains('dark') && S.theme === 'light');
    ok('light palette active', getComputedStyle(document.body).getPropertyValue('--selbg').trim() === '#191712');
    ok('light theme persisted', JSON.parse(localStorage.getItem('guitar-poster-v1')).theme === 'light');
    [...document.querySelectorAll('#themeRow button')].find(b => b.textContent === 'DARK').click();
    ok('back to dark', document.body.classList.contains('dark') && S.theme === 'dark');

    // ---------- tonnetz (degree lattice) ----------
    ok('tonnetz 37 nodes', document.querySelectorAll('#tzSvg .tz-node').length === 37);
    const tzPanel = document.getElementById('tzSvg').closest('section');
    const kcPanel = document.getElementById('keyChordsAux').closest('section');
    ok('tonnetz sits above key chords',
      !!(tzPanel.compareDocumentPosition(kcPanel) & Node.DOCUMENT_POSITION_FOLLOWING));
    const tzTonic = document.querySelector('#tzSvg .tz-node[data-pc="0"]');
    ok('tonnetz tonic label 1', !!tzTonic && tzTonic.querySelector('text').textContent === '1');
    // G7 is still selected: its pcs appear in degree space {7,11,2,5} (key C)
    const tzChordPcs = [...new Set([...document.querySelectorAll('#tzSvg .tz-node.tz-chord')]
      .map(g => +g.dataset.pc))].sort((a, b) => a - b);
    ok('tonnetz highlights G7 pcs', JSON.stringify(tzChordPcs) === JSON.stringify([2, 5, 7, 11]));
    ok('no voice badges on tonnetz',
      !document.querySelector('#tzSvg .tz-badge') &&
      document.querySelectorAll('#tzSvg .tz-bass').length === 1);
    ok('tonnetz overlay only for plain triads',
      document.querySelector('#tzSvg .tz-tri').style.display === 'none');
    window.__APP.selectChord(7, 'maj');
    ok('tonnetz triangle for maj', document.querySelector('#tzSvg .tz-tri').style.display !== 'none');
    window.__APP.tzClick(46, -79.674 / 3);   // interior of the tonic major triangle
    ok('tzClick selects I major', S.sel.root === 0 && S.sel.type === 'maj');
    // reverse sync: a non-tonic triangle click lights up its wheel ring
    window.__APP.tzClick(138, -79.674 / 3);  // G major triangle; the key stays C
    ok('tzClick selects non-tonic triad', S.sel.root === 7 && S.sel.type === 'maj' && S.keyPc === 0);
    const wheelOn = [...document.querySelectorAll('#cofSvg .cof-seg.on')];
    ok('tonnetz triangle highlights wheel', wheelOn.length === 1 &&
      wheelOn[0].dataset.pc === '7' && !wheelOn[0].classList.contains('dimg'));
    document.querySelector('#tzSvg .tz-node[data-pc="7"]')
      .dispatchEvent(new MouseEvent('click', { bubbles: true }));
    ok('tonnetz vertex click sets center', S.center === 7);
    ok('tonnetz center ring visible',
      [...document.querySelectorAll('#tzSvg .tz-cring')].some(c => c.style.display !== 'none'));
    dispBtns.find(b => b.textContent === 'NOTES').click();
    ok('tonnetz note labels', tzTonic.querySelector('text').textContent === 'C');
    dispBtns.find(b => b.textContent === 'INTERVALS').click();
    ok('tonnetz interval labels', [...document.querySelectorAll('#tzSvg .tz-node text')]
      .some(t => t.textContent === 'P5'));
    dispBtns.find(b => b.textContent === 'DEGREES').click();
    // ---------- local center: every occurrence rings + relative labels ----------
    ok('inversion seg removed from tonnetz', !document.getElementById('tzInvRow'));
    ok('header has no inversion suffix',
      document.getElementById('tzHdr').textContent.indexOf('inv') === -1);
    const ctrAbs = document.querySelectorAll('#tzSvg .tz-node[data-pc="7"]').length;
    const ctrRings = [...document.querySelectorAll('#tzSvg .tz-cring')]
      .filter(c => c.style.display !== 'none').length;
    ok('center ring on every lattice occurrence', ctrAbs >= 2 && ctrRings === ctrAbs);
    const allN = document.querySelectorAll('#tzSvg .tz-node').length;
    const rels = [...document.querySelectorAll('#tzSvg .tz-node text.rel')]
      .filter(t => t.style.display !== 'none');
    ok('relative labels on all non-center nodes', rels.length === allN - ctrAbs);
    ok('relative label reads the degree (C is the 4th of G)',
      rels.some(t => t.textContent === '4'));
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    ok('escape clears center', S.center === null &&
      [...document.querySelectorAll('#tzSvg .tz-cring')].every(c => c.style.display === 'none'));

    // ---------- fretboard center keeps its degree label ----------
    S.filter = 'both'; S.fretView = 'scale';
    S.center = 1;                     // not in C major / Cmaj: plain fallback mark
    window.__APP.renderAll();
    const ctrMark = document.querySelector('#fretSvg .g-mark[data-pc="1"]');
    ok('fretboard center shows its degree label', !!ctrMark &&
      !!ctrMark.querySelector('text') && !!ctrMark.querySelector('.cring'));
    S.center = null; window.__APP.renderAll();

    // ---------- rhythm cards (reference) + generator ----------
    ok('16 sixteenth cards', document.querySelectorAll('#rGrid16 .rpatt').length === 16);
    ok('8 triplet cards', document.querySelectorAll('#rGridT .rpatt').length === 8);
    ok('rhythm lives in the right column', !!document.querySelector('.col-right #rhythmSec'));
    const outEmpty = document.getElementById('rhythmOut').innerHTML;
    document.querySelectorAll('#rGridT .rpatt')[0].click();
    ok('cards are reference only (no click generation)',
      document.getElementById('rhythmOut').innerHTML === outEmpty);
    [...document.querySelectorAll('#rhythmGenRow button')].find(b => b.textContent === '16TH').click();
    ok('generator deals two 4-slot bars',
      document.querySelectorAll('#rhythmOut .rmeasure').length === 2 &&
      [...document.querySelectorAll('#rhythmOut .rbeat')].every(b => b.querySelectorAll('.rcell').length === 4));
    const rhythmBefore = document.getElementById('rhythmOut').innerHTML;
    [...document.querySelectorAll('#rhythmGenRow button')].find(b => b.textContent.indexOf('NEW') !== -1).click();
    ok('regenerate deals a new rhythm', document.getElementById('rhythmOut').innerHTML !== rhythmBefore);

    // ---------- keyboard: arrows change key ----------
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
    ok('arrowleft key B (pc 11)', S.keyPc === 11);

    // ---------- scale tabs on the fretboard ----------
    const tabs = [...document.querySelectorAll('#scaleTabs button')];
    ok('10 scale tabs', tabs.length === 10);
    // switching key mode keeps the plain scale of the mode (ionian is active)
    [...document.querySelectorAll('#keyModeRow button')].find(b => b.textContent === 'MINOR').click();
    ok('minor mode -> aeolian', S.keyMode === 'minor' && S.scale === 'aeolian');
    [...document.querySelectorAll('#keyModeRow button')].find(b => b.textContent === 'MAJOR').click();
    ok('major mode -> ionian again', S.keyMode === 'major' && S.scale === 'ionian');
    const dTab = tabs.find(b => b.dataset.scale === 'dorian');
    dTab.click();
    ok('dorian tab selected', S.scale === 'dorian' && dTab.classList.contains('on'));
    ok('scale formula in fretboard header',
      document.getElementById('fretScaleHdr').textContent === '1 2 \u266d3 4 5 6 \u266d7');
    // scale-only filter: the b3 of B dorian (D) must be labelled
    [...document.querySelectorAll('#fretFilterRow button')].find(b => b.textContent === 'SCALE').click();
    ok('dorian b3 labels on fretboard',
      [...document.querySelectorAll('#fretSvg .g-mark text')].filter(t => t.textContent === '\u266d3').length >= 2);

    // ---------- persistence ----------
    const saved = JSON.parse(localStorage.getItem('guitar-poster-v1'));
    ok('state persisted', saved && saved.keyPc === 11 && saved.scale === 'dorian');
  } catch (err) {
    out.push('ERROR ' + (err && err.message));
  }
  const pass = out.filter(s => s.startsWith('PASS')).length;
  document.title = 'TESTS ' + pass + '/' + out.length;
  const d = document.createElement('div');
  d.id = 'testres';
  d.textContent = out.join('\n');
  document.body.appendChild(d);
  document.getAnimations().forEach(a => a.finish());
})();
"""

SCEN_JS = r"""
(function(){
  document.head.insertAdjacentHTML('beforeend', '<style>*{transition:none!important}</style>');
  // Scenario: C major -> V -> G7 -> select b7 -> see it everywhere
  document.dispatchEvent(new KeyboardEvent('keydown', { key: '5', bubbles: true }));   // V of C major
  [...document.querySelectorAll('#fretFilterRow button')].find(b => b.textContent === 'ALL').click();
  window.__APP.toggleCenter(5);   // local center on b7 (F)
  document.getAnimations().forEach(a => a.finish());
})();
"""

def inject(path, js):
    html = open(SRC).read()
    assert html.count('</body>') == 1
    html = html.replace('</body>', '<script>' + js + '</script>\n</body>')
    open(path, 'w').write(html)

inject(os.path.join(DST_DIR, 'index-test.html'), TEST_JS)
inject(os.path.join(DST_DIR, 'index-scenario.html'), SCEN_JS)
print('written:', DST_DIR)
