// Builds a standalone HTML page from a v2 lab.js spec without creating canvas.json.
// Usage: node build.cjs <lab.js> <out.html>
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ASSETS_DIR = path.join(__dirname, '..', 'assets');
const TEMPLATE_PATH = path.join(ASSETS_DIR, 'lab-template.html');
const MNA_PATH = path.join(ASSETS_DIR, 'mna.js');
const RUNTIME_PATH = path.join(ASSETS_DIR, 'lab-runtime.js');

const ALLOWED_CDNS = Object.freeze([
  'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
  'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
  'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
  'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
]);

function escapeHtml(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sanitizeComment(text) {
  return String(text == null ? '' : text).replace(/--/g, '- -');
}

function escapeScript(code) {
  return String(code == null ? '' : code).replace(/<\/(script)/gi, '<\\/$1');
}

function replaceLiteral(str, placeholder, value) {
  return str.split(placeholder).join(value);
}

// Execute lab.js in an isolated CommonJS wrapper matching browser IIFE globals
// (no Node require/process leaks, no require.cache staleness).
function loadLab(srcFile) {
  const resolved = path.resolve(String(srcFile || ''));
  const src = fs.readFileSync(resolved, 'utf8');
  const wrapped = `(function (module, exports, require, __filename, __dirname) { ${src}\n});`;
  const script = new vm.Script(wrapped, { filename: resolved });
  const factory = script.runInThisContext();
  const mod = { exports: {} };
  factory(mod, mod.exports, undefined, undefined, undefined);
  const spec = mod.exports;
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
    throw new Error('lab.js must export a spec object');
  }
  return spec;
}

function titleOf(spec) {
  if (!spec || typeof spec !== 'object') return '';
  return typeof spec.title === 'string' ? spec.title.trim() : '';
}

function build(srcFile, outFile) {
  const resolvedSrc = path.resolve(srcFile);
  const resolvedOut = path.resolve(outFile);
  const spec = loadLab(resolvedSrc);
  const title = titleOf(spec);
  if (!title) {
    throw new Error('lab.js spec is missing a non-empty title');
  }

  const template = fs.readFileSync(TEMPLATE_PATH, 'utf8');
  const mnaSrc = fs.readFileSync(MNA_PATH, 'utf8').trim();
  const runtimeSrc = fs.readFileSync(RUNTIME_PATH, 'utf8').trim();
  const labSrc = fs.readFileSync(resolvedSrc, 'utf8').trim();

  const rel = path.relative(path.dirname(resolvedOut), resolvedSrc).split(path.sep).join('/');
  const sourceComment = `생성 파일: ${sanitizeComment(rel)}을 고친 뒤 ec2-interactive/scripts/build.cjs로 다시 만드세요.`;

  const labBundle = [
    '(function () {',
    '  var module = { exports: {} };',
    '  var exports = module.exports;',
    '  (function (module, exports) {',
    labSrc,
    '  })(module, exports);',
    '  var spec = module.exports;',
    '  function boot() {',
    '    var root = document.getElementById("ec2-lab-root");',
    '    if (!root || !globalThis.EC2Lab) return;',
    '    globalThis.EC2Lab.mount(spec, root, { mna: globalThis.EC2MNA });',
    '  }',
    '  if (document.getElementById("ec2-lab-root")) {',
    '    boot();',
    '  } else if (document.readyState === "loading") {',
    '    document.addEventListener("DOMContentLoaded", boot, { once: true });',
    '  } else {',
    '    boot();',
    '  }',
    '})();',
  ].join('\n');

  let out = template;
  out = replaceLiteral(out, '__TITLE__', escapeHtml(title));
  out = replaceLiteral(out, '__SOURCE_COMMENT__', sourceComment);
  out = replaceLiteral(out, '__MNA_SCRIPT__', escapeScript(mnaSrc));
  out = replaceLiteral(out, '__RUNTIME_SCRIPT__', escapeScript(runtimeSrc));
  out = replaceLiteral(out, '__LAB_SCRIPT__', escapeScript(labBundle));
  return out;
}

if (require.main === module) {
  const [srcArg, outArg] = process.argv.slice(2);
  if (!srcArg || !outArg || !fs.existsSync(srcArg) || !fs.statSync(srcArg).isFile()) {
    console.error('usage: node build.cjs <lab.js> <out.html>');
    process.exit(2);
  }
  const srcFile = path.resolve(srcArg);
  const outFile = path.resolve(outArg);
  const html = build(srcFile, outFile);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, html, 'utf8');
  console.log('wrote ' + outFile);
}

module.exports = { build, loadLab, titleOf, ALLOWED_CDNS };
