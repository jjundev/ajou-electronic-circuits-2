const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const SKILL = path.join(__dirname, '..');
const REPO = path.join(SKILL, '..', '..', '..');
const read = (rel) => fs.readFileSync(path.join(SKILL, rel), 'utf8').replace(/\r\n/g, '\n');

test('frontmatter names the skill', () => {
  const md = read('SKILL.md');
  const fm = md.match(/^---\n([\s\S]*?)\n---\n/);
  assert.ok(fm, 'frontmatter block');
  assert.match(fm[1], /^name: ec2-interactive$/m);
  const d = fm[1].match(/^description: (.+)$/m);
  assert.ok(d && d[1].trim().length > 20, 'description');
});

test('every referenced skill file exists', () => {
  const md = read('SKILL.md');
  const refs = [...new Set([...md.matchAll(/\b((?:assets|scripts|references)\/[\w.-]+)/g)].map((m) => m[1]))];
  assert.ok(refs.length >= 8, 'references: ' + refs.join(', '));
  for (const r of refs) assert.ok(fs.existsSync(path.join(SKILL, r)), r);
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
