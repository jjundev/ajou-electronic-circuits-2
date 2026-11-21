// Saves one v2 lab.js into a 복습노트 folder under the next free number, then builds its standalone HTML.
// Usage: node save.cjs <RUN/n/lab.js> <DEST> <name>   → {"nn", "html", "dir"} JSON (exit 0), usage (exit 2), or error (exit 1)
// Files are 인터렉티브_NN_<name>.html and .assets/자료_인터렉티브_NN_<name>/lab.js (no canvas.json).
// Never overwrites: the number skips every 인터렉티브_NN* and .assets/자료_인터렉티브_NN*. Nothing is written next to the source.
const fs = require('node:fs');
const path = require('node:path');
const { nextNumber } = require('./resolve.cjs');
const { build } = require('./build.cjs');

// A file name part: no path or reserved characters, no leading dot.
function cleanName(name) {
  const n = String(name == null ? '' : name).trim().replace(/\s+/g, '_');
  if (!n || /[\\/:*?"<>|]/.test(n) || n.startsWith('.')) {
    throw new Error('bad name: ' + JSON.stringify(name));
  }
  return n;
}

function save({ src, dest, name }) {
  name = cleanName(name);
  src = path.resolve(String(src || ''));
  dest = path.resolve(String(dest || ''));
  if (!fs.existsSync(src) || !fs.statSync(src).isFile()) {
    throw new Error('source lab.js not found: ' + src);
  }

  const hadDest = fs.existsSync(dest);
  fs.mkdirSync(dest, { recursive: true });
  const nn = nextNumber(dest);
  const assets = path.join(dest, '.assets');
  const hadAssets = fs.existsSync(assets);
  const dir = path.join(assets, '자료_인터렉티브_' + nn + '_' + name);
  const html = path.join(dest, '인터렉티브_' + nn + '_' + name + '.html');
  fs.mkdirSync(assets, { recursive: true });

  const cleanupEmptyDirs = () => {
    if (!hadAssets) { try { fs.rmdirSync(assets); } catch (e) {} }
    if (!hadDest) { try { fs.rmdirSync(dest); } catch (e) {} }
  };

  try {
    fs.mkdirSync(dir); // non-recursive: fails if dir appeared concurrently
  } catch (e) {
    cleanupEmptyDirs();
    throw e;
  }

  let fd = null;
  let ownsHtml = false;
  try {
    const copy = path.join(dir, 'lab.js');
    fs.copyFileSync(src, copy);
    const page = build(copy, html);
    fd = fs.openSync(html, 'wx');
    ownsHtml = true;
    fs.writeFileSync(fd, page, 'utf8');
    fs.closeSync(fd);
    fd = null;
  } catch (e) {
    if (fd !== null) { try { fs.closeSync(fd); } catch {} }
    if (ownsHtml) { try { fs.unlinkSync(html); } catch {} }
    fs.rmSync(dir, { recursive: true, force: true });
    cleanupEmptyDirs();
    throw e;
  }
  return { nn, html, dir };
}

if (require.main === module) {
  const [src, dest, name] = process.argv.slice(2);
  if (!src || !dest || !name || !fs.existsSync(src) || !fs.statSync(src).isFile()) {
    console.error('usage: node save.cjs <RUN/n/lab.js> <DEST> <name>');
    process.exit(2);
  }
  try {
    console.log(JSON.stringify(save({ src, dest, name })));
  } catch (e) {
    console.error('save failed: ' + String(e.message || e).split('\n')[0]);
    process.exit(1);
  }
}

module.exports = { save };
