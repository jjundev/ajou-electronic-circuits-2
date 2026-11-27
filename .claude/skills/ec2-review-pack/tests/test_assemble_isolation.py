"""scripts/assemble.py and workbook/assemble.py share a module name; neither may shadow the other.

Each check runs in a new interpreter (-E) so sys.modules starts empty, as in a pack_cli process.
"""
import re
import subprocess
import sys

import pytest

from _util import REPO, SCRIPTS

EPE_SCRIPTS = REPO / '.claude/skills/ec2-problem-explain/scripts'
WORKBOOK_ASSEMBLE = (REPO / 'workbook/assemble.py').resolve()
NOTE_ASSEMBLE = (SCRIPTS / 'assemble.py').resolve()


def run(code):
    result = subprocess.run([sys.executable, '-E', '-c', code], cwd=SCRIPTS,
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    return result.stdout


BIND_WORKBOOK_ASSEMBLE = (
    'import sys\n'
    f'sys.path.insert(0, {str(REPO / "workbook")!r})\n'
    'import assemble\n'
    'sys.path.pop(0)\n'
)


def test_receipt_chain_loads_after_the_note_module():
    out = run(
        'import sys\n'
        'sys.path.insert(0, ".")\n'
        'import assemble\n'
        'import publish_answer, epe_shared\n'
        f'from pathlib import Path\n'
        'print(Path(sys.modules["assemble"].__file__).resolve())\n'
        'print(epe_shared.TEXTBOOK_ID_RE.pattern)\n')
    bound, pattern = out.splitlines()
    assert bound == str(NOTE_ASSEMBLE)
    wb = run(BIND_WORKBOOK_ASSEMBLE + 'print(assemble.TEXTBOOK_ID_RE.pattern)\n').strip()
    assert pattern == wb


def test_note_module_loads_after_the_workbook_module():
    out = run(
        BIND_WORKBOOK_ASSEMBLE +
        'sys.path.insert(0, ".")\n'
        'import pack_parallel, pack_probe\n'
        'from pathlib import Path\n'
        'm = pack_probe.note_module()\n'
        'print(Path(m.__file__).resolve())\n'
        'print(all(hasattr(m, n) for n in ("read_fragment", "stage_problem_index", "assemble", "esc")))\n'
        'print(Path(sys.modules["assemble"].__file__).resolve())\n')
    note, complete, bound = out.splitlines()
    assert (note, complete, bound) == (str(NOTE_ASSEMBLE), 'True', str(WORKBOOK_ASSEMBLE))


def test_epe_shared_reuses_a_bound_workbook_module():
    out = run(
        BIND_WORKBOOK_ASSEMBLE +
        f'sys.path.insert(0, {str(EPE_SCRIPTS)!r})\n'
        'import epe_shared\n'
        'print(epe_shared.KIND_DIR is assemble.KIND_DIR)\n')
    assert out.strip() == 'True'


@pytest.mark.parametrize('path', [*sorted(SCRIPTS.glob('*.py')), EPE_SCRIPTS / 'epe_shared.py'],
                         ids=lambda p: p.name)
def test_no_product_module_imports_assemble_by_name(path):
    if path == NOTE_ASSEMBLE:
        pytest.skip('the note builder itself')
    text = path.read_text(encoding='utf-8')
    assert not re.search(r'^\s*(import assemble\b|from assemble import)', text, re.M)
