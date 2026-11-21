const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync, spawnSync } = require('node:child_process');
const { build, loadLab, titleOf, ALLOWED_CDNS } = require('../scripts/build.cjs');

const SKILL = path.join(__dirname, '..');
const EX = path.join(SKILL, 'references', 'example-lab.js');

test('ALLOWED_CDNS contains exact 4 allowed CDN URLs', () => {
  assert.deepEqual([...ALLOWED_CDNS], [
    'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
  ]);
});

test('loadLab and titleOf read spec without polluting require cache', () => {
  const spec = loadLab(EX);
  assert.equal(spec.id, 'example-voltage-divider');
  assert.equal(titleOf(spec), '전압 분배기 동작 프로브');
  assert.equal(typeof spec.evaluate, 'function');
});

test('build makes a standalone HTML page from lab.js without creating canvas.json', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ec2-build-'));
  const outHtml = path.join(dir, '인터렉티브_01.html');
  const html = build(EX, outHtml);

  for (const needle of [
    '<!doctype html>',
    '<title>전압 분배기 동작 프로브</title>',
    'id="ec2-lab-root"',
    'EC2MNA',
    'EC2Lab',
    'EC2Lab.mount(',
    ...ALLOWED_CDNS,
  ]) {
    assert.ok(html.includes(needle), `missing ${needle}`);
  }
  for (const legacy of ['<x-dc>', '<template id="dc-template">', 'mountDC(', 'canvas.json']) {
    assert.equal(html.includes(legacy), false, `unexpected legacy marker ${legacy}`);
  }
  assert.equal(fs.existsSync(path.join(path.dirname(EX), 'canvas.json')), false);
  assert.equal(fs.existsSync(outHtml), false); // build() returns HTML without writing disk
});

test('build escapes </script> inside lab.js and preserves $$ KaTeX patterns (Review Focus #3)', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ec2-build-esc-'));
  const labPath = path.join(dir, 'lab.js');
  const outHtml = path.join(dir, 'out.html');

  const src = fs.readFileSync(EX, 'utf8').replace(
    "title: '전압 분배기 동작 프로브',",
    () => "title: '안전 <테스트> & \"프로브\"',\n  _evil: '</script><SCRIPT>alert(1)</SCRIPT>',\n  _dollar: '$$ $& $\\' $`',"
  );
  fs.writeFileSync(labPath, src, 'utf8');

  const html = build(labPath, outHtml);
  assert.ok(html.includes('<title>안전 &lt;테스트&gt; &amp; &quot;프로브&quot;</title>'));
  assert.ok(html.includes('<\\/script><SCRIPT>alert(1)<\\/SCRIPT>'));
  assert.ok(html.includes('$$v_{\\\\text{out}}'));
  assert.ok(html.includes("$$ $& $\\' $`"));

  // Exact 6 closing </script> tags matching lab-template.html (no premature termination).
  const closeScripts = (html.match(/<\/script>/gi) || []).length;
  assert.equal(closeScripts, 6, 'unexpected </script> tag inside bundled scripts');

  // Verify the injected __LAB_SCRIPT__ block parses cleanly and executes with exact strings intact.
  const scriptBodies = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const lastScript = scriptBodies[scriptBodies.length - 1];
  let mountedSpec = null;
  const vm = require('node:vm');
  vm.runInNewContext(lastScript, {
    document: { getElementById: () => ({ id: 'ec2-lab-root' }), readyState: 'complete' },
    globalThis: {
      EC2MNA: {},
      EC2Lab: { mount: (spec) => { mountedSpec = spec; } },
    },
  });
  assert.equal(mountedSpec._evil, '</script><SCRIPT>alert(1)</SCRIPT>');
  assert.equal(mountedSpec._dollar, "$$ $& $' $`");
});

test('CLI writes standalone HTML without canvas.json and exits 2 on bad usage', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ec2-build-cli-'));
  const srcDir = path.join(dir, '자료_인터렉티브_01');
  fs.mkdirSync(srcDir);
  const src = path.join(srcDir, 'lab.js');
  fs.copyFileSync(EX, src);
  const out = path.join(dir, '인터렉티브_01.html');

  const stdout = execFileSync(process.execPath, [path.join(SKILL, 'scripts', 'build.cjs'), src, out], { encoding: 'utf8' });
  assert.match(stdout, /^wrote /);
  assert.ok(fs.existsSync(out));
  assert.ok(fs.readFileSync(out, 'utf8').includes('자료_인터렉티브_01/lab.js'));
  assert.equal(fs.existsSync(path.join(srcDir, 'canvas.json')), false);

  const missingArgs = spawnSync(process.execPath, [path.join(SKILL, 'scripts', 'build.cjs')], { encoding: 'utf8' });
  assert.equal(missingArgs.status, 2);
  assert.match(missingArgs.stderr, /usage:/);

  const missingSrc = spawnSync(process.execPath, [path.join(SKILL, 'scripts', 'build.cjs'), path.join(dir, 'nope.js'), out], { encoding: 'utf8' });
  assert.equal(missingSrc.status, 2);
});
