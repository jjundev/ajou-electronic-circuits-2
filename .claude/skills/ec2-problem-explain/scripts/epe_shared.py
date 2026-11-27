"""Narrow adapter to the repo's workbook, Markdown and HTML-check APIs."""
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
# ec2-review-pack/scripts also has an assemble.py; whichever a process imports first owns the
# name `assemble`, so workbook/assemble.py is loaded by path below. html2md/check_html come
# from the review-pack directory, appended last; they import neither assemble nor problem.
for _path in (REPO / 'workbook', REPO / '.claude/skills/ec2-review-pack/scripts'):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

from problem import (load_problem, html_fields, problem_figures, solution, ProblemError,
                     textbook_figure_filename, exam_figure_filename)  # noqa: E402


def workbook_assemble():
    """workbook/assemble.py, reusing it when already bound to `assemble`; never binds that name."""
    import importlib.util
    path = (REPO / 'workbook' / 'assemble.py').resolve()
    loaded = sys.modules.get('assemble')
    if loaded is not None and Path(getattr(loaded, '__file__', '') or '.').resolve() == path:
        return loaded
    loaded = sys.modules.get('ec2_workbook_assemble')
    if loaded is None:
        spec = importlib.util.spec_from_file_location('ec2_workbook_assemble', path)
        loaded = importlib.util.module_from_spec(spec)
        sys.modules['ec2_workbook_assemble'] = loaded
        try:
            spec.loader.exec_module(loaded)
        except BaseException:
            del sys.modules['ec2_workbook_assemble']
            raise
    return loaded


_wb = workbook_assemble()
TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR = _wb.TEXTBOOK_ID_RE, _wb.EXAM_ID_RE, _wb.KIND_DIR
del _wb

from html2md import Builder, Node, Ctx, VOID, serialize, convert, check_md  # noqa: E402
from check_html import check_location_marks, math_delimiter_errors  # noqa: E402
from learning_style import (StyleSnapshot, StyleAudit, LearningStyleError, read_style,
                            check_style, validate_style_audit, PERSONALIZED_REVIEW_POLICY, STYLE_PATH)  # noqa: E402


def parse(text):
    parser = Builder()
    parser.feed(text)
    return parser.root


def outer(node):
    if isinstance(node, str):
        return html.escape(node, quote=False)
    if node.tag == 'svg':
        return serialize(node)
    attrs = ''.join(f' {k}="{html.escape(v, quote=True)}"' for k, v in node.attrs.items())
    start = f'<{node.tag}{attrs}>'
    return start if node.tag in VOID else start + inner(node) + f'</{node.tag}>'


def inner(node, skip_summary=False):
    return ''.join(outer(c) for c in node.children
                   if not (skip_summary and isinstance(c, Node) and c.tag == 'summary'))


def compact(s):
    return re.sub(r'\s+', '', parse(s).text())
