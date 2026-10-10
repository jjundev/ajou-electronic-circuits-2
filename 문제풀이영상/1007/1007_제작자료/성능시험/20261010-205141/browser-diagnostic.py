"""Bounded diagnostic. Run only after the parent sends GO.

Writes scratch composition and diagnostic results only. Production files are read.
"""
from pathlib import Path
import hashlib, json, os, re, shutil, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / '문제풀이영상/1007/1007_제작자료/실행/20261010-124459-semantic-caption-wrap/videos/problem-d885c8738da3/composition'
CLI = Path('/Users/hyunjun_macbook_pro/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/cli.js')
FFMPEG = '/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
OUT = HERE / 'browser-diagnostic'
ENV = os.environ.copy()
ENV['HYPERFRAMES_FFMPEG_PATH'] = FFMPEG
ENV['HF_FORCE_DRAWELEMENT'] = '0'
ENV['HF_DE_VERIFY'] = '4'
ENV['HF_DE_VERIFY_MIN_DB'] = '32'
FRAMES = [0, 30, 60, 90, 120, 150, 180, 210, 239]


def inventory(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def call(command, cwd=None, log=None):
    result = subprocess.run(list(map(str, command)), cwd=cwd, env=ENV,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=180)
    if log:
        log.write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); see {log}')
    return result.stdout


def digest_rows(path):
    rows = [line.split(',') for line in path.read_text().splitlines()
            if line and not line.startswith('#')]
    assert len(rows) == 240, f'Expected 240 decoded frames, got {len(rows)}'
    pts = [int(row[2].strip()) for row in rows]
    assert pts == list(range(240)), f'Unexpected frame alignment in {path}'
    return [row[-1].strip() for row in rows]


