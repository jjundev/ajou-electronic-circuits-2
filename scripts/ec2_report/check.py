"""보고서 md 를 노션에 올리기 전·후에 검사한다.

규칙 출처는 논회실 `scripts/lab/validate.py` (`_NFM_LOSSY`, `check_report_wrapping`,
`check_notion_markdown`). 노션 왕복은 파이프 표를 `<table>` 로, 인라인 수식
`$x$` 를 ``$`x`$`` 로 돌려준다 — 이 둘은 손실이 아니라 형태 변화로 센다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

AI_WORDS = re.compile(r"Claude|ChatGPT|(?<![A-Za-z])GPT(?![A-Za-z])|Gemini|OpenAI|Anthropic|Copilot"
                      r"|생성형|인공지능|LLM|(?<![A-Za-z])AI(?![A-Za-z])")

_H5 = re.compile(r"^#{5,}\s")
_HEADING = re.compile(r"^#{1,6}\s")
_FOOTNOTE = re.compile(r"\[\^[^\]]+\]")
# 노션이 입력으로도 받는 자체 블록 태그 (논회실 `_NFM_BLOCK_TAGS`). 원시 HTML 이 아니다.
_NFM_BLOCK_TAGS = ("table_of_contents", "empty-block")
_RAW_HTML = re.compile(rf"^<(?!/?(?:{'|'.join(_NFM_BLOCK_TAGS)})\b)[a-zA-Z]")
_TABLE_SEP = re.compile(r"^\|[\s:|-]+\|$")
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_LINE_BLOCK = re.compile(r"\$\$.*?\$\$")
_INLINE_MATH = re.compile(r"\$`?[^$\n]+?`?\$")
_IMAGE_LOCAL = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_IMAGE_ANY = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
_ORDERED = re.compile(r"^\d+\.")
# `2-(a)` 꼴 문항 참조. 대절 헤딩에 번호가 없으므로 'Spice Problem (a)' 처럼 이름으로 쓴다.
_OLD_REF = re.compile(r"(?<![\w.])\d-\([a-z]\)")
_CAPTION_ALT = re.compile(r"!\[(그림\s*\d+\.[^\]]*)\]\(")
_NOT_PROSE = ("#", "|", "-", "*", ">", "!", "<", "$$")
MAX_COLUMNS = 11
FIG_DIR = "figs"  # 보고서 그림은 md 옆 figs/ 한 폴더에만 둔다
_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

_LABELS = {"headings": "헤딩", "tables": "표", "math_blocks": "수식 블록",
           "inline_math": "인라인 수식", "images": "그림"}


@dataclass(frozen=True)
class Finding:
    level: str
    where: str
    msg: str

    def __str__(self) -> str:
        return f"{self.level} {self.where}: {self.msg}"


def _is_block_fence(line: str) -> bool:
    return line.strip() == "$$"


def _is_code_fence(line: str) -> bool:
    return line.lstrip().startswith(("```", "~~~"))


def _block_mask(lines: list[str]) -> list[bool]:
    """줄마다 `$$` 수식 블록이나 코드 펜스의 구분 줄·안쪽이면 True."""
    mask, state = [], None
    for line in lines:
        if state is None and _is_code_fence(line):
            state = "code"
            mask.append(True)
        elif state is None and _is_block_fence(line):
            state = "math"
            mask.append(True)
        elif state == "code" and _is_code_fence(line):
            state = None
            mask.append(True)
        elif state == "math" and _is_block_fence(line):
            state = None
            mask.append(True)
        else:
            mask.append(state is not None)
    return mask


def _math_fences(lines: list[str]) -> int:
    """코드 펜스 밖의 단독 `$$` 줄 개수."""
    n, in_code = 0, False
    for line in lines:
        if _is_code_fence(line):
            in_code = not in_code
        elif not in_code and _is_block_fence(line):
            n += 1
    return n


def _cells(line: str) -> list[str]:
    return _CELL_SPLIT.split(line.strip())[1:-1]


def _is_prose(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith(_NOT_PROSE) and not _ORDERED.match(s)


def _check_tables(lines: list[str], name: str) -> list[Finding]:
    out = []
    for i in range(len(lines) - 1):
        if not (lines[i].startswith("|") and _TABLE_SEP.match(lines[i + 1].strip())):
            continue
        width = len(_cells(lines[i]))
        if width > MAX_COLUMNS:
            out.append(Finding("error", f"{name}:{i + 1}행",
                f"표가 {width}열이다 — 노션 PDF 에서 잘린다 ({MAX_COLUMNS}열 이하)"))
        j = i + 2
        while j < len(lines) and lines[j].startswith("|"):
            n = len(_cells(lines[j]))
            if n != width:
                out.append(Finding("error", f"{name}:{j + 1}행",
                    f"표 행의 셀이 {n}개인데 헤더는 {width}개다 — 노션에서 표가 뭉개진다"))
            j += 1
    return out


def check_markdown(path: Path) -> list[Finding]:
    path = Path(path)
    name = path.name
    lines = path.read_text(encoding="utf-8").splitlines()
    mask = _block_mask(lines)
    out: list[Finding] = []

    fences = _math_fences(lines)
    if fences % 2:
        out.append(Finding("error", name,
            f"단독 $$ 줄이 {fences}개다 — 수식 블록이 닫히지 않았다"))

    footnotes = 0
    for i, line in enumerate(lines, start=1):
        m = AI_WORDS.search(line)
        if m:
            out.append(Finding("error", f"{name}:{i}행",
                f"{i}행에 AI 관련 낱말 '{m.group()}' 이 있다 — 보고서에 쓰지 않는다"))
        if mask[i - 1]:
            continue
        where = f"{name}:{i}행"
        if _H5.match(line):
            out.append(Finding("error", where, "h5 이상 헤딩은 노션이 h4 로 강등한다"))
        if _HEADING.match(line) and "`" in line:
            out.append(Finding("error", where, "헤딩 안 백틱은 노션에서 코드 서식으로 남는다"))
        if line.startswith("▶"):
            out.append(Finding("error", where,
                "줄 맨 앞 ▶ 는 노션이 토글 블록으로 바꾼다 — **▶** 로 쓴다 (docs/notion-probe.md)"))
        if _RAW_HTML.match(line):
            out.append(Finding("error", where, "열 0 의 원시 HTML 은 노션이 받지 않는다"))
        for ref in _OLD_REF.findall(line):
            out.append(Finding("error", where,
                f"문항을 '{ref}' 처럼 번호로 가리킨다 — 대절 헤딩에 번호가 없으므로 "
                "'Spice Problem (a)', 'Design Problem (a)' 처럼 대절 이름으로 쓴다"))
        for alt in _CAPTION_ALT.findall(line):
            out.append(Finding("warn", where,
                f"그림 설명이 '{alt}' 로 시작한다 — 노션이 이것을 캡션으로 다는데, 이미지 안에 "
                "이미 캡션이 있으면 두 번 나온다. 그런 그림은 ![](…) 로 비운다"))
        footnotes += len(_FOOTNOTE.findall(line))
        bare = _LINE_BLOCK.sub("", line.replace("\\$", ""))
        if bare.count("$") % 2:
            out.append(Finding("error", where, "인라인 수식의 $ 짝이 맞지 않는다"))
    if footnotes:
        out.append(Finding("error", name, f"각주가 {footnotes}곳 있다 — 노션이 지원하지 않는다"))

    out.extend(_check_tables(lines, name))

    wraps = [i + 1 for i in range(len(lines) - 1)
             if not mask[i] and not mask[i + 1]
             and _is_prose(lines[i]) and _is_prose(lines[i + 1])]
    if wraps:
        out.append(Finding("error", name,
            f"산문 줄이 {len(wraps)}곳에서 접혀 있다 (첫 자리 {wraps[0]}행) — "
            "노션은 줄바꿈을 그대로 렌더하므로 문단은 한 줄로 쓴다"))

    local = [t for t in _IMAGE_LOCAL.findall("\n".join(lines))
             if not t.startswith(("http://", "https://", "data:"))]
    for k, t in enumerate(local, start=1):
        if not re.fullmatch(rf"{FIG_DIR}/[^/]+", t):
            out.append(Finding("error", name,
                f"그림 '{t}' 이 {FIG_DIR}/ 밖에 있다 — 노션에 넣을 그림은 md 옆 {FIG_DIR}/ 한 폴더에 모은다"))
        elif not Path(t).name.startswith(f"{k:02d}_"):
            out.append(Finding("error", name,
                f"그림 '{t}' 은 본문 {k}번째 그림이다 — 파일 이름을 '{k:02d}_<이름>' 으로 한다 "
                "(번호는 본문에 나오는 순서, 노션에 넣는 순서)"))
    fig_dir = path.parent / FIG_DIR
    if fig_dir.is_dir():
        used = {Path(t).name for t in local}
        extra = sorted(f.name for f in fig_dir.iterdir()
                       if f.suffix.lower() in _IMAGE_EXT and f.name not in used)
        if extra:
            out.append(Finding("warn", name,
                f"{FIG_DIR}/ 에 본문이 쓰지 않는 그림이 있다 — 치우거나 sim/ 쪽으로 옮긴다: " + ", ".join(extra)))
    if local:
        out.append(Finding("info", name,
            f"노션에서 직접 넣을 그림 {len(local)}장: " + ", ".join(local)))
    return out


def shape(text: str) -> dict[str, int]:
    lines = text.splitlines()
    fences = sum(1 for line in lines if _is_block_fence(line))
    rest = "\n".join(line for line in lines if not _is_block_fence(line))
    rest = _LINE_BLOCK.sub("", rest.replace("\\$", ""))
    return {
        "headings": sum(1 for line in lines if re.match(r"^#{1,4}\s", line)),
        "tables": sum(1 for line in lines if _TABLE_SEP.match(line.strip()))
                  + len(re.findall(r"<table\b", text, re.IGNORECASE)),
        "math_blocks": fences // 2,
        "inline_math": len(_INLINE_MATH.findall(rest)),
        "images": len(re.findall(r"!\[", text)),
    }


def roundtrip(src: str, baseline: str) -> list[Finding]:
    a, b = shape(src), shape(baseline)
    return [Finding("error", "왕복",
                    f"{_LABELS[k]} 개수가 {a[k]}개에서 {b[k]}개로 줄었다")
            for k in _LABELS if b[k] < a[k]]


def check_pulled_images(text: str) -> list[Finding]:
    return [Finding("error", "노션 그림", f"그림 빈자리: {alt or '(캡션 없는 그림)'}")
            for alt, target in _IMAGE_ANY.findall(text)
            if not target.strip().startswith(("http://", "https://"))]
