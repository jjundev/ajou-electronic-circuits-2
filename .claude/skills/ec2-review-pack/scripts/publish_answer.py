#!/usr/bin/env python3
"""Bind review evidence and atomically install an answer PDF in its owning pack.

This checks review records and hashes; it does not perform a screen, semantic,
source, or mathematical review on behalf of the recorded reviewer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

_WORKBOOK = Path(__file__).resolve().parents[4] / 'workbook'
sys.path.insert(0, str(_WORKBOOK))
from answer_overlay import load_answer_overlay  # noqa: E402


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    _require(isinstance(value, dict), f'JSON object required: {path}')
    return value


def _review(review_path, pdf_path, overlay_path, overlay):
    review = _object(review_path)
    _require(type(review.get('schema_version')) is int and review['schema_version'] == 1,
             'Unsupported review schema_version')
    _require(review.get('status') == 'pass', 'A passing screen review is required')
    _require(isinstance(review.get('reviewer'), str) and review['reviewer'].strip(),
             'A named reviewer is required')
    _require(review.get('overflow') == [], 'Review must record no overflow')
    for key, expected in [('pdf_sha256', _digest(pdf_path)),
                          ('overlay_sha256', _digest(overlay_path)),
                          ('learning_style_sha256', overlay['learning_style']['sha256'])]:
        _require(review.get(key) == expected, f'Review hash mismatch: {key}')
    evidence = review.get('evidence')
    _require(isinstance(evidence, list) and evidence, 'Review evidence is required')
    suffixes = set()
    seen = set()
    for item in evidence:
        _require(isinstance(item, dict) and isinstance(item.get('path'), str)
                 and item['path'].strip(), 'Evidence file path required')
        name = Path(item['path'])
        _require(not name.is_absolute(), 'Evidence paths must be review-relative')
        file = (review_path.parent / name).resolve(strict=True)
        _require(file.is_file() and file not in seen, 'Evidence must name distinct files')
        _require(item.get('sha256') == _digest(file), f'Evidence changed: {name}')
        seen.add(file)
        suffixes.add(file.suffix.lower())
    _require('.png' in suffixes, 'Rendered page PNG evidence required')
    _require(bool(suffixes & {'.md', '.txt', '.html', '.json'}), 'Review report evidence required')
    return review


def publish_answer(repo: Path, overlay_path: Path, pdf_path: Path, review_path: Path,
                   destination: Path, backup_dir: Path) -> Path:
    """Return verified old-PDF backup, or receipt.json when first installing.

    All fallible preparation completes before os.replace. Failed preparation or
    replacement preserves the destination; completed backup/receipt evidence is
    retained and a temporary destination-side file is removed on failure.
    """
    repo = Path(repo).resolve(strict=True)
    overlay_path = Path(overlay_path).absolute()
    pdf_path = Path(pdf_path).resolve(strict=True)
    review_path = Path(review_path).resolve(strict=True)
    raw = _object(overlay_path)
    problems = raw.get('problems')
    _require(isinstance(problems, list) and all(isinstance(p, dict) and 'id' in p for p in problems),
             'Overlay problem IDs required')
    ids = [p['id'] for p in problems]
    overlay = load_answer_overlay(overlay_path, repo, ids)
    overlay_path = overlay_path.resolve(strict=True)
    expected = overlay_path.parent.parent.parent / f"복습문제_{overlay['range']}_{overlay['slug']}-답안.pdf"
    destination = Path(destination).absolute()
    _require(not destination.is_symlink() and destination.resolve() == expected,
             'Destination must be the exact owning pack answer PDF')
    destination = expected
    _require(pdf_path != destination, 'Input PDF must be a separate temporary result')
    review = _review(review_path, pdf_path, overlay_path, overlay)
    review_hash = _digest(review_path)
    pdf_bytes = pdf_path.read_bytes()
    _require(hashlib.sha256(pdf_bytes).hexdigest() == review['pdf_sha256'], 'PDF changed during validation')
    old_hash = _digest(destination) if destination.exists() else None
    backup_dir = Path(backup_dir).absolute()
    backup_dir.mkdir(parents=True, exist_ok=False)
    backup = backup_dir / destination.name if old_hash is not None else None
    temp_path = None
    try:
        if backup is not None:
            shutil.copyfile(destination, backup)
            _require(_digest(backup) == old_hash, 'Backup verification failed')
        with tempfile.NamedTemporaryFile(prefix='.answer-', suffix='.tmp', dir=destination.parent,
                                         delete=False) as temp:
            temp_path = Path(temp.name)
            temp.write(pdf_bytes)
            temp.flush()
            os.fsync(temp.fileno())
        _require(_digest(temp_path) == review['pdf_sha256'], 'Temporary PDF verification failed')
        receipt = backup_dir / 'receipt.json'
        receipt.write_text(json.dumps({'schema_version': 1, 'destination': str(destination),
            'pdf_sha256': review['pdf_sha256'], 'overlay_sha256': review['overlay_sha256'],
            'learning_style_sha256': review['learning_style_sha256'], 'review_sha256': review_hash,
            'backup': str(backup) if backup else None, 'backup_sha256': old_hash},
            ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # Validate current source/style/reviews again after preparing all outputs.
        load_answer_overlay(overlay_path, repo, ids)
        _require(_digest(review_path) == review_hash, 'Review record changed during preparation')
        _review(review_path, pdf_path, overlay_path, overlay)
        _require(not destination.is_symlink(), 'Destination became a symlink')
        current_old_hash = _digest(destination) if destination.exists() else None
        _require(current_old_hash == old_hash, 'Destination changed during preparation')
        result = backup if backup is not None else receipt
        os.replace(temp_path, destination)
    except BaseException:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('repo', 'overlay', 'pdf', 'review', 'destination', 'backup-dir'):
        parser.add_argument('--' + option, required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = publish_answer(args.repo, args.overlay, args.pdf, args.review,
                                args.destination, args.backup_dir)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Publication failed: {exc}\n')
    print(result)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
