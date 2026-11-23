// Standard HTML/SVG interactive lab runtime for ec2-interactive v2.
// Supports 3 archetypes ('probe', 'bench', 'approx') with pure state reducers
// and DOM mounting; exposes globalThis.EC2Lab and CommonJS module.exports.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.EC2Lab = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';

  // ---------- Spec Readers ----------

  function getModes(spec) {
    return Array.isArray(spec && spec.modes) ? spec.modes : [];
  }

  function getModeDef(spec, modeKey) {
    const modes = getModes(spec);
    return modes.find((m) => m.key === modeKey) || modes[0] || null;
  }

  function matchesMode(item, modeKey) {
    if (!item || typeof item !== 'object') return false;
    if (item.mode !== undefined) return item.mode === modeKey;
    if (Array.isArray(item.modes)) return item.modes.includes(modeKey);
    return true;
  }

  function getParamsForMode(spec, modeKey) {
    return (Array.isArray(spec && spec.params) ? spec.params : []).filter((p) => matchesMode(p, modeKey));
  }

  function normalizePortOptions(opts) {
    return (Array.isArray(opts) ? opts : []).map((o) => {
      if (o && typeof o === 'object') {
        const id = o.id !== undefined ? String(o.id) : String(o.value ?? o.label ?? '');
        return { id, label: String(o.label ?? id), shortLabel: String(o.shortLabel ?? o.label ?? id) };
      }
      const s = String(o);
      return { id: s, label: s, shortLabel: s };
    });
  }

  function getPortsForMode(spec, modeKey) {
    const m = getModeDef(spec, modeKey);
    const list = (m && Array.isArray(m.ports))
      ? m.ports
      : (Array.isArray(spec && spec.ports) ? spec.ports.filter((p) => matchesMode(p, modeKey)) : []);
    return list.map((p) => {
      const options = normalizePortOptions(p.options);
      const id = String(p.id);
      const def = p.def !== undefined ? String(p.def) : (options[0] ? options[0].id : '');
      return {
        id,
        label: String(p.label || id),
        options,
        def,
        answer: p.answer !== undefined ? String(p.answer) : (p.correct !== undefined ? String(p.correct) : undefined),
        badOption: p.badOption !== undefined ? String(p.badOption) : undefined,
      };
    });
  }

  function getElemsForMode(spec, modeKey) {
    const m = getModeDef(spec, modeKey);
    const list = (m && Array.isArray(m.elems))
      ? m.elems
      : (Array.isArray(spec && spec.elems) ? spec.elems.filter((e) => matchesMode(e, modeKey)) : []);
    return list.map((e) => (typeof e === 'string'
      ? { id: e, label: e }
      : { id: String(e.id), label: String(e.label || e.id) }));
  }

  function getCausalStepsForMode(spec, modeKey) {
    const m = getModeDef(spec, modeKey);
    const list = (m && Array.isArray(m.causalSteps))
      ? m.causalSteps
      : (Array.isArray(spec && spec.causalSteps) ? spec.causalSteps.filter((s) => matchesMode(s, modeKey)) : []);
    return list.map((s, idx) => ({
      id: s.id !== undefined ? s.id : idx + 1,
      label: String(s.label || s.title || `단계 ${idx + 1}`),
      detail: String(s.detail || s.text || ''),
    }));
  }

  function getStepsForMode(spec, modeKey) {
    const steps = Array.isArray(spec && spec.steps) ? spec.steps : [];
    const out = [];
    for (let i = 0; i < steps.length; i++) {
      if (!steps[i].mode || steps[i].mode === modeKey) out.push({ s: steps[i], i });
    }
    return out;
  }

  function normalizeToggleEntry(d) {
    return Array.isArray(d)
      ? { key: String(d[0]), label: String(d[1] ?? d[0]), def: Boolean(d[2]) }
      : { key: String(d.key), label: String(d.label ?? d.key), def: Boolean(d.def) };
  }

  function getTogglesForMode(spec, modeKey) {
    const raw = spec && spec.toggles;
    if (!raw) return [];
    const list = Array.isArray(raw) ? raw.filter((t) => Array.isArray(t) || matchesMode(t, modeKey)) : (raw[modeKey] || []);
    return list.map(normalizeToggleEntry);
  }

  function getPresetsForMode(spec, modeKey) {
    const m = getModeDef(spec, modeKey);
    const list = (m && Array.isArray(m.presets))
      ? m.presets
      : (Array.isArray(spec && spec.presets) ? spec.presets.filter((p) => matchesMode(p, modeKey)) : []);
    return list.map((p, idx) => ({
      id: String(p.id ?? p.key ?? idx),
      label: String(p.label || p.title || `프리셋 ${idx + 1}`),
      mode: p.mode,
      params: p.params || null,
      ports: p.ports || null,
      disabledElems: Array.isArray(p.disabledElems) ? p.disabledElems.slice() : null,
      causalStep: p.causalStep,
    }));
  }

  function getMistakesForMode(spec, modeKey) {
    const raw = spec && spec.mistakes;
    if (!raw) return [];
    return Array.isArray(raw) ? raw : (Array.isArray(raw[modeKey]) ? raw[modeKey] : []);
  }

  // ---------- Pure State Functions ----------

  function clampParam(spec, key, rawVal) {
    if (rawVal === '' || rawVal === null || rawVal === undefined || typeof rawVal === 'boolean') return null;
    const num = Number(rawVal);
    if (!Number.isFinite(num)) return null;
    const def = (Array.isArray(spec && spec.params) ? spec.params : []).find((p) => p.key === key);
    if (!def) return num;
    const min = typeof def.min === 'number' ? def.min : -Infinity;
    const max = typeof def.max === 'number' ? def.max : Infinity;
    return Math.min(max, Math.max(min, num));
  }

  function collectInitialToggles(spec) {
    const toggles = {};
    const raw = spec && spec.toggles;
    if (!raw) return toggles;
    const lists = Array.isArray(raw) ? [raw] : Object.values(raw);
    for (const list of lists) {
      for (const item of list || []) {
        const t = normalizeToggleEntry(item);
        if (!(t.key in toggles)) toggles[t.key] = t.def;
      }
    }
    return toggles;
  }

  function collectInitialPorts(spec, firstModeKey) {
    const ports = {};
    const addPorts = (list) => {
      for (const p of list || []) {
        const id = String(p.id);
        if (!(id in ports)) {
          const opts = normalizePortOptions(p.options);
          ports[id] = p.def !== undefined ? String(p.def) : (opts[0] ? opts[0].id : '');
        }
      }
    };
    for (const m of getModes(spec)) addPorts(m.ports);
    addPorts(spec && spec.ports);
    if (firstModeKey) {
      for (const p of getPortsForMode(spec, firstModeKey)) ports[p.id] = p.def;
    }
    return ports;
  }

  function createInitialState(spec) {
    const firstMode = getModes(spec)[0];
    const mode = firstMode ? firstMode.key : '';
    const params = {};
    for (const p of Array.isArray(spec && spec.params) ? spec.params : []) {
      params[p.key] = p.def !== undefined ? p.def : p.min;
    }
    const disabledElems = Array.isArray(spec && spec.initialDisabledElems)
      ? spec.initialDisabledElems.map(String)
      : [];
    return {
      mode,
      step: -1,
      params,
      disabledElems,
      ports: collectInitialPorts(spec, mode),
      causalStep: 0,
      predictChoice: null,
      predictDismissed: false,
      predictExpanded: false,
      predictVerified: false,
      toggles: collectInitialToggles(spec),
      theme: 'light',
      drawer: null,
      leftOpen: true,
      rightOpen: true,
      focusNode: null,
    };
  }

  function cloneState(state) {
    const out = {
      mode: state.mode,
      step: state.step,
      params: Object.assign({}, state.params),
      disabledElems: Array.isArray(state.disabledElems) ? state.disabledElems.slice() : [],
      ports: Object.assign({}, state.ports),
      causalStep: state.causalStep || 0,
      predictChoice: state.predictChoice ?? null,
      predictDismissed: Boolean(state.predictDismissed),
      predictExpanded: Boolean(state.predictExpanded),
      predictVerified: Boolean(state.predictVerified),
      toggles: Object.assign({}, state.toggles),
      theme: state.theme === 'dark' ? 'dark' : 'light',
      drawer: state.drawer || null,
      leftOpen: state.leftOpen !== false,
      rightOpen: state.rightOpen !== false,
      focusNode: state.focusNode ?? null,
    };
    if (state.narrow !== undefined) out.narrow = Boolean(state.narrow);
    return out;
  }

  function applyModeSwitch(spec, next, modeKey) {
    const target = getModes(spec).find((m) => m.key === modeKey);
    if (!target) return false;
    next.mode = target.key;
    next.step = -1;
    next.causalStep = 0;
    next.focusNode = null;
    next.predictChoice = null;
    next.predictVerified = false;
    if (Array.isArray(target.ports)) {
      for (const p of getPortsForMode(spec, target.key)) next.ports[p.id] = p.def;
    }
    return true;
  }

  function applyPatch(spec, next, patch) {
    if (patch.params && typeof patch.params === 'object') {
      for (const [k, v] of Object.entries(patch.params)) {
        const clamped = clampParam(spec, k, v);
        if (clamped !== null) next.params[k] = clamped;
      }
    }
    if (patch.ports && typeof patch.ports === 'object') {
      for (const [k, v] of Object.entries(patch.ports)) next.ports[k] = String(v);
    }
    if (Array.isArray(patch.disabledElems)) next.disabledElems = patch.disabledElems.map(String);
    if (patch.causalStep !== undefined) next.causalStep = patch.causalStep;
  }

  function reduceState(spec, state, action) {
    if (!action || typeof action !== 'object') return state;
    const next = cloneState(state);

    switch (action.type) {
      case 'SET_MODE': {
        if (action.mode === state.mode) return state;
        return applyModeSwitch(spec, next, action.mode) ? next : state;
      }

      case 'PICK_STEP': {
        const idx = action.index !== undefined ? action.index : action.step;
        if (idx === -1) {
          next.step = -1;
          return next;
        }
        const s = (Array.isArray(spec && spec.steps) ? spec.steps : [])[idx];
        if (!s) return state;
        if (s.mode && s.mode !== next.mode) applyModeSwitch(spec, next, s.mode);
        applyPatch(spec, next, s);
        next.step = idx;
        return next;
      }

      case 'SET_PARAM': {
        const clamped = clampParam(spec, action.key, action.value);
        if (clamped === null) return state;
        next.params[action.key] = clamped;
        next.step = -1;
        return next;
      }

      case 'APPLY_PRESET': {
        const id = String(action.id ?? action.key ?? '');
        const preset = action.preset || getPresetsForMode(spec, next.mode).find((p) => p.id === id)
          || (Array.isArray(spec && spec.presets) ? spec.presets.find((p) => String(p.id ?? p.key) === id) : null);
        if (!preset) return state;
        if (preset.mode && preset.mode !== next.mode) applyModeSwitch(spec, next, preset.mode);
        applyPatch(spec, next, preset);
        next.step = -1;
        return next;
      }

      case 'TOGGLE_ELEM': {
        const id = String(action.id);
        const idx = next.disabledElems.indexOf(id);
        if (idx >= 0) next.disabledElems.splice(idx, 1);
        else next.disabledElems.push(id);
        return next;
      }

      case 'SET_PORT': {
        const portId = String(action.portId ?? action.id ?? action.port ?? '');
        if (!portId) return state;
        next.ports[portId] = String(action.value);
        return next;
      }

      case 'PULSE_CAUSAL': {
        if (action.reset === true || action.step === 0 || action.causalStep === 0) {
          next.causalStep = 0;
          return next;
        }
        const explicit = action.step !== undefined ? action.step : action.causalStep;
        if (explicit !== undefined) {
          next.causalStep = explicit;
          return next;
        }
        const ids = getCausalStepsForMode(spec, next.mode).map((s) => s.id);
        if (ids.length === 0) return state;
        const delta = action.delta !== undefined ? action.delta : 1;
        const idx = ids.indexOf(next.causalStep);
        if (delta < 0) next.causalStep = idx <= 0 ? 0 : ids[idx - 1];
        else next.causalStep = idx < 0 ? ids[0] : (idx + 1 < ids.length ? ids[idx + 1] : 0);
        return next;
      }

      case 'ANSWER_PREDICT': {
        const prediction = spec.predict;
        const choice = action.choice ?? action.optionId ?? action.id;
        if (!matchesMode(prediction, state.mode) || state.predictDismissed ||
            !prediction.options.some((option) => (typeof option === 'object' ? option.id : option) === choice)) return state;
        next.predictChoice = choice;
        next.predictExpanded = true;
        next.predictVerified = false;
        return next;
      }

      case 'VERIFY_PREDICT': {
        const prediction = spec.predict;
        if (!matchesMode(prediction, state.mode) || state.predictDismissed ||
            state.predictChoice === null || state.predictVerified) return state;
        if (prediction.check) {
          applyPatch(spec, next, prediction.check.before || {});
          applyPatch(spec, next, prediction.check.after);
          next.step = -1;
        }
        next.predictVerified = true;
        return next;
      }

      case 'OPEN_PREDICT': {
        next.predictExpanded = true;
        next.predictDismissed = false;
        return next;
      }

      case 'DISMISS_PREDICT': {
        next.predictChoice = null;
        next.predictDismissed = true;
        next.predictExpanded = false;
        next.predictVerified = false;
        return next;
      }

      case 'TOGGLE_OPT': {
        next.toggles[action.key] = !next.toggles[action.key];
        return next;
      }

      case 'SET_THEME': {
        if (action.theme !== 'light' && action.theme !== 'dark') return state;
        next.theme = action.theme;
        return next;
      }

      case 'TOGGLE_PANEL': {
        const side = action.side;
        if (side !== 'left' && side !== 'right') return state;
        if (action.narrow) next.drawer = next.drawer === side ? null : side;
        else if (side === 'left') next.leftOpen = !next.leftOpen;
        else next.rightOpen = !next.rightOpen;
        return next;
      }

      case 'CLOSE_DRAWER': {
        next.drawer = null;
        return next;
      }

      case 'FOCUS_NODE': {
        const nid = action.nodeId ? String(action.nodeId) : null;
        next.focusNode = next.focusNode === nid ? null : nid;
        return next;
      }

      default:
        return state;
    }
  }

  function buildProbeStates(spec) {
    const states = [];
    const base = createInitialState(spec);
    states.push({ label: '초기 상태', state: base });

    if (spec && spec.predict && Array.isArray(spec.predict.options) && spec.predict.options.length > 0) {
      const mode = getModes(spec).find((m) => matchesMode(spec.predict, m.key));
      if (mode) {
        const start = reduceState(spec, base, { type: 'SET_MODE', mode: mode.key });
        const opt = spec.predict.options[0];
        const choice = typeof opt === 'object' ? opt.id : opt;
        const chosen = reduceState(spec, start, { type: 'ANSWER_PREDICT', choice });
        states.push({ label: '예측 카드 응답', state: chosen });
        states.push({ label: '예측 결과 확인', state: reduceState(spec, chosen, { type: 'VERIFY_PREDICT' }) });
      }
    }

    for (const m of getModes(spec)) {
      let modeState = reduceState(spec, base, { type: 'SET_MODE', mode: m.key });
      modeState = reduceState(spec, modeState, { type: 'DISMISS_PREDICT' });
      const mLabel = m.label || m.key;
      states.push({ label: `모드: ${mLabel}`, state: modeState });

      const cSteps = getCausalStepsForMode(spec, m.key);
      if (cSteps.length > 0) {
        states.push({
          label: `${mLabel}: 인과 마지막 박자`,
          state: reduceState(spec, modeState, { type: 'PULSE_CAUSAL', step: cSteps[cSteps.length - 1].id }),
        });
      }

      const portDefs = getPortsForMode(spec, m.key);
      if (portDefs.length > 0) {
        let correctState = modeState;
        const answers = {};
        for (const p of portDefs) {
          const ans = p.answer !== undefined ? p.answer : (p.options[0] ? p.options[0].id : p.def);
          answers[p.id] = ans;
          correctState = reduceState(spec, correctState, { type: 'SET_PORT', portId: p.id, value: ans });
        }
        states.push({ label: `${mLabel}: 정답 조립`, state: correctState });

        const badTarget = portDefs.find((p) => p.options.some((o) => o.id !== answers[p.id]));
        if (badTarget) {
          const badOpt = badTarget.badOption && badTarget.options.some((o) => o.id === badTarget.badOption)
            ? badTarget.badOption
            : badTarget.options.find((o) => o.id !== answers[badTarget.id]).id;
          states.push({
            label: `${mLabel}: 대표 오조립`,
            state: reduceState(spec, correctState, { type: 'SET_PORT', portId: badTarget.id, value: badOpt }),
          });
        }
      }

      for (const elItem of getElemsForMode(spec, m.key)) {
        states.push({
          label: `${mLabel}: ${elItem.label} OFF`,
          state: reduceState(spec, modeState, { type: 'TOGGLE_ELEM', id: elItem.id }),
        });
      }

      for (const preset of getPresetsForMode(spec, m.key)) {
        states.push({
          label: `${mLabel}: 프리셋 ${preset.label}`,
          state: reduceState(spec, modeState, { type: 'APPLY_PRESET', id: preset.id }),
        });
      }
    }

    const allSteps = Array.isArray(spec && spec.steps) ? spec.steps : [];
    for (let i = 0; i < allSteps.length; i++) {
      let st = reduceState(spec, base, { type: 'PICK_STEP', index: i });
      st = reduceState(spec, st, { type: 'DISMISS_PREDICT' });
      states.push({
        label: `단계 ${i + 1}: ${allSteps[i].title || allSteps[i].label || ''}`.trim(),
        state: st,
      });
    }

    return states;
  }

  // ---------- DOM & Formatting Helpers ----------

  function el(doc, tag, attrs, text) {
    const node = doc.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v === undefined || v === null || v === false) continue;
        if (k === 'className') node.className = String(v);
        else node.setAttribute(k, v === true ? '' : String(v));
      }
    }
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function svgEl(doc, tag, attrs, text) {
    const node = doc.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v !== undefined && v !== null) node.setAttribute(k, String(v));
      }
    }
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function formatParamValue(p, val) {
    if (typeof p.format === 'function') return String(p.format(val));
    const num = Number(val);
    if (!Number.isFinite(num)) return String(val ?? '');
    let numStr;
    if (Math.abs(num) >= 100 || Number.isInteger(num)) numStr = String(Math.round(num * 100) / 100);
    else if (Math.abs(num) >= 1) numStr = num.toFixed(2).replace(/\.?0+$/, '');
    else numStr = num.toPrecision(3).replace(/\.?0+$/, '');
    return p.unit ? `${numStr} ${p.unit}` : numStr;
  }

  function formatTick(v) {
    if (!Number.isFinite(v)) return '';
    if (v === 0) return '0';
    const abs = Math.abs(v);
    if (abs >= 1000 || abs < 0.01) return v.toExponential(1).replace(/\.0e/, 'e');
    if (abs >= 10) return String(Math.round(v * 10) / 10);
    return String(Math.round(v * 100) / 100);
  }

  function formatNodeBadge(info) {
    if (info === null || info === undefined) return '';
    if (typeof info === 'string') return info;
    if (typeof info === 'number') return Number.isFinite(info) ? formatTick(info) : '';
    let base = '';
    if (info.badge !== undefined) base = String(info.badge);
    else if (info.text !== undefined) base = String(info.text);
    else if (info.v !== undefined || info.val !== undefined) {
      const raw = info.v !== undefined ? info.v : info.val;
      const numStr = typeof raw === 'number' && Number.isFinite(raw) ? formatTick(raw) : String(raw);
      base = info.unit ? `${numStr} ${info.unit}` : numStr;
    }
    if (!base) return '';
    if (info.dir === 'up' && !base.includes('↑')) return `${base} ↑`;
    if (info.dir === 'down' && !base.includes('↓')) return `${base} ↓`;
    if ((info.dir === '↑' || info.dir === '↓') && !base.includes(info.dir)) return `${base} ${info.dir}`;
    return base;
  }

  function ensureShell(doc, rootEl, spec) {
    rootEl.classList.add('lab-app');
    if (!rootEl.getAttribute('data-drawer')) rootEl.setAttribute('data-drawer', 'none');

    let topbar = rootEl.querySelector('.topbar');
    let layout = rootEl.querySelector('.layout');
    let scrim = rootEl.querySelector('.scrim');

    if (!topbar || !layout) {
      rootEl.replaceChildren();
      const makeToggleSvg = (leftSide) => {
        const s = svgEl(doc, 'svg', { viewBox: '0 0 24 24', 'aria-hidden': 'true' });
        s.appendChild(svgEl(doc, 'rect', { class: 'strip', x: leftSide ? '3' : '15', y: '4', width: '6', height: '16', rx: '1' }));
        s.appendChild(svgEl(doc, 'rect', { x: '3', y: '4', width: '18', height: '16', rx: '3' }));
        s.appendChild(svgEl(doc, 'path', { d: leftSide ? 'M9 4v16' : 'M15 4v16' }));
        return s;
      };

      const leftBtn = el(doc, 'button', {
        className: 'text-btn panel-toggle', type: 'button',
        'data-drawer-btn': 'left', 'aria-label': '조작 패널', 'aria-expanded': 'true', 'aria-pressed': 'true',
      });
      leftBtn.appendChild(makeToggleSvg(true));
      leftBtn.appendChild(el(doc, 'span', null, '조작'));

      const themeBtn = el(doc, 'button', {
        className: 'text-btn theme-toggle', type: 'button',
        'aria-label': '다크 모드로 전환', title: '다크 모드로 전환',
      });
      const moon = svgEl(doc, 'svg', { class: 'i-moon', viewBox: '0 0 24 24', 'aria-hidden': 'true' });
      moon.appendChild(svgEl(doc, 'path', { d: 'M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z' }));
      const sun = svgEl(doc, 'svg', { class: 'i-sun', viewBox: '0 0 24 24', 'aria-hidden': 'true' });
      sun.appendChild(svgEl(doc, 'circle', { cx: '12', cy: '12', r: '4' }));
      sun.appendChild(svgEl(doc, 'path', { d: 'M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4' }));
      themeBtn.appendChild(moon);
      themeBtn.appendChild(sun);

      const rightBtn = el(doc, 'button', {
        className: 'text-btn panel-toggle', type: 'button',
        'data-drawer-btn': 'right', 'aria-label': '설명 패널', 'aria-expanded': 'true', 'aria-pressed': 'true',
      });
      rightBtn.appendChild(makeToggleSvg(false));
      rightBtn.appendChild(el(doc, 'span', null, '설명'));

      topbar = el(doc, 'header', { className: 'topbar' });
      topbar.appendChild(leftBtn);
      topbar.appendChild(el(doc, 'strong', { className: 'brand' }, spec.title || ''));
      topbar.appendChild(el(doc, 'div', { className: 'seg', role: 'group', 'aria-label': '모드 선택' }));
      topbar.appendChild(themeBtn);
      topbar.appendChild(rightBtn);

      const panelLeft = el(doc, 'aside', { className: 'panel panel-left is-open', 'aria-label': '조작' });
      panelLeft.appendChild(el(doc, 'div', { className: 'panel-inner' }));

      const stage = el(doc, 'main', { className: 'stage', 'aria-label': '회로 실험실' });
      stage.appendChild(el(doc, 'div', { className: 'predict-slot' }));
      const wrap = el(doc, 'div', { className: 'lab-stage-wrap' });
      wrap.appendChild(el(doc, 'div', { className: 'lab-stage' }));
      stage.appendChild(wrap);
      stage.appendChild(el(doc, 'div', { className: 'plot-slot' }));

      const panelRight = el(doc, 'aside', { className: 'panel panel-right is-open', 'aria-label': '설명' });
      panelRight.appendChild(el(doc, 'div', { className: 'panel-inner' }));

      layout = el(doc, 'div', { className: 'layout' });
      layout.appendChild(panelLeft);
      layout.appendChild(stage);
      layout.appendChild(panelRight);

      scrim = el(doc, 'div', { className: 'scrim', 'aria-hidden': 'true' });

      rootEl.appendChild(topbar);
      rootEl.appendChild(layout);
      rootEl.appendChild(scrim);
    }

    const panelLeft = rootEl.querySelector('.panel-left');
    const panelRight = rootEl.querySelector('.panel-right');
    return {
      leftBtn: rootEl.querySelector('[data-drawer-btn="left"]'),
      rightBtn: rootEl.querySelector('[data-drawer-btn="right"]'),
      brandEl: rootEl.querySelector('.brand'),
      modeSegEl: rootEl.querySelector('.seg'),
      themeBtn: rootEl.querySelector('.theme-toggle'),
      panelLeft,
      panelLeftInner: panelLeft ? panelLeft.querySelector('.panel-inner') : null,
      panelRight,
      panelRightInner: panelRight ? panelRight.querySelector('.panel-inner') : null,
      stageEl: rootEl.querySelector('.stage'),
      predictSlot: rootEl.querySelector('.predict-slot'),
      stageWrap: rootEl.querySelector('.lab-stage-wrap'),
      svgHost: rootEl.querySelector('.lab-stage'),
      plotSlot: rootEl.querySelector('.plot-slot'),
      scrimEl: rootEl.querySelector('.scrim'),
    };
  }

  function buildPlotSvg(doc, plotData) {
    const W = 480;
    const H = 228;
    const x0 = 72;
    const x1 = 460;
    const y0 = 20;
    const y1 = 166;
    const pw = x1 - x0;
    const ph = y1 - y0;

    const exact = Array.isArray(plotData.exact) ? plotData.exact.filter((pt) => Number.isFinite(pt[0]) && Number.isFinite(pt[1])) : [];
    const approx = Array.isArray(plotData.approx) ? plotData.approx.filter((pt) => Number.isFinite(pt[0]) && Number.isFinite(pt[1])) : [];
    const allPts = exact.concat(approx);
    if (allPts.length === 0) return null;

    let xMin = typeof plotData.xMin === 'number' ? plotData.xMin : Math.min(...allPts.map((p) => p[0]));
    let xMax = typeof plotData.xMax === 'number' ? plotData.xMax : Math.max(...allPts.map((p) => p[0]));
    if (xMax <= xMin) xMax = xMin + 1;

    let yMin = typeof plotData.yMin === 'number' ? plotData.yMin : Math.min(...allPts.map((p) => p[1]));
    let yMax = typeof plotData.yMax === 'number' ? plotData.yMax : Math.max(...allPts.map((p) => p[1]));
    if (yMax <= yMin) {
      yMin -= 1;
      yMax += 1;
    }

    const isLogX = plotData.xScale === 'log' && xMin > 0 && xMax > 0;
    const mapX = (x) => {
      const t = isLogX
        ? (Math.log10(Math.max(x, xMin)) - Math.log10(xMin)) / (Math.log10(xMax) - Math.log10(xMin))
        : (x - xMin) / (xMax - xMin);
      return x0 + Math.max(0, Math.min(1, t)) * pw;
    };
    const mapY = (y) => y1 - Math.max(0, Math.min(1, (y - yMin) / (yMax - yMin))) * ph;
    const toPathD = (pts) => pts.map((pt, i) => `${i === 0 ? 'M' : 'L'}${mapX(pt[0]).toFixed(1)},${mapY(pt[1]).toFixed(1)}`).join(' ');

    const svg = svgEl(doc, 'svg', {
      viewBox: `0 0 ${W} ${H}`,
      role: 'img',
      'aria-label': plotData.ariaLabel || `${plotData.xLabel || 'x'} 대비 ${plotData.yLabel || 'y'} 비교 그래프`,
    });

    svg.appendChild(svgEl(doc, 'line', { class: 'plot-axis', x1: x0, y1: y0, x2: x0, y2: y1 }));
    svg.appendChild(svgEl(doc, 'line', { class: 'plot-axis', x1: x0, y1: y1, x2: x1, y2: y1 }));

    for (const yt of [yMin, (yMin + yMax) / 2, yMax]) {
      const py = mapY(yt);
      svg.appendChild(svgEl(doc, 'line', { class: 'plot-axis', x1: x0, y1: py.toFixed(1), x2: x0 + 5, y2: py.toFixed(1) }));
      svg.appendChild(svgEl(doc, 'text', {
        class: 'fig-muted', x: x0 - 14, y: (py + 4).toFixed(1), 'text-anchor': 'end',
      }, formatTick(yt)));
    }

    const xTicks = isLogX ? [xMin, Math.sqrt(xMin * xMax), xMax] : [xMin, (xMin + xMax) / 2, xMax];
    for (const xt of xTicks) {
      const px = mapX(xt);
      svg.appendChild(svgEl(doc, 'line', { class: 'plot-axis', x1: px.toFixed(1), y1: y1 - 5, x2: px.toFixed(1), y2: y1 }));
      svg.appendChild(svgEl(doc, 'text', {
        class: 'fig-muted', x: px.toFixed(1), y: y1 + 24, 'text-anchor': 'middle',
      }, formatTick(xt)));
    }

    if (plotData.xLabel) {
      svg.appendChild(svgEl(doc, 'text', {
        class: 'fig-muted', x: (x0 + x1) / 2, y: H - 8, 'text-anchor': 'middle',
      }, plotData.xLabel));
    }
    if (plotData.yLabel) {
      const cy = (y0 + y1) / 2;
      svg.appendChild(svgEl(doc, 'text', {
        class: 'fig-muted', x: 16, y: cy, 'text-anchor': 'middle', transform: `rotate(-90 16 ${cy})`,
      }, plotData.yLabel));
    }

    if (approx.length >= 2) svg.appendChild(svgEl(doc, 'path', { class: 'fig-ink', 'stroke-dasharray': '6 4', d: toPathD(approx) }));
    if (exact.length >= 2) svg.appendChild(svgEl(doc, 'path', { class: 'fig-accent', d: toPathD(exact) }));

    if (Array.isArray(plotData.marker) && Number.isFinite(plotData.marker[0]) && Number.isFinite(plotData.marker[1])) {
      const mx = mapX(plotData.marker[0]);
      const my = mapY(plotData.marker[1]);
      svg.appendChild(svgEl(doc, 'line', { class: 'plot-guide', x1: mx.toFixed(1), y1: y1, x2: mx.toFixed(1), y2: my.toFixed(1) }));
      svg.appendChild(svgEl(doc, 'circle', { class: 'fig-dot', cx: mx.toFixed(1), cy: my.toFixed(1), r: '4.5' }));
    }
    if (Array.isArray(plotData.approxMarker) && Number.isFinite(plotData.approxMarker[0]) && Number.isFinite(plotData.approxMarker[1])) {
      svg.appendChild(svgEl(doc, 'circle', {
        class: 'fig-ink', cx: mapX(plotData.approxMarker[0]).toFixed(1), cy: mapY(plotData.approxMarker[1]).toFixed(1), r: '4',
      }));
    }
    return svg;
  }

  function findHookEl(svg, attr, value) {
    if (!svg) return null;
    for (const node of svg.querySelectorAll(`[${attr}]`)) {
      if (node.getAttribute(attr) === value) return node;
    }
    return null;
  }

  function estimateBadgeAnchor(svg, nodeId) {
    const matches = [];
    for (const node of svg.querySelectorAll('[data-node]')) {
      if (node.getAttribute('data-node') === nodeId) matches.push(node);
    }
    if (matches.length === 0) return null;
    const target = matches.find((n) => n.tagName && n.tagName.toLowerCase() === 'circle') || matches[0];
    const cx = parseFloat(target.getAttribute('cx'));
    const cy = parseFloat(target.getAttribute('cy'));
    if (Number.isFinite(cx) && Number.isFinite(cy)) return [cx, cy - 22];
    const x = parseFloat(target.getAttribute('x'));
    const y = parseFloat(target.getAttribute('y'));
    if (Number.isFinite(x) && Number.isFinite(y)) return [x, y - 18];
    try {
      if (typeof target.getBBox === 'function') {
        const b = target.getBBox();
        return [b.x + b.width / 2, b.y - 16];
      }
    } catch (e) {}
    return [40, 24];
  }

  function addPanelSection(doc, parent, title, bodyEl) {
    const sec = el(doc, 'div', { className: 'sec' });
    sec.appendChild(el(doc, 'h3', { className: 'sec-title' }, title));
    sec.appendChild(bodyEl);
    parent.appendChild(sec);
    return sec;
  }

  // ---------- Mount ----------

  function mount(spec, rootEl, deps) {
    const d = deps || {};
    const doc = d.document || (typeof document !== 'undefined' ? document : null);
    const win = d.window || (typeof window !== 'undefined' ? window : null);
    const mna = d.mna || (typeof globalThis !== 'undefined' ? globalThis.EC2MNA : null);

    if (!doc || !rootEl) {
      throw new Error('EC2Lab.mount requires a valid document and root element');
    }

    const systemDark = () => {
      try { return Boolean(win && win.matchMedia && win.matchMedia('(prefers-color-scheme: dark)').matches); } catch (e) { return false; }
    };
    const isNarrowViewport = () => {
      if (d.narrow !== undefined) return Boolean(d.narrow);
      try { return Boolean(win && win.matchMedia && win.matchMedia('(max-width: 1023.98px)').matches); } catch (e) { return false; }
    };
    const isReduceMotion = () => {
      try { return Boolean(win && win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch (e) { return false; }
    };

    let savedTheme = null;
    try {
      savedTheme = win && win.localStorage ? win.localStorage.getItem('od-theme') : null;
    } catch (e) {
      savedTheme = null;
    }

    let state = createInitialState(spec);
    state.theme = (savedTheme === 'light' || savedTheme === 'dark') ? savedTheme : (systemDark() ? 'dark' : 'light');
    state.narrow = isNarrowViewport();

    const dom = ensureShell(doc, rootEl, spec);
    if (dom.brandEl) dom.brandEl.textContent = spec.title || '';

    let openPortMenu = null;
    let lastModeKey = null;
    let lastSvgEl = null;
    let leftBuiltMode = null;
    let pulseTimer = null;
    let loggedEvalErr = false;

    const stopPulse = () => {
      if (pulseTimer !== null) {
        clearInterval(pulseTimer);
        pulseTimer = null;
      }
    };

    const renderMath = () => {
      if (!win || typeof win.renderMathInElement !== 'function') return;
      const opts = {
        delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }],
        throwOnError: false,
        ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'svg'],
      };
      try {
        if (dom.panelRightInner) win.renderMathInElement(dom.panelRightInner, opts);
        if (dom.predictSlot) win.renderMathInElement(dom.predictSlot, opts);
      } catch (e) {}
    };

    function updateSvgPortAria() {
      if (!lastSvgEl) return;
      for (const portEl of lastSvgEl.querySelectorAll('[data-port]')) {
        portEl.setAttribute('aria-expanded', openPortMenu === portEl.getAttribute('data-port') ? 'true' : 'false');
      }
    }

    function closePortPopover(restoreFocus) {
      const existing = dom.stageWrap && dom.stageWrap.querySelector('.port-popover');
      if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
      const prevId = openPortMenu;
      openPortMenu = null;
      if (restoreFocus && prevId && lastSvgEl) {
        const portEl = findHookEl(lastSvgEl, 'data-port', prevId);
        if (portEl && typeof portEl.focus === 'function') portEl.focus();
      }
      updateSvgPortAria();
    }

    function openPortPopover(portId, anchorEl) {
      const portDef = getPortsForMode(spec, state.mode).find((p) => p.id === portId);
      if (!portDef || portDef.options.length === 0) return;
      if (openPortMenu === portId) {
        closePortPopover(false);
        return;
      }
      closePortPopover(false);
      openPortMenu = portId;
      updateSvgPortAria();

      const pop = el(doc, 'div', { className: 'port-popover', role: 'menu', 'aria-label': portDef.label });
      pop.appendChild(el(doc, 'div', { className: 'port-popover-title' }, portDef.label));
      const menuBtns = [];
      for (const opt of portDef.options) {
        const pressed = state.ports[portId] === opt.id ? 'true' : 'false';
        const btn = el(doc, 'button', {
          type: 'button', role: 'menuitemradio', 'aria-pressed': pressed, 'aria-checked': pressed,
        }, opt.label);
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          closePortPopover(true);
          dispatch({ type: 'SET_PORT', portId, value: opt.id });
        });
        menuBtns.push(btn);
        pop.appendChild(btn);
      }
      pop.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          if (menuBtns.length === 0) return;
          e.preventDefault();
          const cur = menuBtns.indexOf(doc.activeElement);
          const nextIdx = e.key === 'ArrowDown'
            ? (cur + 1) % menuBtns.length
            : (cur <= 0 ? menuBtns.length - 1 : cur - 1);
          if (menuBtns[nextIdx] && menuBtns[nextIdx].focus) menuBtns[nextIdx].focus();
        }
      });
      dom.stageWrap.appendChild(pop);
      const focusTarget = menuBtns.find((b) => b.getAttribute('aria-pressed') === 'true') || menuBtns[0];
      if (focusTarget && typeof focusTarget.focus === 'function') {
        try { focusTarget.focus(); } catch (e) {}
      }

      try {
        if (anchorEl && anchorEl.getBoundingClientRect && dom.stageWrap.getBoundingClientRect) {
          const wr = dom.stageWrap.getBoundingClientRect();
          const ar = anchorEl.getBoundingClientRect();
          if (wr.width > 0 && ar.width >= 0) {
            pop.style.left = `${Math.round(Math.max(8, Math.min(ar.left - wr.left, Math.max(8, wr.width - 170))))}px`;
            pop.style.top = `${Math.round(Math.max(8, Math.min(ar.bottom - wr.top + 6, Math.max(8, wr.height - 120))))}px`;
          }
        }
      } catch (e) {}
    }

    function bindSvgHooks(svg) {
      for (const nodeEl of svg.querySelectorAll('[data-node]')) {
        const nid = nodeEl.getAttribute('data-node');
        nodeEl.addEventListener('click', () => dispatch({ type: 'FOCUS_NODE', nodeId: nid }));
      }
      for (const elemEl of svg.querySelectorAll('[data-elem]')) {
        const eid = elemEl.getAttribute('data-elem');
        elemEl.setAttribute('role', 'button');
        elemEl.setAttribute('tabindex', '0');
        const toggle = (e) => { e.stopPropagation(); dispatch({ type: 'TOGGLE_ELEM', id: eid }); };
        elemEl.addEventListener('click', toggle);
        elemEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(e); }
        });
      }
      for (const portEl of svg.querySelectorAll('[data-port]')) {
        const pid = portEl.getAttribute('data-port');
        portEl.setAttribute('role', 'button');
        portEl.setAttribute('tabindex', '0');
        portEl.setAttribute('aria-haspopup', 'menu');
        portEl.setAttribute('aria-expanded', 'false');
        const open = (e) => { e.stopPropagation(); openPortPopover(pid, portEl); };
        portEl.addEventListener('click', open);
        portEl.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(e); }
        });
      }
    }

    function syncBadges(svg, evalRes) {
      const showLabels = state.toggles && ('labels' in state.toggles) ? Boolean(state.toggles.labels) : true;
      const badgeMap = new Map();
      const collect = (mapObj, onlyExistingSlot) => {
        if (!showLabels || !mapObj || typeof mapObj !== 'object') return;
        for (const [id, info] of Object.entries(mapObj)) {
          if (badgeMap.has(id)) continue;
          if (onlyExistingSlot && !findHookEl(svg, 'data-badge-for', id)) continue;
          const txt = formatNodeBadge(info);
          if (txt) badgeMap.set(id, { txt, info });
        }
      };
      collect(evalRes && evalRes.nodes, false);
      collect(evalRes && evalRes.branches, false);
      collect(evalRes && evalRes.ports, true);

      const existingSlots = new Map();
      for (const slot of svg.querySelectorAll('[data-badge-for]')) {
        const id = slot.getAttribute('data-badge-for');
        existingSlots.set(id, slot);
        if (!badgeMap.has(id)) {
          slot.replaceChildren();
          slot.classList.remove('lab-badge', 'is-hot', 'is-bad');
        }
      }

      let badgesLayer = svg.querySelector('[data-badges]');
      for (const [id, entry] of badgeMap.entries()) {
        let slot = existingSlots.get(id);
        if (!slot) {
          const anchor = estimateBadgeAnchor(svg, id);
          if (!anchor) continue;
          if (!badgesLayer) {
            badgesLayer = svgEl(doc, 'g', { 'data-badges': '' });
            svg.appendChild(badgesLayer);
          }
          slot = svgEl(doc, 'g', {
            'data-badge-for': id,
            'data-auto-badge': '1',
            transform: `translate(${Math.round(anchor[0])}, ${Math.round(anchor[1])})`,
          });
          badgesLayer.appendChild(slot);
        }

        slot.classList.add('lab-badge');
        const info = entry.info && typeof entry.info === 'object' ? entry.info : {};
        slot.classList.toggle('is-hot', Boolean(info.hot || state.focusNode === id));
        slot.classList.toggle('is-bad', Boolean(info.bad));

        const rect = svgEl(doc, 'rect', { class: 'lab-badge-bg', 'data-badge-bg': '1', y: '-11', height: '22', rx: '6' });
        const textNode = svgEl(doc, 'text', { class: 'lab-badge-text', x: '0', y: '4', 'text-anchor': 'middle' }, entry.txt);
        slot.replaceChildren(rect, textNode);

        let textW = 0;
        try { if (textNode.getComputedTextLength) textW = textNode.getComputedTextLength(); } catch (e) { textW = 0; }
        const w = Math.max(42, Math.ceil((textW > 0 ? textW : entry.txt.length * 7.2) + 14));
        rect.setAttribute('x', String(-w / 2));
        rect.setAttribute('width', String(w));
      }
    }

    function syncSvg(evalRes) {
      const m = getModeDef(spec, state.mode);
      if (!m) return;

      if (lastModeKey !== state.mode) {
        dom.svgHost.innerHTML = m.svg || '';
        lastSvgEl = dom.svgHost.querySelector('svg');
        if (lastSvgEl) {
          if (!lastSvgEl.getAttribute('role')) lastSvgEl.setAttribute('role', 'img');
          if (!lastSvgEl.getAttribute('aria-label') && (m.ariaLabel || spec.title)) {
            lastSvgEl.setAttribute('aria-label', m.ariaLabel || spec.title);
          }
          bindSvgHooks(lastSvgEl);
        }
        lastModeKey = state.mode;
      }

      const svg = lastSvgEl;
      if (!svg) return;

      for (const elNode of svg.querySelectorAll('[data-node]')) {
        const id = elNode.getAttribute('data-node');
        const info = evalRes && evalRes.nodes ? evalRes.nodes[id] : null;
        const isObj = info && typeof info === 'object';
        elNode.classList.toggle('is-hot', Boolean((isObj && info.hot) || state.focusNode === id));
        elNode.classList.toggle('is-bad', Boolean(isObj && info.bad));
        elNode.classList.toggle('is-dim', Boolean(isObj && info.dim));
      }

      for (const elBr of svg.querySelectorAll('[data-branch]')) {
        const id = elBr.getAttribute('data-branch');
        const info = evalRes && evalRes.branches ? evalRes.branches[id] : null;
        const isObj = info && typeof info === 'object';
        const rev = Boolean(isObj && (info.dir === -1 || info.dir === 'rev'));
        elBr.classList.toggle('is-hot', info === true || Boolean(isObj && (info.hot || info.active)));
        elBr.classList.toggle('is-bad', Boolean(isObj && info.bad));
        elBr.classList.toggle('is-dim', Boolean(isObj && info.dim));
        elBr.classList.toggle('is-rev', rev);
        if (isObj && info.dir !== undefined) elBr.setAttribute('data-dir', rev ? 'rev' : 'fwd');
      }

      for (const elItem of svg.querySelectorAll('[data-elem]')) {
        const id = elItem.getAttribute('data-elem');
        const isOff = state.disabledElems.includes(id);
        const info = evalRes && evalRes.elems ? evalRes.elems[id] : null;
        elItem.classList.toggle('is-off', isOff);
        elItem.classList.toggle('is-hot', Boolean(!isOff && info && info.hot));
        elItem.classList.toggle('is-bad', Boolean(info && info.bad));
        elItem.classList.toggle('is-dim', Boolean(info && info.dim));
        elItem.setAttribute('aria-pressed', isOff ? 'false' : 'true');
      }

      const portDefs = getPortsForMode(spec, state.mode);
      for (const portEl of svg.querySelectorAll('[data-port]')) {
        const id = portEl.getAttribute('data-port');
        const val = state.ports[id];
        const portDef = portDefs.find((p) => p.id === id);
        const opt = portDef ? portDef.options.find((o) => o.id === val) : null;
        const info = evalRes && evalRes.ports ? evalRes.ports[id] : null;
        portEl.classList.toggle('is-bad', Boolean(info && info.bad));
        portEl.classList.toggle('is-hot', Boolean(info && (info.hot || info.ok)));
        portEl.setAttribute('data-port-state', val != null ? String(val) : '');

        for (const viewEl of portEl.querySelectorAll('[data-port-view]')) {
          if (viewEl.getAttribute('data-port-view') === val) {
            viewEl.removeAttribute('hidden');
            viewEl.removeAttribute('display');
          } else {
            viewEl.setAttribute('hidden', '');
            viewEl.setAttribute('display', 'none');
          }
        }
        const chip = portEl.querySelector('.port-chip');
        if (chip && opt) {
          const chipText = chip.tagName && chip.tagName.toLowerCase() === 'text'
            ? chip
            : chip.querySelector('text');
          if (chipText) chipText.textContent = opt.shortLabel || opt.label;
          else chip.textContent = opt.shortLabel || opt.label;
        }
      }

      const curStep = Number(state.causalStep) || 0;
      for (const cEl of svg.querySelectorAll('[data-causal-step]')) {
        const nums = (cEl.getAttribute('data-causal-step') || '').split(',').map((s) => Number(s.trim())).filter(Number.isFinite);
        if (curStep <= 0 || nums.length === 0) {
          cEl.classList.remove('is-hot', 'is-done', 'is-dim');
        } else {
          const isCur = nums.includes(curStep);
          const isDone = !isCur && nums.some((n) => n < curStep);
          cEl.classList.toggle('is-hot', isCur);
          cEl.classList.toggle('is-done', isDone);
          cEl.classList.toggle('is-dim', !isCur && !isDone);
        }
      }

      syncBadges(svg, evalRes);
      updateSvgPortAria();
    }

    function renderPredictCard(evalRes, focusedControl, verifiedNow) {
      const p = spec.predict;
      const slot = dom.predictSlot;
      if (!slot) return;
      if (!matchesMode(p, state.mode)) {
        slot.replaceChildren();
        return;
      }
      const sidebar = !state.narrow && state.rightOpen && dom.panelRightInner;
      const destination = sidebar || dom.stageEl;
      if (slot.parentElement !== destination) destination.prepend(slot);

      function button(label, className, control, action, attrs) {
        const btn = el(doc, 'button', {
          type: 'button', className, 'data-predict-focus': control, ...attrs,
        }, label);
        btn.addEventListener('click', () => dispatch(action));
        return btn;
      }

      if (state.predictDismissed || (!sidebar && !state.predictExpanded)) {
        const open = button('예측해 보기', 'predict-btn predict-open', 'open',
          { type: 'OPEN_PREDICT' }, { 'aria-expanded': 'false' });
        slot.replaceChildren(open);
        if (focusedControl) open.focus({ preventScroll: true });
        return;
      }

      const card = el(doc, 'section', { className: 'predict-card', 'aria-label': '예측 확인' });
      card.appendChild(el(doc, 'p', { className: 'predict-prompt' }, p.prompt));
      const optsRow = el(doc, 'div', { className: 'predict-opts' });
      for (const [index, rawOpt] of p.options.entries()) {
        const oid = typeof rawOpt === 'object' ? rawOpt.id : rawOpt;
        const olabel = typeof rawOpt === 'object' ? rawOpt.label : rawOpt;
        optsRow.appendChild(button(olabel, 'predict-btn', `choice-${index}`,
          { type: 'ANSWER_PREDICT', choice: oid }, { 'aria-pressed': String(state.predictChoice === oid) }));
      }
      card.appendChild(optsRow);

      if (state.predictVerified) {
        const correct = state.predictChoice === p.answerId;
        const feedback = el(doc, 'div', {
          className: `predict-feedback${correct ? '' : ' is-wrong'}`,
          'data-predict-focus': 'result', tabindex: '-1',
        });
        feedback.appendChild(el(doc, 'b', null, correct ? '예측과 같아요.' : '예측과 달랐어요.'));
        if (p.check) {
          let before;
          if (p.check.before) {
            const baseline = cloneState(state);
            applyPatch(spec, baseline, p.check.before);
            before = evaluate(baseline);
          }
          const readings = el(doc, 'ul', { className: 'predict-readings' });
          for (const id of p.check.tiles) {
            const tile = (evalRes.tiles || []).find((entry) => (entry.id ?? entry.label) === id);
            if (!tile) continue;
            const prior = before?.tiles?.find((entry) => (entry.id ?? entry.label) === id);
            const value = tile.val ?? tile.value;
            const reading = prior ? `${prior.val ?? prior.value} → ${value}` : value;
            readings.appendChild(el(doc, 'li', null, `${tile.label} · ${reading}`));
          }
          if (readings.children.length) feedback.appendChild(readings);
        }
        if (p.explain) feedback.appendChild(el(doc, 'p', null, p.explain));
        card.appendChild(feedback);
      }
      const actions = el(doc, 'div', { className: 'predict-actions' });
      if (!state.predictVerified) {
        const verify = button('회로에서 확인', 'predict-btn predict-verify', 'verify', { type: 'VERIFY_PREDICT' });
        verify.disabled = state.predictChoice === null;
        actions.appendChild(verify);
      }
      actions.appendChild(button(state.predictVerified ? '예측 접기' : '바로 실험하기', 'predict-skip', 'skip',
        { type: 'DISMISS_PREDICT' }));
      card.appendChild(actions);
      slot.replaceChildren(card);
      if (verifiedNow) card.querySelector('[data-predict-focus="result"]').focus();
      else if (focusedControl) {
        const target = focusedControl === 'open' ? card.querySelector('.predict-opts button')
          : card.querySelector(`[data-predict-focus="${focusedControl}"]`);
        (target || card.querySelector('.predict-opts button'))?.focus({ preventScroll: true });
      }
    }

    function renderPlot(evalRes) {
      const pd = evalRes && evalRes.plotData;
      if (!pd) {
        dom.plotSlot.replaceChildren();
        return;
      }
      const wrap = el(doc, 'section', { className: 'plot-wrap', 'aria-label': pd.title || '근사 비교 그래프' });
      const head = el(doc, 'div', { className: 'plot-head' });
      const legend = el(doc, 'div', { className: 'plot-legend' });

      const exactItem = el(doc, 'span');
      exactItem.appendChild(el(doc, 'span', { className: 'plot-sw exact' }));
      exactItem.appendChild(el(doc, 'span', null, pd.exactLabel || '정확식 (실선)'));
      legend.appendChild(exactItem);

      if (Array.isArray(pd.approx) && pd.approx.length > 0) {
        const approxItem = el(doc, 'span');
        approxItem.appendChild(el(doc, 'span', { className: 'plot-sw approx' }));
        approxItem.appendChild(el(doc, 'span', null, pd.approxLabel || '근사식 (점선)'));
        legend.appendChild(approxItem);
      }
      head.appendChild(legend);

      if (typeof pd.errPct === 'number' && Number.isFinite(pd.errPct)) {
        const threshold = pd.thresholdPct !== undefined ? pd.thresholdPct : 10;
        const broken = pd.errPct >= threshold;
        head.appendChild(el(doc, 'span', {
          className: `err-badge${broken ? ' is-bad' : ''}`,
        }, `오차 ${pd.errPct.toFixed(1)}% · ${broken ? `${threshold}% 초과 (근사 붕괴)` : `${threshold}% 이내`}`));
      }
      wrap.appendChild(head);

      const plotSvg = buildPlotSvg(doc, pd);
      if (plotSvg) wrap.appendChild(plotSvg);
      dom.plotSlot.replaceChildren(wrap);
    }

    function buildLeftPanel() {
      const inner = dom.panelLeftInner;
      if (!inner) return;
      inner.replaceChildren();

      const pHead = el(doc, 'div', { className: 'panel-head' });
      pHead.appendChild(el(doc, 'h2', null, '조작'));
      const closeBtn = el(doc, 'button', { type: 'button', className: 'text-btn' }, '닫기');
      closeBtn.addEventListener('click', () => dispatch({ type: 'CLOSE_DRAWER' }));
      pHead.appendChild(closeBtn);
      inner.appendChild(pHead);

      let sections = 0;

      const toggles = getTogglesForMode(spec, state.mode);
      if (toggles.length > 0) {
        sections++;
        const grid = el(doc, 'div', { className: 'opt' });
        for (const t of toggles) {
          const btn = el(doc, 'button', {
            type: 'button', className: 'btn', 'data-toggle-key': t.key,
            'aria-pressed': state.toggles[t.key] ? 'true' : 'false',
          });
          btn.appendChild(el(doc, 'span', { className: 'box', 'aria-hidden': 'true' }));
          btn.appendChild(el(doc, 'span', null, t.label));
          btn.addEventListener('click', () => dispatch({ type: 'TOGGLE_OPT', key: t.key }));
          grid.appendChild(btn);
        }
        addPanelSection(doc, inner, '보기 옵션', grid);
      }

      const cSteps = getCausalStepsForMode(spec, state.mode);
      if (cSteps.length > 0) {
        sections++;
        const wrap = el(doc, 'div');
        const bar = el(doc, 'div', { className: 'causal-bar' });
        const pulseBtn = el(doc, 'button', { type: 'button', className: 'btn', 'data-causal-action': 'pulse', 'aria-pressed': 'false' }, '자동 맥동');
        const nextBtn = el(doc, 'button', { type: 'button', className: 'btn', 'data-causal-action': 'next' }, '다음 박자');
        const resetBtn = el(doc, 'button', { type: 'button', className: 'btn', 'data-causal-action': 'reset' }, '초기화');

        nextBtn.addEventListener('click', () => { stopPulse(); pulseBtn.setAttribute('aria-pressed', 'false'); dispatch({ type: 'PULSE_CAUSAL', delta: 1 }); });
        resetBtn.addEventListener('click', () => { stopPulse(); pulseBtn.setAttribute('aria-pressed', 'false'); dispatch({ type: 'PULSE_CAUSAL', reset: true }); });
        pulseBtn.addEventListener('click', () => {
          if (pulseTimer !== null) {
            stopPulse();
            pulseBtn.setAttribute('aria-pressed', 'false');
            return;
          }
          if (isReduceMotion()) {
            dispatch({ type: 'PULSE_CAUSAL', delta: 1 });
            return;
          }
          pulseTimer = setInterval(() => dispatch({ type: 'PULSE_CAUSAL', delta: 1 }), 900);
          pulseBtn.setAttribute('aria-pressed', 'true');
          dispatch({ type: 'PULSE_CAUSAL', delta: 1 });
        });

        bar.appendChild(nextBtn);
        bar.appendChild(pulseBtn);
        bar.appendChild(resetBtn);
        wrap.appendChild(bar);

        const list = el(doc, 'div', { className: 'steps' });
        for (let i = 0; i < cSteps.length; i++) {
          const cs = cSteps[i];
          const btn = el(doc, 'button', {
            type: 'button', className: 'btn', 'data-causal-id': String(cs.id),
            'aria-pressed': state.causalStep === cs.id ? 'true' : 'false',
          });
          btn.appendChild(el(doc, 'span', { className: 'step-num num' }, String(i + 1)));
          const txt = el(doc, 'span', { className: 'step-txt' });
          txt.appendChild(el(doc, 'b', null, cs.label));
          if (cs.detail) txt.appendChild(el(doc, 'span', null, cs.detail));
          btn.appendChild(txt);
          btn.addEventListener('click', () => {
            stopPulse();
            pulseBtn.setAttribute('aria-pressed', 'false');
            dispatch({ type: 'PULSE_CAUSAL', step: cs.id });
          });
          list.appendChild(btn);
        }
        wrap.appendChild(list);
        addPanelSection(doc, inner, '+Δv 인과 도미노', wrap);
      }

      const portDefs = getPortsForMode(spec, state.mode);
      if (portDefs.length > 0) {
        sections++;
        const list = el(doc, 'div', { className: 'port-controls' });
        for (const p of portDefs) {
          const grp = el(doc, 'div', { className: 'port-group' });
          grp.appendChild(el(doc, 'span', { className: 'port-group-label' }, p.label));
          const row = el(doc, 'div', { className: 'port-choices' });
          for (const opt of p.options) {
            const btn = el(doc, 'button', {
              type: 'button', className: 'btn', 'data-port-ctrl': p.id, 'data-port-opt': opt.id,
              'aria-pressed': state.ports[p.id] === opt.id ? 'true' : 'false',
            }, opt.label);
            btn.addEventListener('click', () => { closePortPopover(false); dispatch({ type: 'SET_PORT', portId: p.id, value: opt.id }); });
            row.appendChild(btn);
          }
          grp.appendChild(row);
          list.appendChild(grp);
        }
        addPanelSection(doc, inner, '포트 종단 조립', list);
      }

      const elems = getElemsForMode(spec, state.mode);
      if (elems.length > 0) {
        sections++;
        const list = el(doc, 'div', { className: 'elem-controls' });
        for (const item of elems) {
          const btn = el(doc, 'button', {
            type: 'button', className: 'btn', 'data-elem-ctrl': item.id,
            'aria-pressed': state.disabledElems.includes(item.id) ? 'false' : 'true',
          });
          btn.appendChild(el(doc, 'span', { className: 'box', 'aria-hidden': 'true' }));
          btn.appendChild(el(doc, 'span', null, item.label));
          btn.addEventListener('click', () => dispatch({ type: 'TOGGLE_ELEM', id: item.id }));
          list.appendChild(btn);
        }
        addPanelSection(doc, inner, '소자 포함 여부', list);
      }

      const params = getParamsForMode(spec, state.mode);
      if (params.length > 0) {
        sections++;
        const list = el(doc, 'div', { className: 'slider-list' });
        for (const p of params) {
          const row = el(doc, 'div', { className: 'slider-row' });
          const head = el(doc, 'div', { className: 'slider-head' });
          const inputId = `param-${p.key}`;
          head.appendChild(el(doc, 'label', { for: inputId }, p.label || p.key));
          head.appendChild(el(doc, 'span', { className: 'slider-val', 'data-param-val': p.key }, formatParamValue(p, state.params[p.key])));
          row.appendChild(head);

          const isLog = p.scale === 'log' && p.min > 0 && p.max > p.min;
          const rangeAttrs = isLog
            ? {
                id: inputId, type: 'range', min: '0', max: '1000', step: '1',
                'data-param-key': p.key, 'data-param-log': '1',
                value: String(Math.round(1000 * Math.log(state.params[p.key] / p.min) / Math.log(p.max / p.min))),
              }
            : {
                id: inputId, type: 'range', min: String(p.min), max: String(p.max),
                step: String(p.step !== undefined ? p.step : 'any'),
                'data-param-key': p.key, value: String(state.params[p.key]),
              };
          const slider = el(doc, 'input', rangeAttrs);
          slider.addEventListener('input', (e) => {
            const raw = Number(e.target.value);
            dispatch({ type: 'SET_PARAM', key: p.key, value: isLog ? p.min * Math.pow(p.max / p.min, raw / 1000) : raw });
          });
          row.appendChild(slider);
          list.appendChild(row);
        }
        addPanelSection(doc, inner, '소자·입력 값', list);
      }

      const presets = getPresetsForMode(spec, state.mode);
      if (presets.length > 0) {
        sections++;
        const grid = el(doc, 'div', { className: 'preset-grid' });
        for (const pr of presets) {
          const btn = el(doc, 'button', { type: 'button', className: 'btn', 'data-preset-id': pr.id }, pr.label);
          btn.addEventListener('click', () => dispatch({ type: 'APPLY_PRESET', id: pr.id }));
          grid.appendChild(btn);
        }
        addPanelSection(doc, inner, '대표 설정', grid);
      }

      const steps = getStepsForMode(spec, state.mode);
      if (steps.length > 0) {
        sections++;
        const wrap = el(doc, 'div');
        const list = el(doc, 'div', { className: 'steps' });
        for (let k = 0; k < steps.length; k++) {
          const { s, i } = steps[k];
          const btn = el(doc, 'button', {
            type: 'button', className: 'btn', 'data-step-idx': String(i),
            'aria-pressed': state.step === i ? 'true' : 'false',
          });
          btn.appendChild(el(doc, 'span', { className: 'step-num num' }, String(k + 1)));
          const txt = el(doc, 'span', { className: 'step-txt' });
          txt.appendChild(el(doc, 'b', null, s.title || s.label || `단계 ${k + 1}`));
          if (s.who || s.subtitle) txt.appendChild(el(doc, 'span', null, s.who || s.subtitle));
          btn.appendChild(txt);
          btn.addEventListener('click', () => dispatch({ type: 'PICK_STEP', index: i }));
          list.appendChild(btn);
        }
        wrap.appendChild(list);
        wrap.appendChild(el(doc, 'div', { className: 'detail', 'data-step-detail': '', 'aria-live': 'polite', hidden: true }));
        addPanelSection(doc, inner, '단계별 살펴보기', wrap);
      }

      if (sections === 0) {
        inner.appendChild(el(doc, 'p', { className: 'sub' }, '이 보기에는 추가 조작이 없어요.'));
      }
      leftBuiltMode = state.mode;
    }

    function syncStepDetail() {
      if (!dom.panelLeftInner) return;
      const detailEl = dom.panelLeftInner.querySelector('[data-step-detail]');
      if (!detailEl) return;
      const s = state.step >= 0 && Array.isArray(spec.steps) ? spec.steps[state.step] : null;
      if (s && (s.text || s.detail)) {
        detailEl.removeAttribute('hidden');
        detailEl.textContent = s.text || s.detail;
      } else {
        detailEl.setAttribute('hidden', '');
        detailEl.textContent = '';
      }
    }

    function syncLeftPanelInPlace() {
      if (!dom.panelLeftInner) return;
      if (leftBuiltMode !== state.mode) {
        buildLeftPanel();
        syncStepDetail();
        return;
      }
      const inner = dom.panelLeftInner;
      for (const btn of inner.querySelectorAll('[data-toggle-key]')) {
        btn.setAttribute('aria-pressed', state.toggles[btn.getAttribute('data-toggle-key')] ? 'true' : 'false');
      }
      for (const btn of inner.querySelectorAll('[data-causal-id]')) {
        btn.setAttribute('aria-pressed', String(state.causalStep) === btn.getAttribute('data-causal-id') ? 'true' : 'false');
      }
      const pulseBtn = inner.querySelector('[data-causal-action="pulse"]');
      if (pulseBtn) pulseBtn.setAttribute('aria-pressed', pulseTimer !== null ? 'true' : 'false');
      for (const btn of inner.querySelectorAll('[data-port-ctrl]')) {
        const match = state.ports[btn.getAttribute('data-port-ctrl')] === btn.getAttribute('data-port-opt');
        btn.setAttribute('aria-pressed', match ? 'true' : 'false');
      }
      for (const btn of inner.querySelectorAll('[data-elem-ctrl]')) {
        btn.setAttribute('aria-pressed', state.disabledElems.includes(btn.getAttribute('data-elem-ctrl')) ? 'false' : 'true');
      }
      for (const p of getParamsForMode(spec, state.mode)) {
        const val = state.params[p.key];
        const labelEl = findHookEl(inner, 'data-param-val', p.key);
        if (labelEl) labelEl.textContent = formatParamValue(p, val);
        const inputEl = findHookEl(inner, 'data-param-key', p.key);
        if (inputEl) {
          inputEl.value = inputEl.hasAttribute('data-param-log') && p.min > 0 && p.max > p.min
            ? String(Math.round(1000 * Math.log(val / p.min) / Math.log(p.max / p.min)))
            : String(val);
        }
      }
      for (const btn of inner.querySelectorAll('[data-step-idx]')) {
        btn.setAttribute('aria-pressed', state.step === Number(btn.getAttribute('data-step-idx')) ? 'true' : 'false');
      }
      syncStepDetail();
    }

    function renderRightPanel(evalRes) {
      const inner = dom.panelRightInner;
      if (!inner) return;
      inner.replaceChildren();

      const pHead = el(doc, 'div', { className: 'panel-head' });
      pHead.appendChild(el(doc, 'h2', null, '설명'));
      const closeBtn = el(doc, 'button', { type: 'button', className: 'text-btn' }, '닫기');
      closeBtn.addEventListener('click', () => dispatch({ type: 'CLOSE_DRAWER' }));
      pHead.appendChild(closeBtn);
      inner.appendChild(pHead);

      if (evalRes && Array.isArray(evalRes.tiles) && evalRes.tiles.length > 0) {
        const grid = el(doc, 'div', { className: `tiles${evalRes.tiles.length === 3 ? ' three' : ''}` });
        for (const t of evalRes.tiles) {
          const tile = el(doc, 'div', { className: 'tile' });
          tile.appendChild(el(doc, 'b', { className: 'num' }, t.val ?? t.value ?? ''));
          tile.appendChild(el(doc, 'span', null, t.label ?? ''));
          grid.appendChild(tile);
        }
        addPanelSection(doc, inner, '수치 요약', grid);
      }

      if (evalRes && evalRes.diagnosis) {
        const diag = typeof evalRes.diagnosis === 'string' ? { kind: 'info', text: evalRes.diagnosis } : evalRes.diagnosis;
        const kind = diag.kind || (diag.singular ? 'bad' : 'info');
        const box = el(doc, 'div', {
          className: `diagnosis${kind === 'ok' ? ' is-ok' : kind === 'warn' ? ' is-warn' : kind === 'bad' ? ' is-bad' : ''}`,
          'aria-live': 'polite',
        });
        if (diag.title) box.appendChild(el(doc, 'b', null, diag.title));
        box.appendChild(el(doc, 'span', null, diag.text || diag.reason || ''));
        addPanelSection(doc, inner, '회로 진단', box);
      }

      const eqs = [];
      if (evalRes && evalRes.formula) eqs.push(typeof evalRes.formula === 'string' ? { tex: evalRes.formula } : evalRes.formula);
      if (evalRes && Array.isArray(evalRes.equations)) {
        for (const eq of evalRes.equations) eqs.push(typeof eq === 'string' ? { tex: eq } : eq);
      }
      if (eqs.length > 0) {
        const box = el(doc, 'div', { className: 'formula-box' });
        for (const eq of eqs) {
          const item = el(doc, 'div', { className: 'eq-item' });
          if (eq.name || eq.title) item.appendChild(el(doc, 'span', { className: 'eq-name' }, eq.name || eq.title));
          item.appendChild(el(doc, 'div', null, eq.tex || eq.text || ''));
          box.appendChild(item);
        }
        addPanelSection(doc, inner, '핵심 수식', box);
      }

      const activeCausal = getCausalStepsForMode(spec, state.mode).find((c) => c.id === state.causalStep);
      const summaryText = (evalRes && evalRes.summary) || (activeCausal && activeCausal.detail) || '';
      if (summaryText) {
        addPanelSection(doc, inner, '지금 일어나는 일', el(doc, 'p', { className: 'summary-box', 'aria-live': 'polite' }, summaryText));
      }

      const mistakes = getMistakesForMode(spec, state.mode);
      if (mistakes.length > 0) {
        const sec = el(doc, 'div', { className: 'sec warn' });
        sec.appendChild(el(doc, 'h3', { className: 'sec-title' }, '꼭 기억해요'));
        for (const mk of mistakes) {
          const item = el(doc, 'div', { className: 'mistake' });
          item.appendChild(el(doc, 'b', null, mk.title || ''));
          item.appendChild(el(doc, 'span', null, mk.text || ''));
          sec.appendChild(item);
        }
        inner.appendChild(sec);
      }
    }

    function syncTopbarAndPanels() {
      try {
        doc.documentElement.setAttribute('data-theme', state.theme);
        if (doc.documentElement.dataset) doc.documentElement.dataset.theme = state.theme;
      } catch (e) {}

      if (dom.themeBtn) {
        const lbl = state.theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환';
        dom.themeBtn.setAttribute('aria-label', lbl);
        dom.themeBtn.setAttribute('title', lbl);
      }

      if (dom.modeSegEl) {
        const modes = getModes(spec);
        if (modes.length <= 1) {
          dom.modeSegEl.setAttribute('hidden', '');
          dom.modeSegEl.replaceChildren();
        } else {
          dom.modeSegEl.removeAttribute('hidden');
          dom.modeSegEl.replaceChildren();
          for (const m of modes) {
            const btn = el(doc, 'button', {
              type: 'button', 'aria-pressed': m.key === state.mode ? 'true' : 'false',
            }, m.label || m.key);
            btn.addEventListener('click', () => dispatch({ type: 'SET_MODE', mode: m.key }));
            dom.modeSegEl.appendChild(btn);
          }
        }
      }

      rootEl.setAttribute('data-drawer', state.narrow ? (state.drawer || 'none') : 'none');
      const leftOn = state.narrow ? state.drawer === 'left' : state.leftOpen;
      const rightOn = state.narrow ? state.drawer === 'right' : state.rightOpen;

      if (dom.panelLeft) dom.panelLeft.classList.toggle('is-open', leftOn);
      if (dom.panelRight) dom.panelRight.classList.toggle('is-open', rightOn);
      if (dom.scrimEl) dom.scrimEl.classList.toggle('is-on', Boolean(state.narrow && state.drawer));

      for (const [btn, on] of [[dom.leftBtn, leftOn], [dom.rightBtn, rightOn]]) {
        if (!btn) continue;
        btn.setAttribute('aria-expanded', on ? 'true' : 'false');
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      }
    }

    function evaluate(snapshot) {
      try {
        return typeof spec.evaluate === 'function' ? spec.evaluate(snapshot, mna) : {};
      } catch (err) {
        if (!loggedEvalErr) {
          loggedEvalErr = true;
          if (typeof console !== 'undefined' && console.error) console.error(err);
        }
        return { diagnosis: { kind: 'bad', title: '계산 오류', text: String(err && err.message ? err.message : err) } };
      }
    }

    function render(verifiedNow = false) {
      const focusedControl = dom.predictSlot?.contains(doc.activeElement)
        ? doc.activeElement.getAttribute('data-predict-focus') : null;
      syncTopbarAndPanels();
      const evalRes = evaluate(state);
      syncSvg(evalRes);
      renderPlot(evalRes);
      syncLeftPanelInPlace();
      renderRightPanel(evalRes);
      renderPredictCard(evalRes, focusedControl, verifiedNow);
      renderMath();
    }

    function dispatch(action) {
      const next = reduceState(spec, state, action);
      if (next === state) return;
      if (['SET_MODE', 'APPLY_PRESET', 'PICK_STEP', 'VERIFY_PREDICT'].includes(action.type)) {
        stopPulse();
        closePortPopover(false);
      }
      if (['SET_PARAM', 'SET_PORT', 'TOGGLE_ELEM', 'APPLY_PRESET', 'PICK_STEP'].includes(action.type)) {
        next.predictVerified = false;
      }
      if (action.type === 'SET_THEME') {
        try {
          if (win && win.localStorage) {
            if ((next.theme === 'dark') === systemDark()) win.localStorage.removeItem('od-theme');
            else win.localStorage.setItem('od-theme', next.theme);
          }
        } catch (e) {}
      }
      state = next;
      render(action.type === 'VERIFY_PREDICT');
    }

    if (dom.leftBtn) dom.leftBtn.addEventListener('click', () => dispatch({ type: 'TOGGLE_PANEL', side: 'left', narrow: state.narrow }));
    if (dom.rightBtn) dom.rightBtn.addEventListener('click', () => dispatch({ type: 'TOGGLE_PANEL', side: 'right', narrow: state.narrow }));
    if (dom.scrimEl) dom.scrimEl.addEventListener('click', () => dispatch({ type: 'CLOSE_DRAWER' }));
    if (dom.themeBtn) dom.themeBtn.addEventListener('click', () => dispatch({ type: 'SET_THEME', theme: state.theme === 'dark' ? 'light' : 'dark' }));

    const onDocClick = (e) => {
      if (!openPortMenu) return;
      const pop = dom.stageWrap && dom.stageWrap.querySelector('.port-popover');
      if (pop && !pop.contains(e.target)) closePortPopover(false);
    };
    const onKeyDown = (e) => {
      if (e.key !== 'Escape') return;
      if (openPortMenu) {
        e.preventDefault();
        closePortPopover(true);
      } else if (state.narrow && state.drawer) {
        e.preventDefault();
        dispatch({ type: 'CLOSE_DRAWER' });
      }
    };
    const onDocReady = () => renderMath();
    let mq = null;
    const onMqChange = () => {
      const narrowNow = isNarrowViewport();
      if (narrowNow !== state.narrow) {
        state = Object.assign(cloneState(state), { narrow: narrowNow, drawer: null });
        render();
      }
    };

    try { doc.addEventListener('click', onDocClick); } catch (e) {}
    try { doc.addEventListener('keydown', onKeyDown); } catch (e) {}
    try {
      if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', onDocReady);
      if (win) win.addEventListener('load', onDocReady);
    } catch (e) {}
    try {
      if (win && win.matchMedia) {
        mq = win.matchMedia('(max-width: 1023.98px)');
        if (mq && mq.addEventListener) mq.addEventListener('change', onMqChange);
      }
    } catch (e) {}

    render();

    const controller = {
      getState: () => cloneState(state),
      setMode: (mode) => dispatch({ type: 'SET_MODE', mode }),
      pickStep: (index) => dispatch({ type: 'PICK_STEP', index }),
      setParam: (key, value) => dispatch({ type: 'SET_PARAM', key, value }),
      applyPreset: (id) => dispatch({ type: 'APPLY_PRESET', id }),
      toggleElem: (id) => dispatch({ type: 'TOGGLE_ELEM', id }),
      setPort: (portId, value) => dispatch({ type: 'SET_PORT', portId, value }),
      pulseCausal: (step) => dispatch(step === undefined ? { type: 'PULSE_CAUSAL', delta: 1 } : { type: 'PULSE_CAUSAL', step }),
      answerPredict: (choice) => dispatch({ type: 'ANSWER_PREDICT', choice }),
      dismissPredict: () => dispatch({ type: 'DISMISS_PREDICT' }),
      setTheme: (theme) => dispatch({ type: 'SET_THEME', theme }),
      togglePanel: (side) => dispatch({ type: 'TOGGLE_PANEL', side, narrow: state.narrow }),
      closeDrawer: () => dispatch({ type: 'CLOSE_DRAWER' }),
      renderMath,
      listProbeStates: () => buildProbeStates(spec),
      applyProbeState: (probeState) => {
        if (!probeState || typeof probeState !== 'object') return;
        stopPulse();
        closePortPopover(false);
        const init = createInitialState(spec);
        const merged = Object.assign(init, cloneState({
          ...init,
          ...probeState,
          params: Object.assign({}, init.params, probeState.params || {}),
          ports: Object.assign({}, init.ports, probeState.ports || {}),
          toggles: Object.assign({}, init.toggles, probeState.toggles || {}),
          disabledElems: Array.isArray(probeState.disabledElems) ? probeState.disabledElems : init.disabledElems,
          theme: state.theme,
          drawer: (probeState.drawer === 'left' || probeState.drawer === 'right') ? probeState.drawer : state.drawer,
          leftOpen: probeState.leftOpen !== undefined ? probeState.leftOpen : state.leftOpen,
          rightOpen: probeState.rightOpen !== undefined ? probeState.rightOpen : state.rightOpen,
        }));
        merged.narrow = state.narrow;
        state = merged;
        render();
      },
      destroy: () => {
        stopPulse();
        try { doc.removeEventListener('click', onDocClick); } catch (e) {}
        try { doc.removeEventListener('keydown', onKeyDown); } catch (e) {}
        try {
          if (win) win.removeEventListener('load', onDocReady);
          if (mq && mq.removeEventListener) mq.removeEventListener('change', onMqChange);
        } catch (e) {}
      },
    };

    if (win) win.__EC2_LAB__ = controller;
    return controller;
  }

  return { createInitialState, reduceState, buildProbeStates, mount };
});
