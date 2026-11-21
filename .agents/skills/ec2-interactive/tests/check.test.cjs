const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { check } = require('../scripts/check.cjs');

const SKILL = path.join(__dirname, '..');
const EX = path.join(SKILL, 'references', 'example-lab.js');
const CLI = path.join(SKILL, 'scripts', 'check.cjs');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'ec2-check-'));
let seq = 0;

function mutate(fn) {
  const src = fs.readFileSync(EX, 'utf8');
  const out = fn(src);
  assert.notEqual(out, src, 'mutation changed nothing');
  const file = path.join(TMP, `m${seq++}.js`);
  fs.writeFileSync(file, out, 'utf8');
  return file;
}

function writeRaw(code) {
  const file = path.join(TMP, `raw${seq++}.js`);
  fs.writeFileSync(file, code, 'utf8');
  return file;
}

test('example-lab.js passes all checks cleanly', () => {
  const r = check(EX);
  assert.equal(r.ok, true, (r.details || []).join('\n'));
  assert.deepEqual(r.errors, []);
});

test('missing SVG hooks produce HOOK_MISSING', () => {
  const missingNode = mutate((s) => s.replaceAll('data-node="out"', 'data-node="other"'));
  const r1 = check(missingNode);
  assert.equal(r1.ok, false);
  assert.ok(r1.errors.some((e) => e.code === 'HOOK_MISSING' && /out/.test(e.message)), r1.details.join('\n'));

  const missingBranch = mutate((s) => s.replace('data-branch="i_div"', 'data-branch="other"'));
  assert.ok(check(missingBranch).errors.some((e) => e.code === 'HOOK_MISSING'));

  const missingElem = mutate((s) => s.replace('data-elem="r2"', 'data-elem="other"'));
  assert.ok(check(missingElem).errors.some((e) => e.code === 'HOOK_MISSING'));

  const missingPort = mutate((s) => s.replace('data-port="load"', 'data-port="other"'));
  assert.ok(check(missingPort).errors.some((e) => e.code === 'HOOK_MISSING'));

  const missingStep = mutate((s) => s.replace('data-causal-step="3"', 'data-causal-step="99"'));
  assert.ok(check(missingStep).errors.some((e) => e.code === 'HOOK_MISSING'));
});

test('plain-text subscripts and $...$ inside SVG <text> produce SVG_TEXT_NOTATION (Review Focus #3)', () => {
  const f1 = mutate((s) => s.replace('v<tspan baseline-shift="sub" font-size="78%">out</tspan>', 'V_out'));
  const r1 = check(f1);
  assert.equal(r1.ok, false);
  assert.ok(r1.errors.some((e) => e.code === 'SVG_TEXT_NOTATION'), r1.details.join('\n'));

  const f2 = mutate((s) => s.replace('R<tspan baseline-shift="sub" font-size="78%">1</tspan>', '$g_m$'));
  const r2 = check(f2);
  assert.equal(r2.ok, false);
  assert.ok(r2.errors.some((e) => e.code === 'SVG_TEXT_NOTATION'), r2.details.join('\n'));

  const f3 = mutate((s) => s.replace('R<tspan baseline-shift="sub" font-size="78%">2</tspan>', '\\(v_o\\)'));
  assert.ok(check(f3).errors.some((e) => e.code === 'SVG_TEXT_NOTATION'));
});

test('hardcoded hex color in SVG produces HEX_IN_SVG while url(#id) does not', () => {
  const badHex = mutate((s) => s.replace('class="fig-ink" data-branch="i_div"', 'stroke="#2563eb" data-branch="i_div"'));
  const r1 = check(badHex);
  assert.equal(r1.ok, false);
  assert.ok(r1.errors.some((e) => e.code === 'HEX_IN_SVG'), r1.details.join('\n'));

  const validUrlRef = mutate((s) => s.replace('<g data-badges>', '<defs><marker id="ace"><path d="M0 0L4 2"/></marker></defs><line marker-end="url(#ace)" x1="0" y1="0" x2="0" y2="0"/><g data-badges>'));
  const r2 = check(validUrlRef);
  assert.equal(r2.errors.some((e) => e.code === 'HEX_IN_SVG'), false, r2.details.join('\n'));
});

test('mistakes length != 3 or empty fields produce MISTAKES_INVALID', () => {
  const tooFew = mutate((s) => s.replace(
    /\{\s*title: '하단 경로 개방 시 0 V로 착각'[\s\S]*?\},/,
    ''
  ));
  const r1 = check(tooFew);
  assert.equal(r1.ok, false);
  assert.ok(r1.errors.some((e) => e.code === 'MISTAKES_INVALID'), r1.details.join('\n'));

  const emptyTitle = mutate((s) => s.replace("title: '부하 저항을 무시한 무부하 공식 고집'", "title: '   '"));
  assert.ok(check(emptyTitle).errors.some((e) => e.code === 'MISTAKES_INVALID'));
});

