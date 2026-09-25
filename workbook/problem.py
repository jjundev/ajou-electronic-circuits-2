"""문제 md 한 개 → 문제집 JSON 항목의 재료 (제목, html 절, 그림, 힌트, 풀이).

교과서(FORMAT.md)와 기출(FORMAT-EXAM.md) md를 모두 읽는다. 문제집용 절 규칙은 FORMAT.md '문제집용 절'.
"""
import base64
import re
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

import paths  # noqa: F401  (기존 도구 import 경로 설정)
from check_md import (HINT_FORMULA_RE, check_workbook_sections, split_frontmatter,
                      split_sections, split_subsections)
from crop_exam import figure_filename as exam_figure_filename
from crop_figures import figure_filename as textbook_figure_filename
from mdsub import answer_html, inline, to_html

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
# 작성자 보충 표시: 한 줄 안의 (…) 가운데 안쪽 괄호가 없고 이 말이 든 것
MARKER_RE = re.compile(r"[ \t]*\([^()\n]*(?:원문에 없음|원문의 |보조 출처)[^()\n]*\)")
MASK_RE = re.compile(r"\x00(\d+)\x00")
REQUIRED_KEYS = ("id", "kind", "number")


class ProblemError(Exception):
    pass


@dataclass
class Problem:
    path: Path
    meta: dict
    sections: list      # [(제목, 내용)]
    title: str

    @property
    def id(self):
        return str(self.meta["id"])

    @property
    def is_exam(self):
        return self.meta["kind"] == "기출"

    @property
    def figures_dir(self):
        return self.path.parent / "figures" if self.is_exam else self.path.parent.parent / "figures"

    def section(self, name):
        """제목이 name인 첫 절의 내용. 없으면 None."""
        return next((c for t, c in self.sections if t == name), None)


def load_problem(path):
    path = Path(path)
    try:
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError) as e:
        raise ProblemError(str(e)) from e
    missing = [k for k in REQUIRED_KEYS if k not in meta]
    if missing:
        raise ProblemError(f"frontmatter 키 누락: {', '.join(missing)}")
    errors = check_workbook_sections(body)
    if errors:
        raise ProblemError("; ".join(errors))
    h1 = next((line for line in body.splitlines() if line.startswith("# ")), None)
    if not h1 or " — " not in h1:
        raise ProblemError("H1 '# <종류> <번호> — <제목>' 없음")
    return Problem(path, meta, split_sections(body), h1.split(" — ", 1)[1].strip())


@lru_cache(maxsize=None)
def exam_info(exam_dir):
    return yaml.safe_load((Path(exam_dir) / "exam.yaml").read_text(encoding="utf-8")) or {}


def strip_markers(md):
    """작성자 보충 표시를 지운다. 수식을 먼저 가려 두므로 수식 안은 그대로이고, 수식을 품은 표시도 지워진다."""
    maths = []

    def mask(m):
        maths.append(m.group(0))
        return f"\x00{len(maths) - 1}\x00"

    masked = MARKER_RE.sub("", MATH_RE.sub(mask, md))
    return MASK_RE.sub(lambda m: maths[int(m.group(1))], masked)


def drop_circuit_lines(md):
    """'- 회로:' 줄과 그 아래 들여쓴 줄을 뺀다 (문제 그림이 PDF에 함께 나오므로)."""
    out, skipping = [], False
    for line in md.splitlines():
        if line.startswith("- 회로:"):
            skipping = True
            continue
        if skipping and line.startswith(" "):
            continue
        skipping = False
        out.append(line)
    return "\n".join(out)


def example_answer_md(text):
    """'## 답 (검증용)'에서 답 글만: '### ' 소절이나 코드 블록 앞까지, '> ' 메모 줄은 뺀다."""
    keep = []
    for line in text.splitlines():
        if line.startswith("### ") or line.startswith("```"):
            break
        if not line.startswith("> "):
            keep.append(line)
    return "\n".join(keep).strip()


def problem_figure_ids(p):
    ids = []
    for fig in p.meta.get("figures") or []:
        fig_id = str(fig.get("id"))
        if fig.get("role") == "problem" and fig_id not in ids:
            ids.append(fig_id)
    return ids


def html_fields(p):
    fields = {}
    original = p.section("원문")
    if original is not None:
        fields["original"] = to_html(original)
    conditions = p.section("조건") or ""
    if problem_figure_ids(p):
        conditions = drop_circuit_lines(conditions)
    fields["conditions"] = to_html(strip_markers(conditions))
    fields["ask"] = to_html(strip_markers(p.section("구할 것") or ""))
    return fields


@lru_cache(maxsize=None)
def _figures_dpi(fig_dir):
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
    return spec.get("dpi", 144)


def png_size(data):
    if data[:8] != PNG_SIGNATURE:
        raise ProblemError("PNG 파일이 아님")
    return struct.unpack(">II", data[16:24])


def figures(p):
    """문제 그림(role: problem)을 base64 data URI와 인쇄 크기(mm)로. mm = 픽셀 / dpi × 25.4."""
    name = exam_figure_filename if p.is_exam else textbook_figure_filename
    out = []
    for fig_id in problem_figure_ids(p):
        png = p.figures_dir / name(fig_id)
        if not png.exists():
            raise ProblemError(f"그림 파일 없음: {png}")
        try:
            dpi = _figures_dpi(p.figures_dir)
        except FileNotFoundError as e:
            raise ProblemError(f"figures.yaml 없음: {p.figures_dir}") from e
        data = png.read_bytes()
        w, h = png_size(data)
        out.append({"src": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
                    "w_mm": round(w / dpi * 25.4, 1), "h_mm": round(h / dpi * 25.4, 1)})
    return out


def hints(p):
    text = p.section("힌트")
    if not text:
        return []
    out = []
    for label, body in split_subsections(text):
        formula, lines = None, []
        for line in body.splitlines():
            m = HINT_FORMULA_RE.match(line.rstrip())
            if m:
                formula = m.group(1).strip()
            else:
                lines.append(line)
        hint = {"label": inline(label), "html": to_html("\n".join(lines))}
        if formula:
            hint["formula"] = formula
        out.append(hint)
    return out


def solution(p):
    """'## 풀이'가 있으면 단계와 답. 없고 예제면 '## 답 (검증용)'의 답만. 둘 다 없으면 None."""
    text = p.section("풀이")
    if text:
        subs = split_subsections(text)
        return {"steps": [{"label": inline(label), "html": to_html(body)} for label, body in subs[:-1]],
                "answer": answer_html(subs[-1][1])}
    if p.meta["kind"] == "예제":
        answer = p.section("답 (검증용)")
        if answer:
            return {"steps": [], "answer": answer_html(strip_markers(example_answer_md(answer)))}
    return None
