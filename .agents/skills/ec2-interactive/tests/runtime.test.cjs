const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createInitialState, reduceState, buildProbeStates, mount } = require('../assets/lab-runtime.js');

const tpl = fs.readFileSync(path.join(__dirname, '..', 'assets', 'lab-template.html'), 'utf8');

test('lab-template.html matches ec2-review-pack CDN URLs and SVG CSS classes', () => {
  for (const needle of [
    'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
    '.fig-ink', '.fig-accent', '.fig-danger', '.fig-dot', '.fig-text', '.fig-math',
    'data-node-color="blue"', 'data-node-color="red"',
    '__TITLE__', '__SOURCE_COMMENT__', '__MNA_SCRIPT__', '__RUNTIME_SCRIPT__', '__LAB_SCRIPT__',
    'id="ec2-lab-root"', 'data-drawer="none"',
    'data-drawer-btn="left"', 'data-drawer-btn="right"',
    '.is-hot', '.is-bad', '.is-dim', '.is-off', '.port-chip', '.lab-badge', '.lab-badge-bg',
    '.predict-card', '.plot-wrap', 'od-theme',
  ]) {
    assert.ok(tpl.includes(needle), `missing ${needle}`);
  }

  const allowedUrls = new Set([
    'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
  ]);
  for (const m of tpl.matchAll(/https?:\/\/[^\s"'<>)]+/g)) {
    assert.ok(allowedUrls.has(m[0]), `unexpected external URL: ${m[0]}`);
  }
});

test('soft predict card can be dismissed without locking controls, and drawer Escape closes (Review Focus #2)', () => {
  const spec = {
    id: 'demo', title: '데모', archetype: 'probe',
    modes: [{ key: 'a', label: '기본', svg: '<svg viewBox="0 0 100 100"></svg>', ariaLabel: '회로' }],
    predict: { prompt: '출력?', options: [{ id: 'up', label: '상승' }], answerId: 'up', explain: '이유' },
    params: [{ key: 'vin', label: 'v_in', min: -10, max: 10, step: 1, unit: 'mV', def: 5 }],
    causalSteps: [{ id: 1, label: '1단계' }, { id: 2, label: '2단계' }],
    mistakes: { a: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
    evaluate: () => ({ tiles: [{ label: 'V', val: '1 V' }] }),
  };
  let st = createInitialState(spec);
  assert.equal(st.predictDismissed, false);
  st = reduceState(spec, st, { type: 'SET_PARAM', key: 'vin', value: 8 });
  assert.equal(st.params.vin, 8); // 예측 미완료여도 조작 잠기지 않음
  st = reduceState(spec, st, { type: 'DISMISS_PREDICT' });
  assert.equal(st.predictDismissed, true);
  st = reduceState(spec, st, { type: 'TOGGLE_PANEL', side: 'left', narrow: true });
  assert.equal(st.drawer, 'left');
  st = reduceState(spec, st, { type: 'CLOSE_DRAWER' });
  assert.equal(st.drawer, null);
  assert.ok(buildProbeStates(spec).some((p) => p.state.causalStep === 2));
});

test('runtime binds keyboard activation (Enter/Space) on data-port and data-elem hooks (Review Focus #2)', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'lab-runtime.js'), 'utf8');
  assert.match(src, /tabindex/);
  assert.match(src, /Enter/);
  assert.match(src, /Escape/);
});