test('NaN/Infinity or throwing evaluate() produces EVAL_NON_FINITE / EVAL_THROW', () => {
  const nanNode = mutate((s) => s.replace('v: Number(vOut.toFixed(2))', 'v: NaN'));
  const r1 = check(nanNode);
  assert.equal(r1.ok, false);
  assert.ok(r1.errors.some((e) => e.code === 'EVAL_NON_FINITE'), r1.details.join('\n'));

  const nanTile = mutate((s) => s.replace("val: `${vOut.toFixed(2)} V`", "val: `${NaN} V`"));
  assert.ok(check(nanTile).errors.some((e) => e.code === 'EVAL_NON_FINITE'));

  const extremeThrow = mutate((s) => s.replace(
    'const vin = Number(state.params.vin);',
    'const vin = Number(state.params.vin); if (vin === -10 && Number(state.params.r1) === 10) throw new Error("boom at extreme");'
  ));
  const r3 = check(extremeThrow);
  assert.equal(r3.ok, false);
  assert.ok(r3.errors.some((e) => e.code === 'EVAL_THROW' && /boom at extreme/.test(e.message)), r3.details.join('\n'));
});

test('bench archetype allows intentional singular diagnosis when diagnosis.singular === true and no NaN strings leak', () => {
  const benchOk = writeRaw(`
    module.exports = {
      id: 'bench-singular',
      title: '종단 벤치',
      archetype: 'bench',
      modes: [{
        key: 'vv',
        label: 'V-V',
        viewBox: '0 0 200 100',
        ariaLabel: 'V-V 회로',
        svg: '<svg viewBox="0 0 200 100"><g data-port="p1"><text class="port-chip" x="40" y="50">단락</text></g></svg>',
        ports: [{ id: 'p1', label: '포트', options: [{ id: 'open', label: '개방' }, { id: 'short', label: '단락' }], def: 'open', answer: 'open' }],
      }],
      mistakes: { vv: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
      evaluate(state, mna) {
        if (state.ports.p1 === 'short') {
          const r = mna.solveCircuit({ elements: [{ id: 'vs', type: 'vsrc', n1: 'a', n2: '0', value: 1 }, { id: 'sh', type: 'short', n1: 'a', n2: '0' }] });
          return { tiles: [{ label: '상태', val: '단락' }], diagnosis: { kind: 'bad', singular: r.singular, title: '전압원 단락', text: r.reason } };
        }
        return { tiles: [{ label: '상태', val: '정상' }], diagnosis: { kind: 'ok', title: '정상', text: '개방' } };
      },
    };
  `);
  const r = check(benchOk);
  assert.equal(r.ok, true, r.details.join('\n'));
});

test('disallowed external URL produces EXTERNAL_URL while standard SVG xmlns URIs pass', () => {
  const svgXmlnsOk = mutate((s) => s.replace(
    '<svg viewBox="0 0 380 220"',
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 380 220"'
  ));
  const okRes = check(svgXmlnsOk);
  assert.equal(okRes.ok, true, okRes.details.join('\n'));

  const evilXmlnsPrefix = mutate((s) => s.replace(
    '<svg viewBox="0 0 380 220"',
    '<svg xmlns="http://www.w3.org/2000/svg/evil" viewBox="0 0 380 220"'
  ));
  const prefixRes = check(evilXmlnsPrefix);
  assert.equal(prefixRes.ok, false);
  assert.ok(prefixRes.errors.some((e) => e.code === 'EXTERNAL_URL'), prefixRes.details.join('\n'));

  const badUrl = mutate((s) => s.replace(
    "id: 'example-voltage-divider',",
    "id: 'example-voltage-divider',\n  badRef: 'https://evil.example.com/script.js',"
  ));
  const r = check(badUrl);
  assert.equal(r.ok, false);
  assert.ok(r.errors.some((e) => e.code === 'EXTERNAL_URL'), r.details.join('\n'));
});

test('schema errors and load errors are reported accurately', () => {
  const missingInlineViewBox = mutate((s) => s.replace(' viewBox="0 0 380 220"', ''));
  const vbRes = check(missingInlineViewBox);
  assert.equal(vbRes.ok, false);
  assert.ok(vbRes.errors.some((e) => e.code === 'SCHEMA_INVALID'), vbRes.details.join('\n'));

  const badPredict = mutate((s) => s.replace("answerId: 'same'", "answerId: 'wrong-id'"));
  assert.ok(check(badPredict).errors.some((e) => e.code === 'SCHEMA_INVALID'));

  const badArch = mutate((s) => s.replace("archetype: 'probe'", "archetype: '3d'"));
  assert.ok(check(badArch).errors.some((e) => e.code === 'SCHEMA_INVALID'));

  const syntaxErr = writeRaw('module.exports = { broken: ');
  assert.ok(check(syntaxErr).errors.some((e) => e.code === 'LOAD_ERROR'));
});

test('CLI exits 0 with ok, 1 with error lines, 2 on bad usage', () => {
  const ok = spawnSync(process.execPath, [CLI, EX], { encoding: 'utf8' });
  assert.equal(ok.status, 0);
  assert.equal(ok.stdout.trim(), 'ok');

  const badFile = mutate((s) => s.replace('v<tspan baseline-shift="sub" font-size="78%">out</tspan>', 'V_out'));
  const bad = spawnSync(process.execPath, [CLI, badFile], { encoding: 'utf8' });
  assert.equal(bad.status, 1);
  assert.match(bad.stdout, /SVG_TEXT_NOTATION/);

  const usage = spawnSync(process.execPath, [CLI], { encoding: 'utf8' });
  assert.equal(usage.status, 2);

  const missing = spawnSync(process.execPath, [CLI, path.join(TMP, 'missing.js')], { encoding: 'utf8' });
  assert.equal(missing.status, 2);
});
