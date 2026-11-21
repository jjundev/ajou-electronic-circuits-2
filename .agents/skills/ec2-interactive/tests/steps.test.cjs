const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { stepsReport } = require('../scripts/steps.cjs');

const SKILL = path.join(__dirname, '..');
const EX = path.join(SKILL, 'references', 'example-lab.js');
const SCRIPT = path.join(SKILL, 'scripts', 'steps.cjs');

test('stepsReport evaluates every probe state with mode, tiles, nodes, and diagnosis', () => {
  const rows = stepsReport(EX);
  assert.ok(Array.isArray(rows) && rows.length >= 5, `expected >= 5 probe rows, got ${rows.length}`);

  for (const row of rows) {
    assert.equal(typeof row.label, 'string');
    assert.ok(row.label.length > 0);
    assert.equal(row.mode, 'divider');
    assert.equal(typeof row.step, 'number');
    assert.equal(typeof row.causalStep, 'number');
    assert.ok(row.ports && typeof row.ports === 'object');
    assert.ok(Array.isArray(row.disabledElems));
    assert.ok(Array.isArray(row.tiles) && row.tiles.length > 0);
    assert.ok(row.nodes && typeof row.nodes === 'object');
    assert.ok('diagnosis' in row);
  }

  assert.ok(rows.some((r) => r.causalStep === 3), 'should cover last causal step');
  assert.ok(rows.some((r) => r.disabledElems.includes('r2')), 'should cover element OFF');
  assert.ok(rows.some((r) => r.ports.load === 'rl'), 'should cover loaded preset/port');
});

test('CLI prints readable snapshot text and exits 0; missing file exits 2', () => {
  const ok = spawnSync(process.execPath, [SCRIPT, EX], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  assert.match(ok.stdout, /초기 상태/);
  assert.match(ok.stdout, /divider/);
  assert.match(ok.stdout, /출력 전압/);

  assert.equal(spawnSync(process.execPath, [SCRIPT], { encoding: 'utf8' }).status, 2);
  assert.equal(spawnSync(process.execPath, [SCRIPT, '/no/such/lab.js'], { encoding: 'utf8' }).status, 2);
});