test('bench archetype handles port setting, single-drawer toggle, presets, and probe states', () => {
  const spec = {
    id: 'bench-demo',
    title: '종단 조립 데모',
    archetype: 'bench',
    modes: [
      {
        key: 'vv',
        label: 'V-V',
        svg: '<svg viewBox="0 0 200 100"></svg>',
        ariaLabel: 'V-V 회로',
        ports: [
          { id: 'sense-rem', label: '감지 복제', options: [{ id: 'short', label: '단락' }, { id: 'open', label: '개방' }], def: 'short', answer: 'open' },
          { id: 'return-rem', label: '반송 복제', options: [{ id: 'short', label: '단락' }, { id: 'open', label: '개방' }], def: 'open', answer: 'short' },
        ],
      },
      {
        key: 'cc',
        label: 'C-C',
        svg: '<svg viewBox="0 0 200 100"></svg>',
        ariaLabel: 'C-C 회로',
        ports: [
          { id: 'sense-rem', label: '감지 복제', options: [{ id: 'short', label: '단락' }, { id: 'open', label: '개방' }], def: 'open', answer: 'short' },
          { id: 'return-rem', label: '반송 복제', options: [{ id: 'short', label: '단락' }, { id: 'open', label: '개방' }], def: 'short', answer: 'open' },
        ],
      },
    ],
    params: [{ key: 'rd', label: 'R_D', min: 1, max: 10, step: 0.5, unit: 'kΩ', def: 4 }],
    presets: [{ id: 'high-rd', label: '고부하', params: { rd: 10 }, ports: { 'sense-rem': 'open' } }],
    steps: [{ mode: 'cc', title: 'C-C 확인', params: { rd: 6 }, text: 'C-C 설명' }],
    toggles: [['labels', '배지 보기', true]],
    mistakes: {
      vv: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }],
      cc: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }],
    },
    evaluate: (st) => ({ tiles: [{ label: 'R_D', val: `${st.params.rd} kΩ` }] }),
  };

  let st = createInitialState(spec);
  assert.equal(st.mode, 'vv');
  assert.equal(st.ports['sense-rem'], 'short');
  assert.equal(st.toggles.labels, true);

  st = reduceState(spec, st, { type: 'SET_PORT', portId: 'sense-rem', value: 'open' });
  assert.equal(st.ports['sense-rem'], 'open');

  st = reduceState(spec, st, { type: 'APPLY_PRESET', id: 'high-rd' });
  assert.equal(st.params.rd, 10);

  st = reduceState(spec, st, { type: 'SET_PARAM', key: 'rd', value: 999 });
  assert.equal(st.params.rd, 10); // clamped to max

  st = reduceState(spec, st, { type: 'TOGGLE_OPT', key: 'labels' });
  assert.equal(st.toggles.labels, false);

  st = reduceState(spec, st, { type: 'SET_THEME', theme: 'dark' });
  assert.equal(st.theme, 'dark');

  st = reduceState(spec, st, { type: 'TOGGLE_PANEL', side: 'left', narrow: true });
  assert.equal(st.drawer, 'left');
  st = reduceState(spec, st, { type: 'TOGGLE_PANEL', side: 'right', narrow: true });
  assert.equal(st.drawer, 'right'); // single drawer replaces left

  st = reduceState(spec, st, { type: 'TOGGLE_PANEL', side: 'right', narrow: false });
  assert.equal(st.rightOpen, false);

  st = reduceState(spec, st, { type: 'PICK_STEP', index: 0 });
  assert.equal(st.mode, 'cc');
  assert.equal(st.params.rd, 6);

  const probes = buildProbeStates(spec);
  assert.ok(probes.some((p) => p.state.mode === 'vv' && p.state.ports['sense-rem'] === 'open' && p.state.ports['return-rem'] === 'short'));
  assert.ok(probes.some((p) => p.state.mode === 'vv' && (p.state.ports['sense-rem'] !== 'open' || p.state.ports['return-rem'] !== 'short')));
  assert.ok(probes.some((p) => p.state.mode === 'cc' && p.state.ports['sense-rem'] === 'short' && p.state.ports['return-rem'] === 'open'));
});

