// Evaluates every probe state of a v2 lab.js for content review and browser verification.
// Usage: node steps.cjs <lab.js>   → readable state snapshots (exit 0), or usage error (exit 2)
const fs = require('node:fs');
const { loadLab } = require('./build.cjs');
const EC2MNA = require('../assets/mna.js');
const { buildProbeStates } = require('../assets/lab-runtime.js');

function stepsReport(srcFile) {
  const spec = loadLab(srcFile);
  const probeStates = buildProbeStates(spec);
  return probeStates.map(({ label, state }) => {
    const res = typeof spec.evaluate === 'function' ? (spec.evaluate(state, EC2MNA) || {}) : {};
    return {
      label,
      mode: state.mode,
      step: state.step,
      causalStep: state.causalStep,
      ports: Object.assign({}, state.ports),
      disabledElems: Array.isArray(state.disabledElems) ? state.disabledElems.slice() : [],
      tiles: Array.isArray(res.tiles) ? res.tiles : [],
      nodes: res.nodes && typeof res.nodes === 'object' ? res.nodes : {},
      diagnosis: res.diagnosis !== undefined ? res.diagnosis : null,
    };
  });
}

function formatTiles(tiles) {
  if (!Array.isArray(tiles) || tiles.length === 0) return '-';
  return tiles.map((t) => `${t.label}: ${t.val ?? t.value ?? ''}`).join(' | ');
}

function formatNodes(nodes) {
  const entries = Object.entries(nodes || {});
  if (entries.length === 0) return '-';
  return entries.map(([k, info]) => {
    if (info && typeof info === 'object') {
      const val = info.badge ?? info.text ?? (info.v !== undefined ? `${info.v}${info.unit ? ' ' + info.unit : ''}` : JSON.stringify(info));
      return `${k}=${val}`;
    }
    return `${k}=${info}`;
  }).join(', ');
}

function formatDiagnosis(diag) {
  if (!diag) return '-';
  if (typeof diag === 'string') return diag;
  const kind = diag.kind || (diag.singular ? 'bad' : 'info');
  return `[${kind}${diag.singular ? '/singular' : ''}] ${diag.title ? diag.title + ' — ' : ''}${diag.text || diag.reason || ''}`.trim();
}

if (require.main === module) {
  const file = process.argv[2];
  if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    console.error('usage: node steps.cjs <lab.js>');
    process.exit(2);
  }
  let rows;
  try {
    rows = stepsReport(file);
  } catch (e) {
    console.error('steps failed: ' + String(e && e.message ? e.message : e).split('\n')[0]);
    process.exit(1);
  }
  if (rows.length === 0) {
    console.log('단계 없음');
    process.exit(0);
  }
  rows.forEach((r, idx) => {
    const portStr = Object.keys(r.ports).length ? ` ports=${JSON.stringify(r.ports)}` : '';
    const offStr = r.disabledElems.length ? ` off=${r.disabledElems.join(',')}` : '';
    console.log(`${idx + 1}. ${r.label} [mode=${r.mode} step=${r.step} causal=${r.causalStep}${portStr}${offStr}]`);
    console.log(`   타일: ${formatTiles(r.tiles)}`);
    console.log(`   노드: ${formatNodes(r.nodes)}`);
    console.log(`   진단: ${formatDiagnosis(r.diagnosis)}`);
  });
}

module.exports = { stepsReport };
