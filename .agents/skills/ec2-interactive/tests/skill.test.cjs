const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const SKILL = path.join(__dirname, '..');
const REPO = path.join(SKILL, '..', '..', '..');
const read = (rel) => fs.readFileSync(path.join(SKILL, rel), 'utf8').replace(/\r\n/g, '\n');

const LEGACY_DELETED_FILES = [
  'assets/dc-runtime.js',
  'assets/template.dc.html',
  'scripts/harness.cjs',
  'scripts/frequency-model.cjs',
  'scripts/frequency-topics.cjs',
  'scripts/make-frequency-example.cjs',
  'references/scene-api.md',
  'references/example-frequency-response.dc.html',
  'tests/frequency-model.test.cjs',
  'tests/frequency-topics.test.cjs',
  'tests/template.test.cjs',
];

const LEGACY_FORBIDDEN_TERMS = [
  'Main.dc.html',
  'template.dc.html',
  'dc-runtime.js',
  'canvas.json',
  'scene-api.md',
  'harness.cjs',
  'frequency-model.cjs',
  'frequency-topics.cjs',
  'make-frequency-example.cjs',
  'example-frequency-response.dc.html',
];

test('frontmatter names the skill', () => {
  const md = read('SKILL.md');
  const fm = md.match(/^---\n([\s\S]*?)\n---\n/);
  assert.ok(fm, 'frontmatter block');
  assert.match(fm[1], /^name: ec2-interactive$/m);
  const d = fm[1].match(/^description: (.+)$/m);
  assert.ok(d && d[1].trim().length > 20, 'description');
});

test('every referenced skill file exists', () => {
  const skillMd = read('SKILL.md');
  const refsInSkill = [...new Set([...skillMd.matchAll(/\b((?:assets|scripts|references)\/[\w.-]+)/g)].map((m) => m[1]))];
  assert.ok(refsInSkill.length >= 8, 'references: ' + refsInSkill.join(', '));
  for (const r of refsInSkill) assert.ok(fs.existsSync(path.join(SKILL, r)), r);

  const refDocs = fs.readdirSync(path.join(SKILL, 'references'))
    .filter((f) => f.endsWith('.md'))
    .map((f) => path.join('references', f));
  for (const docRel of refDocs) {
    const content = read(docRel);
    const refs = [...new Set([...content.matchAll(/\b((?:assets|scripts|references)\/[\w.-]+)/g)].map((m) => m[1]))];
    for (const r of refs) assert.ok(fs.existsSync(path.join(SKILL, r)), `${docRel} -> ${r}`);
  }
});

test('SKILL.md and references cover v2 contracts and 4 verification gates', () => {
  const skillMd = read('SKILL.md');
  const refFiles = fs.readdirSync(path.join(SKILL, 'references'))
    .filter((f) => f.endsWith('.md'))
    .sort()
    .map((f) => path.join('references', f));
  const combined = [skillMd, ...refFiles.map(read)].join('\n');

  for (const needle of [
    'references/lab-api.md',
    'scripts/probe_interactive.py',
    'assets/mna.js',
    'lab.js',
    'probe',
    'bench',
    'approx',
    'scripts/check.cjs',
    'scripts/steps.cjs',
    'scripts/build.cjs',
    'scripts/save.cjs',
    'references/circuit-verification.md',
  ]) {
    assert.ok(combined.includes(needle), `missing v2 contract reference: ${needle}`);
  }

  // 4 verification gates in SKILL.md: check.cjs, independent verification, probe_interactive.py, live browser check
  assert.ok(skillMd.includes('lab-api.md'), 'SKILL.md must reference lab-api.md');
  assert.ok(skillMd.includes('probe_interactive.py'), 'SKILL.md must reference probe_interactive.py');
  assert.ok(skillMd.includes('mna.js'), 'SKILL.md must reference mna.js');
  assert.ok(skillMd.includes('lab.js'), 'SKILL.md must reference lab.js');
  for (const arch of ['probe', 'bench', 'approx']) {
    assert.match(skillMd, new RegExp(`\\b${arch}\\b`), `SKILL.md must mention archetype ${arch}`);
  }
  assert.ok(skillMd.includes('check.cjs'), 'Gate 1: check.cjs in SKILL.md');
  assert.ok(skillMd.includes('circuit-verification.md') && /독립/.test(skillMd), 'Gate 2: independent circuit verification in SKILL.md');
  assert.ok(skillMd.includes('probe_interactive.py'), 'Gate 3: probe_interactive.py in SKILL.md');
  assert.match(skillMd, /실제 브라우저|브라우저 확인/, 'Gate 4: live browser inspection in SKILL.md');
});

test('SKILL.md and references/*.md do not mention deleted legacy 3D artifacts', () => {
  const docs = [
    'SKILL.md',
    ...fs.readdirSync(path.join(SKILL, 'references'))
      .filter((f) => f.endsWith('.md'))
      .map((f) => path.join('references', f)),
  ];
  for (const docRel of docs) {
    const content = read(docRel);
    for (const term of LEGACY_FORBIDDEN_TERMS) {
      assert.equal(content.includes(term), false, `${docRel} still references legacy term: ${term}`);
    }
  }
});

test('legacy 3D runtime, template, scene-api, and frequency files are deleted', () => {
  for (const rel of LEGACY_DELETED_FILES) {
    assert.equal(fs.existsSync(path.join(SKILL, rel)), false, `legacy file still exists: ${rel}`);
  }
});

test('.claude link resolves to the skill', (t) => {
  const link = path.join(REPO, '.claude', 'skills', 'ec2-interactive');
  let installed = true;
  try { fs.lstatSync(link); } catch { installed = false; }
  if (!installed) return t.skip('no install link (standalone copy)');
  assert.ok(fs.lstatSync(link).isSymbolicLink());
  assert.equal(fs.readlinkSync(link).replace(/\\/g, '/'), '../../.agents/skills/ec2-interactive');
  assert.equal(fs.realpathSync(link), fs.realpathSync(SKILL));
});