def main():
    if OUT.exists():
        raise RuntimeError(f'Refusing to overwrite diagnostic directory: {OUT}')
    OUT.mkdir()
    before = inventory(SOURCE)
    comp = OUT / 'composition'
    shutil.copytree(SOURCE, comp)
    original = (comp / 'index.html').read_text()
    modified, count = re.subn(r'data-duration="[^"]+"', 'data-duration="8"', original, count=1)
    assert count == 1
    old = 'tl.fromTo(clock,{frame:0},{frame:T.total_frames,duration:T.total_frames/30,ease:'
    new = 'tl.fromTo(clock,{frame:1800},{frame:2040,duration:8,ease:'
    assert modified.count(old) == 1
    (comp / 'index.html').write_text(modified.replace(old, new))
    after_copy = inventory(comp)
    assert set(before) == set(after_copy)
    assert all(before[p] == after_copy[p] for p in before if p != 'index.html')
    (OUT / 'source-hashes-before.json').write_text(json.dumps(before, indent=2))
    metadata = {
        'source': str(SOURCE), 'source_interval_s': [60, 68], 'frames': 240,
        'fps': 30, 'expected_size': [1920, 1080], 'cli': str(CLI),
        'cli_version': json.loads((CLI.parent.parent / 'package.json').read_text())['version'],
        'ffmpeg_version': call([FFMPEG, '-version']).splitlines()[0],
        'sparse_frame_indices': FRAMES,
        'limits': 'Single sequential 8-second diagnostic per case; no production adoption; no encoder --gpu; forced drawElement bypass disabled; differences do not establish degradation.',
        'relevant_environment': {k: ENV.get(k) for k in (
            'HYPERFRAMES_FFMPEG_PATH', 'HYPERFRAMES_BROWSER_PATH',
            'PRODUCER_BROWSER_GPU_MODE', 'PRODUCER_FORCE_SCREENSHOT',
            'PRODUCER_EXPERIMENTAL_FAST_CAPTURE', 'PRODUCER_ENABLE_STREAMING_ENCODE',
            'HF_FORCE_DRAWELEMENT', 'HF_DE_VERIFY', 'HF_DE_VERIFY_MIN_DB',
            'HF_FAST_CAPTURE_CSSFX', 'HF_FAST_CAPTURE_INTERVAL_SS',
            'HF_FAST_CAPTURE_BOUNDARY_SS', 'HF_FAST_CAPTURE_INTERVAL_FRACTION')},
    }
    assert metadata['cli_version'] == '0.8.137'
    (OUT / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    results = []
    cases = [('A-metal-screenshot', '--browser-gpu', False),
             ('B-software-screenshot', '--no-browser-gpu', False),
             ('C-metal-fast', '--browser-gpu', True)]
    for name, browser, fast in cases:
        video = OUT / f'{name}.mp4'
        cmd = ['node', CLI, 'render', '--composition', 'index.html', '--quality', 'delivery',
               '--workers', '4', browser, '--experimental-fast-capture=' + str(fast).lower(),
               '--output', video]
        log = OUT / f'{name}.log'
        text = call(['/usr/bin/time', '-lp', *cmd], cwd=comp, log=log)
        row = {'case': name, 'command': list(map(str, cmd)), 'log': log.name,
               'actual_backend_and_capture_lines': [line for line in text.splitlines()
                 if any(key in line for key in ('Browser launched', 'browserGpuMode probe',
                    'fast capture:', 'self-verify', 'drawElement', 'falling back', 're-rendering',
                    'capture_strategy', 'worker_resolution', 'capture_disk'))]}
        for key in ('real', 'user', 'sys'):
            match = re.findall(r'^' + key + r'\s+([0-9.]+)', text, re.M)
            row[key + '_s'] = float(match[-1]) if match else None
        for line in text.splitlines():
            if 'Render:trace' not in line or '{' not in line:
                continue
            try:
                event = json.loads(line[line.index('{'):])
            except ValueError:
                continue
            if event.get('phase') in ('capture_strategy', 'worker_resolution'):
                row.setdefault('strategy_events', []).append(event)
            if event.get('status') == 'end' and event.get('phase') in ('capture_disk', 'encode'):
                row[event['phase'] + '_s'] = event.get('durationMs', 0) / 1000
        probe = json.loads(call(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', video]))
        stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        assert (stream['width'], stream['height'], stream['avg_frame_rate'], int(stream['nb_frames'])) == (1920, 1080, '30/1', 240)
        row['video'] = {k: stream.get(k) for k in ('codec_name', 'width', 'height', 'avg_frame_rate', 'nb_frames', 'duration')}
        results.append(row)
        (OUT / 'results.json').write_text(json.dumps(results, indent=2))
        print(json.dumps(row), flush=True)
    hashes = {}
    selection = '+'.join(f'eq(n\\,{n})' for n in FRAMES)
    for name, _, _ in cases:
        video = OUT / f'{name}.mp4'
        md5 = OUT / f'{name}.framemd5'
        call([FFMPEG, '-y', '-v', 'error', '-threads', '1', '-i', video,
              '-map', '0:v:0', '-an', '-pix_fmt', 'rgb24', '-f', 'framemd5', md5], log=OUT / f'{name}-decode.log')
        hashes[name] = digest_rows(md5)
        images = OUT / name
        images.mkdir()
        call([FFMPEG, '-y', '-v', 'error', '-threads', '1', '-i', video,
              '-vf', 'select=' + selection, '-fps_mode', 'passthrough',
              images / 'sample-%02d.png'], log=OUT / f'{name}-samples.log')
    comparisons = []
    for left, right in ((cases[0][0], cases[1][0]), (cases[0][0], cases[2][0])):
        mismatch = [i for i, (a, b) in enumerate(zip(hashes[left], hashes[right])) if a != b]
        comparison = {'left': left, 'right': right, 'equal_decoded_frames': 240 - len(mismatch),
                      'total_frames': 240, 'mismatched_frame_indices': mismatch}
        if mismatch:
            for metric in ('psnr', 'ssim'):
                stats = OUT / f'{left}-vs-{right}-{metric}.stats'
                filt = (f'[0:v]select={selection},setpts=N/30/TB[a];'
                        f'[1:v]select={selection},setpts=N/30/TB[b];'
                        f'[a][b]{metric}=stats_file={stats.name}')
                summary = call([FFMPEG, '-v', 'info', '-threads', '1', '-i', OUT / f'{left}.mp4',
                                '-threads', '1', '-i', OUT / f'{right}.mp4', '-filter_complex', filt,
                                '-an', '-f', 'null', '-'], cwd=OUT,
                               log=OUT / f'{left}-vs-{right}-{metric}.log')
                comparison[metric + '_summary'] = [line for line in summary.splitlines()
                                                   if metric.upper() in line.upper()][-3:]
        comparisons.append(comparison)
    (OUT / 'comparisons.json').write_text(json.dumps(comparisons, indent=2))
    after = inventory(SOURCE)
    (OUT / 'source-hashes-after.json').write_text(json.dumps(after, indent=2))
    assert before == after, 'Production composition changed during diagnostic'
    print('DIAGNOSTIC COMPLETE ' + str(OUT), flush=True)


if __name__ == '__main__':
    main()