test('approx archetype element toggling and buildProbeStates cover each element OFF', () => {
  const spec = {
    id: 'approx-demo',
    title: '근사 붕괴 데모',
    archetype: 'approx',
    modes: [{ key: 'loading', label: '로딩', svg: '<svg viewBox="0 0 200 100"></svg>', ariaLabel: '로딩 회로' }],
    elems: [
      { id: 'rf-in', label: '입력 R_F 로딩' },
      { id: 'rf-out', label: '출력 R_F 로딩' },
    ],
    params: [{ key: 'rf', label: 'R_F', min: 1, max: 100, step: 1, unit: 'kΩ', def: 10 }],
    mistakes: { loading: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
    evaluate: () => ({ tiles: [{ label: '오차', val: '5%' }] }),
  };

  const st0 = createInitialState(spec);
  assert.deepEqual(st0.disabledElems, []);

  const st1 = reduceState(spec, st0, { type: 'TOGGLE_ELEM', id: 'rf-in' });
  assert.deepEqual(st1.disabledElems, ['rf-in']);
  assert.deepEqual(st0.disabledElems, []); // immutable

  const st2 = reduceState(spec, st1, { type: 'TOGGLE_ELEM', id: 'rf-in' });
  assert.deepEqual(st2.disabledElems, []);

  const probes = buildProbeStates(spec);
  assert.ok(probes.some((p) => p.state.disabledElems.includes('rf-in')));
  assert.ok(probes.some((p) => p.state.disabledElems.includes('rf-out')));
});

function createFakeEnv() {
  function parseHtmlInto(parent, html) {
    parent.children.length = 0;
    const stack = [parent];
    const tokenRe = /<(\/?)([a-zA-Z0-9:-]+)([^>]*?)(\/?)>|([^<]+)/g;
    let m;
    while ((m = tokenRe.exec(String(html || '')))) {
      const top = stack[stack.length - 1];
      if (m[5]) {
        if (top && m[5].trim()) top._text += m[5];
        continue;
      }
      const isClose = m[1] === '/';
      const tag = m[2];
      const attrStr = m[3] || '';
      const selfClose = m[4] === '/';
      if (isClose) {
        if (stack.length > 1) stack.pop();
        continue;
      }
      const el = makeMockNode(tag);
      for (const am of attrStr.matchAll(/([a-zA-Z0-9_:-]+)(?:="([^"]*)")?/g)) {
        el.setAttribute(am[1], am[2] !== undefined ? am[2] : '');
      }
      top.appendChild(el);
      if (!selfClose) stack.push(el);
    }
  }

  function matchesSelector(el, sel) {
    if (sel.startsWith('.')) return sel.slice(1).split('.').every((c) => el.classList.contains(c));
    if (sel.startsWith('#')) return el.getAttribute('id') === sel.slice(1);
    const attrM = sel.match(/^\[([a-zA-Z0-9_-]+)(?:="([^"]*)")?\]$/);
    if (attrM) {
      if (!el.hasAttribute(attrM[1])) return false;
      return attrM[2] === undefined ? true : el.getAttribute(attrM[1]) === attrM[2];
    }
    return el.tagName === sel.toUpperCase();
  }

  function makeMockNode(tagName) {
    const attrs = new Map();
    const listeners = new Map();
    const classes = new Set();
    const children = [];
    const node = {
      tagName: String(tagName || 'DIV').toUpperCase(),
      nodeType: 1,
      children,
      childNodes: children,
      parentNode: null,
      parentElement: null,
      dataset: {},
      style: {},
      _text: '',
      _html: '',
      get className() { return [...classes].join(' '); },
      set className(v) {
        classes.clear();
        for (const c of String(v || '').split(/\s+/)) if (c) classes.add(c);
      },
      classList: {
        add(...cs) { cs.forEach((c) => c && classes.add(c)); },
        remove(...cs) { cs.forEach((c) => classes.delete(c)); },
        toggle(c, force) {
          if (force === true) { classes.add(c); return true; }
          if (force === false) { classes.delete(c); return false; }
          if (classes.has(c)) { classes.delete(c); return false; }
          classes.add(c);
          return true;
        },
        contains(c) { return classes.has(c); },
      },
      get textContent() { return this._text; },
      set textContent(v) { this._text = String(v ?? ''); },
      get innerHTML() { return this._html; },
      set innerHTML(v) { this._html = String(v ?? ''); parseHtmlInto(this, this._html); },
      setAttribute(k, v) {
        const s = String(v);
        attrs.set(k, s);
        if (k === 'class') this.className = s;
        if (k.startsWith('data-')) {
          const camel = k.slice(5).replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
          this.dataset[camel] = s;
        }
      },
      getAttribute(k) { return attrs.has(k) ? attrs.get(k) : null; },
      hasAttribute(k) { return attrs.has(k); },
      removeAttribute(k) {
        attrs.delete(k);
        if (k.startsWith('data-')) {
          const camel = k.slice(5).replace(/-([a-z])/g, (_, ch) => ch.toUpperCase());
          delete this.dataset[camel];
        }
      },
      appendChild(child) {
        if (child.parentNode && child.parentNode.children) {
          const idx = child.parentNode.children.indexOf(child);
          if (idx >= 0) child.parentNode.children.splice(idx, 1);
        }
        child.parentNode = this;
        child.parentElement = this;
        children.push(child);
        return child;
      },
      removeChild(child) {
        const idx = children.indexOf(child);
        if (idx >= 0) children.splice(idx, 1);
        child.parentNode = null;
        child.parentElement = null;
      },
      replaceChildren(...nodes) {
        children.length = 0;
        for (const n of nodes) this.appendChild(n);
      },
      addEventListener(ev, fn) {
        if (!listeners.has(ev)) listeners.set(ev, []);
        listeners.get(ev).push(fn);
      },
      removeEventListener(ev, fn) {
        const list = listeners.get(ev) || [];
        const i = list.indexOf(fn);
        if (i >= 0) list.splice(i, 1);
      },
      dispatchEvent(ev) {
        const e = Object.assign({ preventDefault() {}, stopPropagation() {}, target: this }, ev);
        for (const fn of listeners.get(e.type) || []) fn(e);
      },
      focus() { fakeDoc.activeElement = this; },
      contains(other) {
        if (other === this) return true;
        return children.some((c) => c.contains && c.contains(other));
      },
      querySelectorAll(sel) {
        const out = [];
        const walk = (el) => {
          for (const ch of el.children || []) {
            if (matchesSelector(ch, sel)) out.push(ch);
            walk(ch);
          }
        };
        walk(this);
        return out;
      },
      querySelector(sel) {
        return this.querySelectorAll(sel)[0] || null;
      },
    };
    return node;
  }

  const docListeners = new Map();
  const fakeDoc = {
    documentElement: makeMockNode('html'),
    readyState: 'complete',
    activeElement: null,
    createElement: (t) => makeMockNode(t),
    createElementNS: (_ns, t) => makeMockNode(t),
    addEventListener(ev, fn) {
      if (!docListeners.has(ev)) docListeners.set(ev, []);
      docListeners.get(ev).push(fn);
    },
    removeEventListener(ev, fn) {
      const list = docListeners.get(ev) || [];
      const i = list.indexOf(fn);
      if (i >= 0) list.splice(i, 1);
    },
    dispatchEvent(ev) {
      const e = Object.assign({ preventDefault() {}, stopPropagation() {} }, ev);
      for (const fn of docListeners.get(e.type) || []) fn(e);
    },
  };
  let mathCalls = 0;
  const fakeWin = {
    __EC2_LAB__: null,
    renderMathInElement() { mathCalls++; },
    matchMedia: () => ({ matches: false, addEventListener: () => {}, removeEventListener: () => {} }),
    addEventListener: () => {},
    removeEventListener: () => {},
    localStorage: {
      getItem() { throw new Error('blocked'); },
      setItem() { throw new Error('blocked'); },
      removeItem() { throw new Error('blocked'); },
    },
  };
  return { makeMockNode, fakeDoc, fakeWin, getMathCalls: () => mathCalls };
}

test('mount exposes controller API, passes deps.mna, and survives throwing localStorage', () => {
  const { makeMockNode, fakeDoc, fakeWin } = createFakeEnv();
  const prevWin = globalThis.window;
  globalThis.window = fakeWin;
  try {
    const root = makeMockNode('div');
    root.id = 'ec2-lab-root';
    let seenMna = null;
    const fakeMna = { solveCircuit: () => ({ ok: true, nodes: {}, branches: {} }) };
    const spec = {
      id: 'mount-test',
      title: '마운트 테스트',
      archetype: 'probe',
      modes: [{ key: 'a', label: '기본', svg: '<svg viewBox="0 0 100 100"></svg>', ariaLabel: '회로' }],
      params: [{ key: 'vin', label: 'v_in', min: -5, max: 5, step: 1, unit: 'mV', def: 1 }],
      causalSteps: [{ id: 1, label: '1단계' }, { id: 2, label: '2단계' }],
      mistakes: { a: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
      evaluate: (st, mna) => {
        seenMna = mna;
        return {
          tiles: [{ label: '입력', val: `${st.params.vin} mV` }],
          formula: '$$v_{out} = 2 v_{in}$$',
        };
      },
    };

    const ctrl = mount(spec, root, { mna: fakeMna, document: fakeDoc, window: fakeWin, narrow: true });
    assert.equal(seenMna, fakeMna);
    assert.equal(fakeWin.__EC2_LAB__, ctrl);
    for (const fn of [
      'getState', 'setMode', 'pickStep', 'setParam', 'applyPreset',
      'toggleElem', 'setPort', 'pulseCausal', 'answerPredict', 'dismissPredict',
      'setTheme', 'togglePanel', 'closeDrawer', 'applyProbeState', 'listProbeStates',
    ]) {
      assert.equal(typeof ctrl[fn], 'function', `missing method ${fn}`);
    }

    ctrl.setParam('vin', '');
    assert.equal(ctrl.getState().params.vin, 1); // empty input ignored

    assert.equal(root.getAttribute('data-drawer'), 'none');
    ctrl.togglePanel('left');
    assert.equal(root.getAttribute('data-drawer'), 'left');
    ctrl.togglePanel('right');
    assert.equal(root.getAttribute('data-drawer'), 'right');
    fakeDoc.dispatchEvent({ type: 'keydown', key: 'Escape' });
    assert.equal(root.getAttribute('data-drawer'), 'none');

    ctrl.setTheme('dark');
    assert.equal(ctrl.getState().theme, 'dark');
    const probes = ctrl.listProbeStates();
    assert.ok(probes.length >= 2);
    ctrl.applyProbeState(probes[probes.length - 1].state);
    assert.equal(ctrl.getState().theme, 'dark'); // applyProbeState preserves theme
  } finally {
    if (prevWin === undefined) delete globalThis.window;
    else globalThis.window = prevWin;
  }
});

test('mounted SVG hooks handle Enter/Space, badges preserve transform, and approx plot renders', () => {
  const { makeMockNode, fakeDoc, fakeWin, getMathCalls } = createFakeEnv();
  const root = makeMockNode('div');
  const svgMarkup = [
    '<svg viewBox="0 0 300 160">',
    '<g data-elem="rf"><rect x="10" y="10" width="20" height="10"/></g>',
    '<g data-port="p1"><g class="port-chip"><rect x="0" y="0" width="30" height="14"/><text x="15" y="10">단락</text></g></g>',
    '<line data-causal-step="1" x1="10" y1="80" x2="100" y2="80"/>',
    '<line data-causal-step="2" x1="100" y1="80" x2="220" y2="80"/>',
    '<circle data-node="out" cx="220" cy="80" r="4"/>',
    '<g data-badges><g data-badge-for="out" transform="translate(220, 32)"></g></g>',
    '</svg>',
  ].join('');

  const spec = {
    id: 'hooks-test',
    title: '훅 테스트',
    archetype: 'approx',
    modes: [{
      key: 'm1',
      label: '기본',
      svg: svgMarkup,
      ariaLabel: '테스트 회로',
      ports: [{ id: 'p1', label: '포트 1', options: [{ id: 'short', label: '단락' }, { id: 'open', label: '개방' }], def: 'short', answer: 'open' }],
      elems: [{ id: 'rf', label: 'R_F' }],
    }],
    causalSteps: [{ id: 1, label: '1단계' }, { id: 2, label: '2단계' }],
    mistakes: { m1: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
    evaluate: (st) => ({
      tiles: [{ label: '상태', val: st.ports.p1 }],
      formula: '$$R_{in}$$',
      nodes: { out: { v: 2.67, unit: 'V', dir: 'up', hot: true } },
      plotData: {
        xLabel: 'R_F (kΩ)',
        yLabel: '이득',
        exact: [[1, 10], [10, 50], [100, 90]],
        approx: [[1, 20], [10, 55], [100, 91]],
        marker: [10, 50],
        errPct: 14.5,
        thresholdPct: 10,
      },
    }),
  };

  const ctrl = mount(spec, root, { document: fakeDoc, window: fakeWin, narrow: false });
  assert.ok(getMathCalls() >= 1);

  const elemHook = root.querySelector('[data-elem]');
  assert.equal(elemHook.getAttribute('tabindex'), '0');
  assert.equal(elemHook.getAttribute('role'), 'button');
  elemHook.dispatchEvent({ type: 'keydown', key: ' ' });
  assert.deepEqual(ctrl.getState().disabledElems, ['rf']);
  assert.ok(elemHook.classList.contains('is-off'));
  elemHook.dispatchEvent({ type: 'keydown', key: 'Enter' });
  assert.deepEqual(ctrl.getState().disabledElems, []);

  const portHook = root.querySelector('[data-port]');
  assert.equal(portHook.getAttribute('tabindex'), '0');
  portHook.dispatchEvent({ type: 'keydown', key: 'Enter' });
  const pop = root.querySelector('.port-popover');
  assert.ok(pop);
  fakeDoc.dispatchEvent({ type: 'keydown', key: 'Escape' });
  assert.equal(root.querySelector('.port-popover'), null);

  portHook.dispatchEvent({ type: 'keydown', key: ' ' });
  const pop2 = root.querySelector('.port-popover');
  const openBtn = pop2.querySelectorAll('button')[1];
  openBtn.dispatchEvent({ type: 'click' });
  assert.equal(ctrl.getState().ports.p1, 'open');
  assert.equal(portHook.querySelector('.port-chip').querySelector('text').textContent, '개방');

  const badgeSlot = root.querySelector('[data-badge-for="out"]');
  assert.equal(badgeSlot.getAttribute('transform'), 'translate(220, 32)');
  assert.ok(badgeSlot.querySelector('[data-badge-bg="1"]'));
  assert.equal(badgeSlot.querySelector('.lab-badge-text').textContent, '2.67 V ↑');

  ctrl.pulseCausal(1);
  const stepEls = root.querySelectorAll('[data-causal-step]');
  assert.ok(stepEls[0].classList.contains('is-hot'));
  assert.ok(stepEls[1].classList.contains('is-dim'));

  assert.ok(root.querySelector('.plot-wrap'));
  assert.ok(root.querySelector('.err-badge.is-bad'));
  assert.ok(root.querySelector('.fig-accent'));
  ctrl.destroy();
});
