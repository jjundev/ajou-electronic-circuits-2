"""Narrow adapter to the repo's workbook, Markdown and HTML-check APIs."""
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
# ec2-review-pack/scripts also has an assemble.py, so import the workbook modules first and
# append that directory last: html2md/check_html import neither assemble nor problem.
for _path in (REPO / 'workbook', REPO / '.claude/skills/ec2-review-pack/scripts'):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

from problem import (load_problem, html_fields, problem_figures, solution, ProblemError,
                     textbook_figure_filename, exam_figure_filename)  # noqa: E402
from assemble import TEXTBOOK_ID_RE, EXAM_ID_RE, KIND_DIR  # noqa: E402
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
