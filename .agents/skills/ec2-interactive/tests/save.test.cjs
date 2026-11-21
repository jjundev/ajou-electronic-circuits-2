const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { save } = require('../scripts/save.cjs');

const nfc = (p) => p.normalize('NFC').replace(/\\/g, '/');
const SKILL = path.join(__dirname, '..');
const EX = path.join(SKILL, 'references', 'example-lab.js');
const SCRIPT = path.join(SKILL, 'scripts', 'save.cjs');

function setup() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ec2-save-'));
  const src = path.join(tmp, 'run', '1', 'lab.js');
  fs.mkdirSync(path.dirname(src), { recursive: true });
  fs.writeFileSync(
    src,
    fs.readFileSync(EX, 'utf8').replace("title: '전압 분배기 동작 프로브',", "title: '테스트 주제',"),
    'utf8'
  );
  const dest = path.join(tmp, '1120');
  fs.mkdirSync(dest);
  return { tmp, src, dest };
}

test('first save creates 인터렉티브_01_<이름>.html and .assets/자료_인터렉티브_01_<이름>/lab.js without canvas.json', () => {
  const { src, dest } = setup();
  const r = save({ src, dest, name: '테스트 주제' });
  assert.equal(r.nn, '01');
  assert.equal(nfc(r.html), nfc(path.join(dest, '인터렉티브_01_테스트_주제.html')));
  assert.equal(nfc(r.dir), nfc(path.join(dest, '.assets', '자료_인터렉티브_01_테스트_주제')));

  const built = fs.readFileSync(r.html, 'utf8');
  assert.match(built, /<title>테스트 주제<\/title>/);
  assert.match(built, /EC2MNA/);
  assert.match(built, /EC2Lab/);
  assert.ok(fs.existsSync(path.join(r.dir, 'lab.js')));
  assert.equal(fs.existsSync(path.join(r.dir, 'canvas.json')), false);
  assert.equal(fs.existsSync(path.join(r.dir, 'Main.dc.html')), false);
});

test('existing legacy or v2 html advances next number without touching existing files', () => {
  const { src, dest } = setup();
  fs.writeFileSync(path.join(dest, '인터렉티브_01_기존.html'), 'legacy-1');
  fs.writeFileSync(path.join(dest, '인터렉티브_02_기존2.html'), 'legacy-2');
  fs.mkdirSync(path.join(dest, '.assets', '자료_인터렉티브_03_기존3'), { recursive: true });
  const r = save({ src, dest, name: '새_주제' });
  assert.equal(r.nn, '04');
  assert.equal(path.basename(r.html), '인터렉티브_04_새_주제.html');
  assert.equal(fs.readFileSync(path.join(dest, '인터렉티브_01_기존.html'), 'utf8'), 'legacy-1');
});

test('creates missing dest and writes nothing next to source', () => {
  const { tmp, src } = setup();
  const d = path.join(tmp, 'new', '1120');
  const before = fs.readdirSync(path.dirname(src)).sort();
  const r = save({ src, dest: d, name: 'Test_Topic' });
  assert.equal(r.nn, '01');
  assert.ok(fs.existsSync(path.join(d, '인터렉티브_01_Test_Topic.html')));
  assert.deepEqual(fs.readdirSync(path.dirname(src)).sort(), before);
});

test('two saves in a row get 01 and 02', () => {
  const { src, dest } = setup();
  assert.equal(save({ src, dest, name: 'Test_Topic' }).nn, '01');
  assert.equal(save({ src, dest, name: 'Test_Topic' }).nn, '02');
});

test('normalizes spaces and preserves Korean + English proper nouns; rejects unsafe names', () => {
  const { src, dest } = setup();
  const r = save({ src, dest, name: '  전사와   RNA 가공 ' });
  assert.equal(path.basename(r.html), '인터렉티브_01_전사와_RNA_가공.html');
  assert.equal(path.basename(r.dir), '자료_인터렉티브_01_전사와_RNA_가공');
  assert.match(fs.readFileSync(r.html, 'utf8'), /생성 파일: \.assets\/자료_인터렉티브_01_전사와_RNA_가공\/lab\.js/);

  const { dest: cleanDest } = setup();
  for (const badName of [undefined, '', '   ', 'a/b', '../x', 'a:b', '..']) {
    assert.throws(() => save({ src, dest: cleanDest, name: badName }), /name/, String(badName));
  }
  assert.deepEqual(fs.readdirSync(cleanDest), []);
});

test('a failed save leaves no numbered folder or partial files', () => {
  const { tmp, dest } = setup();
  assert.throws(() => save({ src: path.join(tmp, 'run', '1'), dest, name: 'Test_Topic' }));
  assert.deepEqual(fs.readdirSync(dest), []);

  const badLab = path.join(tmp, 'bad.js');
  fs.writeFileSync(badLab, 'module.exports = { broken:', 'utf8');
  assert.throws(() => save({ src: badLab, dest, name: 'Test_Topic' }));
  assert.deepEqual(fs.readdirSync(dest), []);
});

test('concurrent EEXIST on wx never overwrites existing HTML and rolls back .assets dir', () => {
  const { src, dest } = setup();
  const realOpen = fs.openSync;
  let occupied;
  try {
    fs.openSync = function (file, flags) {
      if (flags === 'wx' && path.dirname(file) === dest) {
        occupied = file;
        fs.writeFileSync(file, 'concurrent owner');
      }
      return realOpen.apply(this, arguments);
    };
    assert.throws(() => save({ src, dest, name: 'CS' }), { code: 'EEXIST' });
  } finally {
    fs.openSync = realOpen;
  }
  assert.equal(fs.readFileSync(occupied, 'utf8'), 'concurrent owner');
  assert.equal(fs.existsSync(path.join(dest, '.assets', '자료_인터렉티브_01_CS')), false);
});

test('simulated writeFileSync failure rolls back partial HTML and .assets dir', () => {
  const { src, dest } = setup();
  const realWrite = fs.writeFileSync;
  try {
    fs.writeFileSync = function (file) {
      if (typeof file === 'number') throw new Error('simulated disk failure');
      return realWrite.apply(this, arguments);
    };
    assert.throws(() => save({ src, dest, name: 'CS' }), /disk failure/);
  } finally {
    fs.writeFileSync = realWrite;
  }
  assert.deepEqual(fs.readdirSync(dest), []);
});

test('CLI prints JSON and exits 0; bad input exits 2', () => {
  const { tmp, src, dest } = setup();
  const ok = spawnSync(process.execPath, [SCRIPT, src, dest, 'Test_Topic'], { encoding: 'utf8' });
  assert.equal(ok.status, 0, ok.stderr);
  assert.equal(JSON.parse(ok.stdout).nn, '01');

  assert.equal(spawnSync(process.execPath, [SCRIPT, src], { encoding: 'utf8' }).status, 2);
  assert.equal(spawnSync(process.execPath, [SCRIPT, src, dest], { encoding: 'utf8' }).status, 2);
  assert.equal(spawnSync(process.execPath, [SCRIPT, '/no/such/lab.js', dest, 'Test_Topic'], { encoding: 'utf8' }).status, 2);
  assert.equal(spawnSync(process.execPath, [SCRIPT, path.join(tmp, 'run', '1'), dest, 'Test_Topic'], { encoding: 'utf8' }).status, 2);
});
