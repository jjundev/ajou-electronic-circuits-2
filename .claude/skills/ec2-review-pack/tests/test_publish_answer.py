"""Publication tests use synthetic evidence only; no real review is asserted."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[4]
# Keep paths.py's tool-directory setup intact for other workbook consumers.
# Append fixture search paths so review-pack's own modules keep precedence.
sys.path.append(str(REPO / 'workbook'))
sys.path.append(str(REPO / 'workbook/tests'))
from overlay_fixture import OverlayBundle, digest, dump

# Exercise the genuine publisher and loader in a fresh interpreter, matching
# the parent pack's CLI boundary and avoiding review-pack/workbook assemble
# module collisions. Only OS failures / timed source edits are injected.
PUBLISH_SCRIPT = REPO / '.claude/skills/ec2-review-pack/scripts/publish_answer.py'
WRAPPER = r"""
import json
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import publish_answer as publisher
repo, overlay, pdf, review, destination, backup = map(Path, sys.argv[2:8])
operation = sys.argv[8]
if operation == 'replace_error':
    def fail_replace(src, dst):
        assert Path(dst) == destination
        raise OSError('injected replace failure')
    publisher.os.replace = fail_replace
elif operation == 'source_after_review':
    original = publisher.load_answer_overlay
    calls = []
    def validate_then_change(*args, **kwargs):
        result = original(*args, **kwargs)
        calls.append(True)
        if len(calls) == 1:
            source = repo / '교과서/마이크로전자회로/ch09/예제/E9.05.md'
            source.write_text('Changed source after initial validation')
        return result
    publisher.load_answer_overlay = validate_then_change
elif operation == 'backup':
    def fail_copy(src, dst): raise OSError('injected backup failure')
    publisher.shutil.copyfile = fail_copy
elif operation == 'receipt':
    original = Path.write_text
    def fail_receipt(path, *args, **kwargs):
        if path.name == 'receipt.json': raise OSError('injected receipt failure')
        return original(path, *args, **kwargs)
    Path.write_text = fail_receipt
elif operation == 'temp':
    def fail_temp(*args, **kwargs): raise OSError('injected temp failure')
    publisher.tempfile.NamedTemporaryFile = fail_temp
elif operation == 'no_post_replace_writes':
    original_replace = publisher.os.replace
    original_write = Path.write_text
    replaced = []
    def checked_replace(src, dst):
        # Both backup and receipt must exist before replacement.
        assert (backup / destination.name).read_bytes() == b'old-pdf'
        assert json.loads((backup / 'receipt.json').read_text())['pdf_sha256']
        original_replace(src, dst)
        replaced.append(True)
    def checked_write(path, *args, **kwargs):
        assert not replaced, 'required write after replacement'
        return original_write(path, *args, **kwargs)
    publisher.os.replace = checked_replace
    Path.write_text = checked_write
try:
    result = publisher.publish_answer(repo, overlay, pdf, review, destination, backup)
except (OSError, ValueError) as exc:
    print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}))
    raise SystemExit(1)
