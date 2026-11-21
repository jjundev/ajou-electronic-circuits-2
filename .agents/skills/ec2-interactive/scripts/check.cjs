// Static and dynamic contract checker for v2 lab.js files.
// Usage: node check.cjs <lab.js>   → prints "ok" (exit 0) or one error per line (exit 1); usage error exits 2.
// check(srcFile) returns { ok, errors: Array<{ code, message, ... }>, details: string[] }.
const fs = require('node:fs');
const path = require('node:path');
const { loadLab, ALLOWED_CDNS } = require('./build.cjs');
const EC2MNA = require('../assets/mna.js');
const { createInitialState, reduceState, buildProbeStates } = require('../assets/lab-runtime.js');

const ALLOWED_CDN_SET = new Set(ALLOWED_CDNS);
const SVG_XMLNS_URIS = new Set(['http://www.w3.org/2000/svg', 'http://www.w3.org/1999/xlink']);
const VALID_ARCHETYPES = new Set(['probe', 'bench', 'approx']);
const URL_RE = /https?:\/\/[^\s"'`<>)]+/g;
const HEX_IN_SVG_RE = /(?<!&|url\(|href=["'])#[0-9a-fA-F]{3,8}\b/g;
const PLAIN_SUBSCRIPT_RE = /[A-Za-z]_(?:\{[A-Za-z0-9,]+\}|[A-Za-z0-9])/;
const LATEX_IN_SVG_TEXT_RE = /\$|\\[\(\[]/;
const NON_FINITE_STRING_RE = /\b(?:NaN|Infinity)\b/;

function isNonEmptyString(v) {
  return typeof v === 'string' && v.trim().length > 0;
}

function matchesMode(item, modeKey) {
  if (!item || typeof item !== 'object') return false;
  if (item.mode !== undefined) return item.mode === modeKey;
  if (Array.isArray(item.modes)) return item.modes.includes(modeKey);
  return true;
}

function collectModeList(spec, modeObj, propName) {
  if (Array.isArray(modeObj && modeObj[propName])) return modeObj[propName];
  if (Array.isArray(spec && spec[propName])) return spec[propName].filter((item) => matchesMode(item, modeObj.key));
  return [];
}

function hasValidViewBox(modeObj) {
  if (typeof modeObj.svg !== 'string') return false;
  const inline = modeObj.svg.match(/<svg\b[^>]*\bviewBox\s*=\s*(?:"([^"]*)"|'([^']*)')/i);
  const vbRaw = inline ? (inline[1] ?? inline[2]) : null;
  if (!isNonEmptyString(vbRaw)) return false;
  const nums = vbRaw.trim().split(/[\s,]+/).map(Number);
  return nums.length === 4 && nums.every(Number.isFinite) && nums[2] > 0 && nums[3] > 0;
}

function extractSvgHooks(svg) {
  const nodes = new Set();
  const branches = new Set();
  const elems = new Set();
  const ports = new Set();
  const causalSteps = new Set();

  for (const m of String(svg || '').matchAll(/\bdata-(node|branch|elem|port|causal-step)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)) {
    const kind = m[1];
    const val = (m[2] !== undefined ? m[2] : m[3] || '').trim();
    if (!val) continue;
    if (kind === 'node') nodes.add(val);
    else if (kind === 'branch') branches.add(val);
    else if (kind === 'elem') elems.add(val);
    else if (kind === 'port') ports.add(val);
    else if (kind === 'causal-step') {
      for (const tok of val.split(',')) {
        const s = tok.trim();
        if (s) causalSteps.add(s);
      }
    }
  }
  return { nodes, branches, elems, ports, causalSteps };
}

function checkExternalUrls(text, sourceLabel, add) {
  for (const m of String(text || '').matchAll(URL_RE)) {
    const url = m[0];
    if (!ALLOWED_CDN_SET.has(url) && !SVG_XMLNS_URIS.has(url)) {
      add('EXTERNAL_URL', `Disallowed external URL in ${sourceLabel}: ${url}`, { url, source: sourceLabel });
    }
  }
}

function checkSchema(spec, add) {
  if (!isNonEmptyString(spec.id)) {
    add('SCHEMA_INVALID', 'spec.id must be a non-empty string');
  }
  if (!isNonEmptyString(spec.title)) {
    add('SCHEMA_INVALID', 'spec.title must be a non-empty string');
  }
  if (!VALID_ARCHETYPES.has(spec.archetype)) {
    add('SCHEMA_INVALID', `spec.archetype must be one of probe, bench, approx (got ${JSON.stringify(spec.archetype)})`);
  }
  if (typeof spec.evaluate !== 'function') {
    add('SCHEMA_INVALID', 'spec.evaluate must be a function');
  }
  if (!Array.isArray(spec.modes) || spec.modes.length === 0) {
    add('SCHEMA_INVALID', 'spec.modes must be a non-empty array');
  } else {
    const modeKeys = new Set();
    for (let i = 0; i < spec.modes.length; i++) {
      const m = spec.modes[i];
      if (!m || typeof m !== 'object') {
        add('SCHEMA_INVALID', `modes[${i}] must be an object`);
        continue;
      }
      if (!isNonEmptyString(m.key)) {
        add('SCHEMA_INVALID', `modes[${i}].key must be a non-empty string`);
      } else if (modeKeys.has(m.key)) {
        add('SCHEMA_INVALID', `duplicate mode key "${m.key}"`);
      } else {
        modeKeys.add(m.key);
      }
      if (!isNonEmptyString(m.label)) {
        add('SCHEMA_INVALID', `modes[${i}].label must be a non-empty string`);
      }
      if (!isNonEmptyString(m.ariaLabel)) {
        add('SCHEMA_INVALID', `modes[${i}].ariaLabel must be a non-empty string`);
      }
      if (!isNonEmptyString(m.svg) || !/<svg\b/i.test(m.svg)) {
        add('SCHEMA_INVALID', `modes[${i}].svg must contain an <svg> element`);
      } else if (!hasValidViewBox(m)) {
        add('SCHEMA_INVALID', `modes[${i}] must provide a valid 4-number viewBox`);
      }
    }

    if (Array.isArray(spec.steps)) {
      for (let i = 0; i < spec.steps.length; i++) {
        const s = spec.steps[i];
        if (s && s.mode !== undefined && !modeKeys.has(s.mode)) {
          add('SCHEMA_INVALID', `steps[${i}].mode "${s.mode}" does not match any mode`);
        }
      }
    }
    if (Array.isArray(spec.presets)) {
      for (let i = 0; i < spec.presets.length; i++) {
        const p = spec.presets[i];
        if (p && p.mode !== undefined && !modeKeys.has(p.mode)) {
          add('SCHEMA_INVALID', `presets[${i}].mode "${p.mode}" does not match any mode`);
        }
      }
    }
  }

  if (spec.predict !== undefined && spec.predict !== null) {
    const p = spec.predict;
    if (typeof p !== 'object' || !isNonEmptyString(p.prompt) || !Array.isArray(p.options) || p.options.length === 0) {
      add('SCHEMA_INVALID', 'spec.predict must have prompt and non-empty options array');
    } else {
      const optIds = new Set();
      for (let i = 0; i < p.options.length; i++) {
        const opt = p.options[i];
        if (opt && typeof opt === 'object') {
          if (!isNonEmptyString(String(opt.id ?? '')) || !isNonEmptyString(opt.label)) {
            add('SCHEMA_INVALID', `predict.options[${i}] must have non-empty id and label`);
          } else {
            optIds.add(String(opt.id));
          }
        } else if (isNonEmptyString(String(opt ?? ''))) {
          optIds.add(String(opt));
        } else {
          add('SCHEMA_INVALID', `predict.options[${i}] must be non-empty`);
        }
      }
      if (p.answerId === undefined || p.answerId === null || !optIds.has(String(p.answerId))) {
        add('SCHEMA_INVALID', `predict.answerId (${JSON.stringify(p.answerId)}) must match an option id`);
      }
    }
  }

  if (spec.params !== undefined) {
    if (!Array.isArray(spec.params)) {
      add('SCHEMA_INVALID', 'spec.params must be an array');
    } else {
      for (let i = 0; i < spec.params.length; i++) {
        const p = spec.params[i];
        if (!p || typeof p !== 'object' || !isNonEmptyString(p.key)) {
          add('SCHEMA_INVALID', `params[${i}] must have a non-empty key`);
          continue;
        }
        if (typeof p.min !== 'number' || !Number.isFinite(p.min) || typeof p.max !== 'number' || !Number.isFinite(p.max) || p.min > p.max) {
          add('SCHEMA_INVALID', `params[${i}] (${p.key}) must have finite min <= max`);
        }
        if (p.def !== undefined && (typeof p.def !== 'number' || !Number.isFinite(p.def))) {
          add('SCHEMA_INVALID', `params[${i}] (${p.key}) def must be finite`);
        }
        if (p.scale === 'log' && (p.min <= 0 || p.max <= p.min)) {
          add('SCHEMA_INVALID', `params[${i}] (${p.key}) log scale requires 0 < min < max`);
        }
      }
    }
  }
}

function checkMistakes(spec, add) {
  if (!Array.isArray(spec.modes)) return;
  const raw = spec.mistakes;
  for (const m of spec.modes) {
    if (!m || !isNonEmptyString(m.key)) continue;
    const list = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw[m.key] : null;
    if (!Array.isArray(list) || list.length !== 3) {
      add('MISTAKES_INVALID', `mistakes.${m.key} must be an array of length 3`, { mode: m.key });
      continue;
    }
    for (let i = 0; i < list.length; i++) {
      const item = list[i];
      if (!item || typeof item !== 'object' || !isNonEmptyString(item.title) || !isNonEmptyString(item.text)) {
        add('MISTAKES_INVALID', `mistakes.${m.key}[${i}] must have non-empty title and text`, { mode: m.key, index: i });
      }
    }
  }
}

function checkSvgMode(spec, m, add) {
  if (!m || typeof m.svg !== 'string') return null;
  checkExternalUrls(m.svg, `mode ${m.key} SVG`, add);

  for (const hm of m.svg.matchAll(HEX_IN_SVG_RE)) {
    add('HEX_IN_SVG', `Hardcoded hex color ${hm[0]} in mode ${m.key} SVG`, { mode: m.key, hex: hm[0] });
  }

  for (const tm of m.svg.matchAll(/<text\b[^>]*>([\s\S]*?)<\/text>/gi)) {
    const inner = tm[1].replace(/<[^>]+>/g, '');
    if (PLAIN_SUBSCRIPT_RE.test(inner) || LATEX_IN_SVG_TEXT_RE.test(inner)) {
      add(
        'SVG_TEXT_NOTATION',
        `Invalid SVG <text> notation in mode ${m.key}: "${inner.trim()}" (use <tspan baseline-shift="sub"> without _ or $...$)`,
        { mode: m.key, text: inner.trim() }
      );
    }
  }

  const hooks = extractSvgHooks(m.svg);
  for (const p of collectModeList(spec, m, 'ports')) {
    const pid = p && p.id !== undefined ? String(p.id) : '';
    if (pid && !hooks.ports.has(pid)) {
      add('HOOK_MISSING', `Missing data-port="${pid}" in mode ${m.key} SVG`, { mode: m.key, hookType: 'port', hookId: pid });
    }
  }
  for (const e of collectModeList(spec, m, 'elems')) {
    const eid = typeof e === 'string' ? e : (e && e.id !== undefined ? String(e.id) : '');
    if (eid && !hooks.elems.has(eid)) {
      add('HOOK_MISSING', `Missing data-elem="${eid}" in mode ${m.key} SVG`, { mode: m.key, hookType: 'elem', hookId: eid });
    }
  }
  const cSteps = collectModeList(spec, m, 'causalSteps');
  for (let i = 0; i < cSteps.length; i++) {
    const cs = cSteps[i];
    const sid = cs && cs.id !== undefined ? String(cs.id) : String(i + 1);
    if (!hooks.causalSteps.has(sid)) {
      add('HOOK_MISSING', `Missing data-causal-step="${sid}" in mode ${m.key} SVG`, { mode: m.key, hookType: 'causal-step', hookId: sid });
    }
  }
  return hooks;
}

function buildTestStates(spec) {
  const list = [];
  const seen = new Set();
  const push = (label, state) => {
    const sig = JSON.stringify({
      mode: state.mode,
      step: state.step,
      params: state.params,
      ports: state.ports,
      disabledElems: state.disabledElems,
      causalStep: state.causalStep,
      predictChoice: state.predictChoice,
      predictDismissed: state.predictDismissed,
      toggles: state.toggles,
    });
    if (seen.has(sig)) return;
    seen.add(sig);
    list.push({ label, state });
  };

  const base = createInitialState(spec);
  push('초기 상태', base);

  for (const entry of buildProbeStates(spec)) {
    push(entry.label, entry.state);
  }

  for (const m of spec.modes) {
    if (!m || !isNonEmptyString(m.key)) continue;
    const modeBase = reduceState(spec, base, { type: 'SET_MODE', mode: m.key });
    const modeParams = (Array.isArray(spec.params) ? spec.params : []).filter(
      (p) => p && matchesMode(p, m.key) && typeof p.min === 'number' && Number.isFinite(p.min) && typeof p.max === 'number' && Number.isFinite(p.max)
    );
    if (modeParams.length === 0) continue;

    if (modeParams.length <= 5) {
      const combos = 1 << modeParams.length;
      for (let mask = 0; mask < combos; mask++) {
        let st = modeBase;
        const parts = [];
        for (let i = 0; i < modeParams.length; i++) {
          const p = modeParams[i];
          const val = (mask & (1 << i)) ? p.max : p.min;
          st = reduceState(spec, st, { type: 'SET_PARAM', key: p.key, value: val });
          parts.push(`${p.key}=${val}`);
        }
        push(`${m.key}:[${parts.join(',')}]`, st);
      }
    } else {
      let allMin = modeBase;
      let allMax = modeBase;
      for (const p of modeParams) {
        push(`${m.key}:${p.key}=min(${p.min})`, reduceState(spec, modeBase, { type: 'SET_PARAM', key: p.key, value: p.min }));
        push(`${m.key}:${p.key}=max(${p.max})`, reduceState(spec, modeBase, { type: 'SET_PARAM', key: p.key, value: p.max }));
        allMin = reduceState(spec, allMin, { type: 'SET_PARAM', key: p.key, value: p.min });
        allMax = reduceState(spec, allMax, { type: 'SET_PARAM', key: p.key, value: p.max });
      }
      push(`${m.key}:all-min`, allMin);
      push(`${m.key}:all-max`, allMax);
    }
  }
  return list;
}

function inspectEvalValues(val, pathStr, stateLabel, add, visited) {
  if (typeof val === 'number') {
    if (!Number.isFinite(val)) {
      add('EVAL_NON_FINITE', `Non-finite number (${val}) at ${pathStr} in "${stateLabel}"`, { state: stateLabel, path: pathStr });
    }
    return;
  }
  if (typeof val === 'string') {
    if (NON_FINITE_STRING_RE.test(val)) {
      add('EVAL_NON_FINITE', `Non-finite string "${val}" at ${pathStr} in "${stateLabel}"`, { state: stateLabel, path: pathStr });
    }
    return;
  }
  if (!val || typeof val !== 'object') return;
  if (visited.has(val)) return;
  visited.add(val);

  if (Array.isArray(val)) {
    for (let i = 0; i < val.length; i++) {
      inspectEvalValues(val[i], `${pathStr}[${i}]`, stateLabel, add, visited);
    }
    return;
  }
  for (const [k, v] of Object.entries(val)) {
    inspectEvalValues(v, `${pathStr}.${k}`, stateLabel, add, visited);
  }
}

function checkReturnedHooks(res, modeKey, hooks, add) {
  if (!hooks) return;
  const groups = [
    ['nodes', 'node', hooks.nodes],
    ['branches', 'branch', hooks.branches],
    ['elems', 'elem', hooks.elems],
    ['ports', 'port', hooks.ports],
  ];
  for (const [prop, attr, set] of groups) {
    const obj = res[prop];
    if (!obj || typeof obj !== 'object') continue;
    for (const id of Object.keys(obj)) {
      if (!set.has(id)) {
        add('HOOK_MISSING', `evaluate() returned ${prop}.${id} without data-${attr}="${id}" in mode ${modeKey} SVG`, {
          mode: modeKey, hookType: attr, hookId: id,
        });
      }
    }
  }
}

function check(srcFile) {
  const errors = [];
  const details = [];
  const seen = new Set();
  const add = (code, message, extra = {}) => {
    const key = `${code}::${message}`;
    if (seen.has(key)) return;
    seen.add(key);
    errors.push(Object.assign({ code, message }, extra));
    details.push(`${code}: ${message}`);
  };

  let rawSrc = '';
  try {
    const resolved = path.resolve(String(srcFile || ''));
    if (!fs.existsSync(resolved) || !fs.statSync(resolved).isFile()) {
      add('LOAD_ERROR', `File not found: ${srcFile}`);
      return { ok: false, errors, details };
    }
    rawSrc = fs.readFileSync(resolved, 'utf8');
  } catch (err) {
    add('LOAD_ERROR', String(err && err.message ? err.message : err));
    return { ok: false, errors, details };
  }

  checkExternalUrls(rawSrc, path.basename(srcFile), add);

  let spec;
  try {
    spec = loadLab(srcFile);
  } catch (err) {
    add('LOAD_ERROR', String(err && err.message ? err.message : err));
    return { ok: false, errors, details };
  }

  checkSchema(spec, add);
  checkMistakes(spec, add);

  const hooksByMode = new Map();
  if (Array.isArray(spec.modes)) {
    for (const m of spec.modes) {
      if (m && isNonEmptyString(m.key)) {
        hooksByMode.set(m.key, checkSvgMode(spec, m, add));
      }
    }
  }

  if (typeof spec.evaluate === 'function' && Array.isArray(spec.modes) && spec.modes.length > 0) {
    const testStates = buildTestStates(spec);
    for (const { label, state } of testStates) {
      let res;
      try {
        res = spec.evaluate(state, EC2MNA);
      } catch (err) {
        add('EVAL_THROW', `${label}: ${String(err && err.message ? err.message : err)}`, { state: label });
        continue;
      }
      if (!res || typeof res !== 'object') {
        add('EVAL_THROW', `${label}: evaluate() returned non-object`, { state: label });
        continue;
      }

      const isSingular = Boolean(res.diagnosis && res.diagnosis.singular === true);
      if (isSingular && spec.archetype !== 'bench') {
        add('EVAL_NON_FINITE', `Singular diagnosis is only allowed in bench archetype (${label})`, { state: label });
      }

      const visited = new WeakSet();
      for (const field of ['nodes', 'branches', 'tiles', 'plotData']) {
        if (res[field] !== undefined) {
          inspectEvalValues(res[field], field, label, add, visited);
        }
      }

      checkReturnedHooks(res, state.mode, hooksByMode.get(state.mode), add);
    }
  }

  return { ok: errors.length === 0, errors, details };
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const file = args.find((a) => !a.startsWith('--'));
  if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    console.error('usage: node check.cjs <lab.js>');
    process.exit(2);
  }
  const r = check(file);
  console.log(r.ok ? 'ok' : r.details.join('\n'));
  process.exit(r.ok ? 0 : 1);
}

module.exports = { check };
