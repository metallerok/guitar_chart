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
    ok('12 root chips', document.querySelectorAll('#rootRow button').length === 12);
    ok('12 key chips', document.querySelectorAll('#keyRow button').length === 12);

    // ---------- movable table ----------
    ok('23 movable rows', document.querySelectorAll('#movBody tr').length === 23);
    ok('69 movable diagrams', document.querySelectorAll('#movBody svg').length === 69);
    // transpose root to F: first movable diagram (maj r6) must become F major barre at fret 1
    [...document.querySelectorAll('#rootRow button')].find(b => b.textContent === 'F').click();
    const firstDots = [...document.querySelectorAll('#movBody tr:first-child td.cell:first-of-type .cdot')];
    const pcs = firstDots.map(g => +g.dataset.pc).sort((a, b) => a - b);
    ok('F maj r6 pcs = F A C', JSON.stringify(pcs) === JSON.stringify([0, 5, 9]));
    const barreF = document.querySelector('#movBody tr:first-child rect.barre');
    ok('F maj r6 barre at fret 1', !!barreF && barreF.getAttribute('y') !== null);
    ok('movRootLabel F', document.getElementById('movRootLabel').textContent.indexOf('F') !== -1);

    // ---------- basic chords ----------
    ok('35 basic diagrams', document.querySelectorAll('#basicBody svg').length === 35);
    ok('basic C maj pcs', [...document.querySelectorAll('#basicBody tr:first-child td.cell:nth-child(4) .cdot')]
      .map(g => +g.dataset.pc).sort((a, b) => a - b).join(',') === '0,4,7');

    // ---------- formula ----------
    ok('23 formula rows', document.querySelectorAll('#formulaBody tr').length === 23);
    ok('formula row maj', document.querySelector('#formulaBody tr[data-ftype="maj"] .fform').textContent === '1 3 5');
    ok('formula row dom7', document.querySelector('#formulaBody tr[data-ftype="7"] .fform').textContent === '1 3 5 \u266d7');
    const selRow = document.querySelector('#formulaBody tr.on');
    ok('formula selected row = maj', !!selRow && selRow.dataset.ftype === 'maj');

    // ---------- circle of fifths ----------
    ok('24 cof segments', document.querySelectorAll('#cofSvg .cof-seg').length === 24);
    // click G on the outer ring
    const gSeg = [...document.querySelectorAll('#cofSvg .cof-seg')].find(p => p.dataset.pc === '7');
    ok('cof G seg exists', !!gSeg);
    gSeg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    ok('key = G after cof click', window.__APP.state.keyPc === 7);
    ok('cof center label G', [...document.querySelectorAll('#cofSvg .cof-center-big')].some(t => t.textContent === 'G'));

    // ---------- key chord tables sync (C major, press V) ----------
    [...document.querySelectorAll('#keyRow button')].find(b => b.textContent === 'C').click();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: '5', bubbles: true }));
    ok('key 5 selects G7', window.__APP.state.sel.root === 7 && window.__APP.state.sel.type === '7');
    ok('formula now dom7', document.querySelector('#formulaBody tr.on').dataset.ftype === '7');
    // fretboard: chord tone marks exist for G7
    ok('fretboard chordt marks', document.querySelectorAll('#fretSvg .g-mark.chordt').length >= 8);
    // degree labels read against the chord root G
    const scaleMark = [...document.querySelectorAll('#fretSvg .g-mark.scale text')].find(t => t.textContent === '\u266d7');
    ok('fretboard shows b7 label', !!scaleMark);

    // ---------- local center ----------
    window.__APP.toggleCenter(7);   // center on G
    ok('center chip G = I', document.getElementById('centerChip').textContent.indexOf('I') !== -1);
    window.__APP.toggleCenter(10);  // center on F = b7 of G
    ok('center chip F = b7', document.getElementById('centerChip').textContent.indexOf('\u266d7') !== -1);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    ok('esc clears center', window.__APP.state.center === null);

    // ---------- display modes ----------
    dispBtns.find(b => b.textContent === 'NOTES').click();
    ok('notes mode on fretboard', [...document.querySelectorAll('#fretSvg .g-mark text')].every(t => /^[A-G\u266d]$/.test(t.textContent)));
    dispBtns.find(b => b.textContent === 'INTERVALS').click();
    ok('intervals mode on fretboard', [...document.querySelectorAll('#fretSvg .g-mark text')].some(t => t.textContent === 'P5'));
    dispBtns.find(b => b.textContent === 'DEGREES').click();

    // ---------- keyboard: arrows change key ----------
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
    ok('arrowleft key F', window.__APP.state.keyPc === 5);

    // ---------- scales ----------
    ok('7 major mode rows', document.querySelectorAll('#scalesBody .scale-row').length === 7);
    ok('3 extra scale rows', document.querySelectorAll('#extraScalesBody .scale-row').length === 3);
    const dorianRow = [...document.querySelectorAll('#scalesBody .scale-row')].find(r => r.dataset.scale === 'dorian');
    dorianRow.click();
    ok('scale selection dorian', window.__APP.state.scale === 'dorian');
    ok('dorian row highlighted', dorianRow.classList.contains('on'));
    ok('dorian degs text', dorianRow.querySelector('.sdegs').textContent.indexOf('\u266d3') !== -1);

    // ---------- persistence ----------
    const saved = JSON.parse(localStorage.getItem('guitar-poster-v1'));
    ok('state persisted', saved && saved.keyPc === 5 && saved.scale === 'dorian');
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
  window.__APP.toggleCenter(10);   // local center on b7 (F)
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