print(json.dumps({'result': str(result)}))
"""


def publish(bundle, operation=''):
    result = subprocess.run([sys.executable, '-c', WRAPPER, str(PUBLISH_SCRIPT.parent),
        *map(str, [bundle.repo, bundle.path, bundle.new_pdf, bundle.review_path,
                   bundle.destination, bundle.backup_dir]), operation], capture_output=True, text=True)
    assert result.stdout.strip(), result.stderr
    outcome = json.loads(result.stdout)
    if result.returncode:
        if outcome['error'] in ('OSError', 'FileNotFoundError', 'FileExistsError'):
            raise OSError(outcome['message'])
        raise ValueError(outcome['message'])
    return Path(outcome['result'])


@pytest.fixture
def publish_fixture(tmp_path):
    bundle = OverlayBundle(tmp_path)
    # Add the old answer only after the explanation bundle hashes are sealed.
    bundle.destination = bundle.stage / '복습문제_1008_샘플-답안.pdf'
    bundle.destination.write_bytes(b'old-pdf')
    run = tmp_path / 'RUN'
    run.mkdir()
    bundle.new_pdf = run / 'answers.pdf'
    bundle.new_pdf.write_bytes(b'%PDF-1.7\nsynthetic test PDF only\n%%EOF')
    png = run / 'page-1.png'
    png.write_bytes(bundle.asset.read_bytes())
    report = run / 'screen-review.md'
    report.write_text('Synthetic test evidence only; not an actual screen review.')
    bundle.review_path = run / 'review.json'
    bundle.review = {'schema_version': 1, 'pdf_sha256': digest(bundle.new_pdf),
        'overlay_sha256': digest(bundle.path),
        'learning_style_sha256': bundle.overlay['learning_style']['sha256'],
        'status': 'pass', 'reviewer': 'synthetic test fixture only',
        'evidence': [{'path': p.name, 'sha256': digest(p)} for p in (png, report)],
        'overflow': []}
    dump(bundle.review_path, bundle.review)
    bundle.backup_dir = tmp_path / 'backup-unique'
    bundle.publish = lambda operation='': publish(bundle, operation)
    return bundle


@pytest.mark.parametrize('failure', ['pdf_changed', 'overlay_changed', 'overflow', 'not_run',
    'missing_evidence', 'outside_destination', 'wrong_pack_destination', 'replace_error',
    'profile_changed', 'evidence_changed', 'missing_png', 'missing_report', 'bad_schema', 'empty_reviewer'])
def test_failed_publish_preserves_existing_pdf(publish_fixture, failure):
    b = publish_fixture
    old_destination = b.destination
    if failure == 'pdf_changed': b.new_pdf.write_bytes(b'changed')
    elif failure == 'overlay_changed': b.path.write_bytes(b.path.read_bytes() + b' ')
    elif failure == 'overflow': b.review['overflow'] = ['page 1']
    elif failure == 'not_run': b.review['status'] = 'not_run'
    elif failure == 'missing_evidence': b.review['evidence'] = []
    elif failure == 'outside_destination': b.destination = b.repo.parent / b.destination.name
    elif failure == 'wrong_pack_destination': b.destination = b.stage / '복습문제_1008_other-답안.pdf'
    elif failure == 'profile_changed': b.source_files[-1].write_text('Changed style')
    elif failure == 'evidence_changed': (b.review_path.parent / 'page-1.png').write_bytes(b'changed')
    elif failure == 'missing_png': b.review['evidence'] = b.review['evidence'][1:]
    elif failure == 'missing_report': b.review['evidence'] = b.review['evidence'][:1]
    elif failure == 'bad_schema': b.review['schema_version'] = 2
    elif failure == 'empty_reviewer': b.review['reviewer'] = '  '
    dump(b.review_path, b.review)
    with pytest.raises((ValueError, OSError)):
        b.publish('replace_error' if failure == 'replace_error' else '')
    assert old_destination.read_bytes() == b'old-pdf'
    assert not list(old_destination.parent.glob('.answer-*.tmp'))


def test_success_keeps_verified_backup(publish_fixture):
    b = publish_fixture
    backup = b.publish()
    assert backup.read_bytes() == b'old-pdf'
    assert backup.parent == b.backup_dir
    assert b.destination.read_bytes() == b.new_pdf.read_bytes()
    receipt = json.loads((b.backup_dir / 'receipt.json').read_text())
    assert receipt['pdf_sha256'] == digest(b.new_pdf)
    assert receipt['overlay_sha256'] == digest(b.path)
    assert receipt['review_sha256'] == digest(b.review_path)
    assert receipt['learning_style_sha256'] == b.review['learning_style_sha256']
    assert receipt['backup'] == str(backup)
    assert receipt['backup_sha256'] == digest(backup)


def test_missing_old_pdf_installs_and_records_receipt(publish_fixture):
    b = publish_fixture
    b.destination.unlink()
    result = b.publish()
    assert result == b.backup_dir / 'receipt.json'
    receipt = json.loads(result.read_text())
    assert receipt['backup'] is None and receipt['backup_sha256'] is None
    assert b.destination.read_bytes() == b.new_pdf.read_bytes()


def test_publication_rechecks_source_after_review(publish_fixture):
    b = publish_fixture
    with pytest.raises(ValueError): b.publish('source_after_review')
    assert b.destination.read_bytes() == b'old-pdf'
    assert not list(b.stage.glob('.answer-*.tmp'))


@pytest.mark.parametrize('operation', ['backup', 'receipt', 'temp'])
def test_preparation_failure_preserves_old_pdf(publish_fixture, operation):
    b = publish_fixture
    with pytest.raises(OSError): b.publish(operation)
    assert b.destination.read_bytes() == b'old-pdf'
    assert not list(b.stage.glob('.answer-*.tmp'))


def test_all_required_writes_finish_before_replacement(publish_fixture):
    b = publish_fixture
    assert b.publish('no_post_replace_writes').read_bytes() == b'old-pdf'
    assert b.destination.read_bytes() == b.new_pdf.read_bytes()


def test_existing_backup_directory_is_not_reused(publish_fixture):
    b = publish_fixture
    b.backup_dir.mkdir()
    (b.backup_dir / 'keep').write_bytes(b'keep')
    with pytest.raises((ValueError, OSError)): b.publish()
    assert (b.backup_dir / 'keep').read_bytes() == b'keep'
    assert b.destination.read_bytes() == b'old-pdf'


def test_cli_publishes_with_real_loader(publish_fixture):
    b = publish_fixture
    result = subprocess.run([sys.executable, str(REPO / '.claude/skills/ec2-review-pack/scripts/publish_answer.py'),
        '--repo', str(b.repo), '--overlay', str(b.path), '--pdf', str(b.new_pdf), '--review', str(b.review_path),
        '--destination', str(b.destination), '--backup-dir', str(b.backup_dir)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()).read_bytes() == b'old-pdf'
    assert b.destination.read_bytes() == b.new_pdf.read_bytes()
