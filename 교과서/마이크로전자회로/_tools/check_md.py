#!/usr/bin/env python3
"""교과서 문제 md 형식 검사기. 규칙은 ../FORMAT.md.

사용법: python3 check_md.py <장 폴더>    예) python3 check_md.py ../ch09
오류가 하나라도 있으면 종료 코드 1.
"""
import re
import sys
import unicodedata
from pathlib import Path

import yaml

from crop_figures import CROP_NAME_RE, figure_filename

KIND_BY_PREFIX = {"E": "예제", "X": "연습문제", "P": "장말문제"}
REQUIRED_KEYS = ["id", "kind", "number", "section", "book_page", "pdf_page",
                 "source_lang", "figures", "depends_on", "refs"]
FIGURE_ROLES = {"problem", "answer"}
ID_RE = re.compile(r"^([EXP])(\d+)\.(\d{2})$")

NODE = r"[A-Za-z0-9_]+"
NUM = r"\d+(\.\d+)?"
SYM = r"\{[^\s{}]+\}"          # {n}, {(W/L)_n}: 중괄호 안에 공백·중괄호 없음
MULT = rf"(\s+m=({NUM}|{SYM}))?"
NETLIST_RES = [
    re.compile(rf"^Q\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+(npn|pnp)(\s+area=({NUM}|{SYM}))?{MULT}$"),
    re.compile(rf"^M\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+(nmos|pmos)"
               rf"(\s+W/L=({NUM}/{NUM}|{SYM}))?{MULT}$"),
    re.compile(rf"^[RCLIV]\w*\s+{NODE}\s+{NODE}(\s+\S+)?$"),
    re.compile(rf"^X\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+opamp$"),
    re.compile(rf"^X\w*(\s+{NODE}){{4}}\s+fdopamp$"),           # 완전 차동: in+ in- out+ out-
    re.compile(rf'^X\w*(\s+{NODE})+\s+box\s+"[^"]+"$'),
    re.compile(rf"^X\w*(\s+{NODE}){{3,}}\s+sum$"),                  # 블록도 덧셈기: 입력… 출력
    re.compile(rf'^X\w*\s+{NODE}\s+{NODE}\s+gain\s+"[^"]+"(\s+tri)?$'),
    re.compile(rf"^D\w*\s+{NODE}\s+{NODE}(\s+laser)?$"),
    re.compile(rf"^[EG]\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+{NODE}\s+\S+$"),  # 전압 제어 종속 전원
    re.compile(rf"^[FH]\w*\s+{NODE}\s+{NODE}\s+V\w*\s+\S+$"),           # 전류 제어: 제어 전압원 이름
]
SPICE_BLOCK_RE = re.compile(r"```spice\n(.*?)\n```", re.DOTALL)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
REQUIRED_BULLETS = ["- 단자:", "- 표시:", "- 배치:"]
NO_CIRCUIT_PREFIX = "## 회로 — 없음"
NO_CIRCUIT_RE = re.compile(r"^## 회로 — 없음 \(.+\)$")
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^### (.+)$", re.MULTILINE)
HINT_FORMULA_RE = re.compile(r"^> 띠: \$([^$]+)\$$")
HINT_STRIP_PREFIX = "> 띠:"
HINT_LABEL_MAX = 24     # 이름표는 문제지 Hint 띠(24mm, 7.5pt)에 그대로 보인다. 3줄쯤
HINT_MAX = 2
LABEL_MATH_RE = re.compile(r"\$([^$]+)\$")
TEX_WRAPPER_RE = re.compile(r"\\(text|mathrm|left|right)\b")
TEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+")
TEX_MARKUP_RE = re.compile(r"[{}_^\\\s]")
WORKBOOK_SECTIONS = ("원문", "힌트", "풀이")
WORKBOOK_TAIL = ("힌트", "풀이")
# 원문 절은 PDF에 그대로 나온다(작성자 표시를 지우지 않음). 수식을 가린 뒤 검사한다.
ORIGINAL_MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
ORIGINAL_MARKER_RE = re.compile(r"원문에 없음|보조 출처|\([^()\n]*원문의 ")
SINGLE_EMPHASIS_RE = re.compile(r"(?<![*\\])\*(?![*\s])[^*\n]+?(?<![*\s])\*(?!\*)")


def split_frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("frontmatter(---)로 시작하지 않음")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("frontmatter 닫는 --- 없음")
    return yaml.safe_load(text[4:end]) or {}, text[end + 5:]


def check_netlist_line(line):
    code = line.split(";", 1)[0].strip()
    if not code or code.startswith("*"):
        return None
    if any(r.match(code) for r in NETLIST_RES):
        return None
    return f"넷리스트 문법 오류: {code!r}"


def split_sections(body):
    """본문을 '## ' 절로 나눈다 → [(제목, 내용)]. 첫 '## ' 앞(H1)은 버린다. 문제집 생성기(workbook/)도 쓴다."""
    ms = list(SECTION_RE.finditer(body))
    ends = [m.start() for m in ms[1:]] + [len(body)]
    return [(m.group(1).strip(), body[m.end():end].strip("\n")) for m, end in zip(ms, ends)]


def split_subsections(text):
    """절 내용을 '### ' 소절로 나눈다 → [(제목, 내용)]. 첫 '### ' 앞에 글이 있으면 ("", 글)을 맨 앞에 둔다."""
    ms = list(SUBSECTION_RE.finditer(text))
    head = text[:ms[0].start()] if ms else text
    out = [("", head.strip("\n"))] if head.strip() else []
    ends = [m.start() for m in ms[1:]] + [len(text)]
    out += [(m.group(1).strip(), text[m.end():end].strip("\n")) for m, end in zip(ms, ends)]
    return out


def check_original(text):
    """## 원문 내용: 인쇄된 문장만. 작성자 표시·*기울임*·### 소절·이미지 줄은 쓰지 않는다."""
    errors = []
    plain = ORIGINAL_MATH_RE.sub("", text)
    if ORIGINAL_MARKER_RE.search(plain):
        errors.append("## 원문: 작성자 표시(원문에 없음, (원문의 …, 보조 출처)는 넣지 않음 — ## 조건에 적음")
    if SINGLE_EMPHASIS_RE.search(plain):
        errors.append("## 원문: *기울임* 강조는 쓰지 않음 (PDF에 별표가 그대로 나옴)")
    lines = text.splitlines()
    if any(line.startswith("### ") for line in lines):
        errors.append("## 원문: ### 소절을 두지 않음")
    if any(line.lstrip().startswith("![") for line in lines):
        errors.append("## 원문: 이미지 줄을 두지 않음")
    return errors


def hint_label_length(label):
    """띠에 보이는 글자 수. 수식 안은 \\mu 같은 명령을 한 글자로, \\text 같은 감싸개와 중괄호·첨자 기호·공백은 0으로 센다."""
    def visible(m):
        tex = TEX_WRAPPER_RE.sub("", m.group(1))
        return TEX_MARKUP_RE.sub("", TEX_COMMAND_RE.sub("x", tex))
    return len(unicodedata.normalize("NFC", LABEL_MATH_RE.sub(visible, label)))


def check_hint(label, text):
    """## 힌트의 ### 소절 하나: 띠 식 줄은 소절당 하나, 들여 쓰지 않고, 이름표는 HINT_LABEL_MAX자까지."""
    errors = []
    strips = [line for line in text.splitlines() if line.lstrip().startswith(HINT_STRIP_PREFIX)]
    for line in strips:
        if line != line.lstrip():
            errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 들여 쓰지 않음 ({line.strip()!r})")
        elif not HINT_FORMULA_RE.match(line.rstrip()):
            errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 '> 띠: $<LaTeX>$' 형식 ({line.strip()!r})")
    if len(strips) > 1:
        errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 소절에 하나만 ({len(strips)}개)")
    n = hint_label_length(label)
    if n > HINT_LABEL_MAX:
        errors.append(f"## 힌트 / ### {label}: 이름표는 {HINT_LABEL_MAX}자까지 (지금 {n}자) — 문제지 띠에 그대로 보임")
    return errors


def check_workbook_sections(body):
    """문제집용 선택 절(## 원문, ## 힌트, ## 풀이)의 위치와 모양. 규칙은 FORMAT.md '문제집용 절'."""
    errors = []
    sections = split_sections(body)
    titles = [t for t, _ in sections]
    for name in WORKBOOK_SECTIONS:
        if titles.count(name) > 1:
            errors.append(f"## {name} 절이 두 번 이상 있음")
    if "원문" in titles and titles[0] != "원문":
        errors.append("## 원문 은 H1 바로 다음 첫 절이어야 함")
    tail = [t for t in titles if t in WORKBOOK_TAIL]
    if tail and titles[-len(tail):] != [t for t in WORKBOOK_TAIL if t in tail]:
        errors.append("## 힌트, ## 풀이 는 이 순서로 본문 맨 끝에 둠")
    content = {t: c for t, c in reversed(sections)}     # 같은 제목이 여럿이면 첫 절
    for name in WORKBOOK_SECTIONS:
        if name in content and not content[name].strip():
            errors.append(f"## {name} 절이 비어 있음")
    if content.get("원문", "").strip():
        errors += check_original(content["원문"])
    for name in WORKBOOK_TAIL:
        if not content.get(name, "").strip():
            continue
        subs = split_subsections(content[name])
        if subs[0][0] == "":
            errors.append(f"## {name}: 첫 ### 소절 앞에 글이 있음")
        for label, text in subs:
            if label and not text.strip():
                errors.append(f"## {name} / ### {label}: 내용 없음")
            if name == "힌트" and label:
                errors += check_hint(label, text)
        if name == "힌트":
            count = sum(1 for label, _ in subs if label)
            if count > HINT_MAX:
                errors.append(f"## 힌트: 힌트는 {HINT_MAX}개까지 (지금 {count}개)")
        if name == "풀이":
            labels = [label for label, _ in subs if label]
            if not labels or labels[-1] != "답" or labels.count("답") > 1:
                errors.append("## 풀이: 마지막 소절 하나만 ### 답 이어야 함")
    return errors


def check_body(body, path, kind):
    """본문 절, 넷리스트, bullet, 이미지 링크를 검사한다. 기출 검사기(from_the_past/md/_tools)도 이 함수를 쓴다."""
    errors = []
    headings = [l.strip() for l in body.splitlines() if l.startswith("## ")]
    for h in ("## 조건", "## 구할 것"):
        if h not in headings:
            errors.append(f"절 누락: {h}")
    for name, text in split_sections(body):
        if name in ("조건", "구할 것") and "상속·참조" in text:
            errors.append(f"## {name}: '상속·참조'를 가리키지 않음 (문제지에 나오지 않음) — 필요한 내용을 조건에 적음")
    circuit_headings = [h for h in headings if h.startswith("## 회로")]
    if not circuit_headings:
        errors.append("절 누락: ## 회로 …")
    for h in circuit_headings:
        if h.startswith(NO_CIRCUIT_PREFIX) and not NO_CIRCUIT_RE.match(h):
            errors.append(f"{h!r}: 그림 없음 제목은 이유를 괄호로 적음 (예: '## 회로 — 없음 (설계 문제)')")
    no_circuit = bool(circuit_headings) and all(h.startswith(NO_CIRCUIT_PREFIX) for h in circuit_headings)
    for sec in re.finditer(r"^## 회로 — 없음.*?(?=^## |\Z)", body, re.DOTALL | re.MULTILINE):
        if "```spice" in sec.group(0):
            errors.append("'## 회로 — 없음' 절 아래에 ```spice 블록이 있음 (넷리스트는 적지 않음)")
    if kind == "예제" and "## 답 (검증용)" not in headings:
        errors.append("예제에 절 누락: ## 답 (검증용)")

    blocks = list(SPICE_BLOCK_RE.finditer(body))
    if not blocks and not no_circuit:
        errors.append("```spice 블록 없음")
    for b in blocks:
        lines = b.group(1).splitlines()
        for line in lines:
            err = check_netlist_line(line)
            if err:
                errors.append(err)
        after = body[b.end():]
        stop = re.search(r"\n(## |### |```)", after)
        tail = [l.strip() for l in (after[:stop.start()] if stop else after).splitlines()]
        for bullet in REQUIRED_BULLETS:
            if not any(l.startswith(bullet) for l in tail):
                first = lines[0].strip() if lines else ""
                errors.append(f"넷리스트 블록({first!r}…) 뒤에 '{bullet}' bullet 없음")

    for link in IMAGE_RE.findall(body):
        if not (path.parent / link).exists():
            errors.append(f"이미지 없음: {link}")
    errors += check_workbook_sections(body)
    return errors


def check_file(path, ch_dir):
    errors, warnings = [], []
    try:
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError) as e:
        return [str(e)], warnings

    missing = [k for k in REQUIRED_KEYS if k not in meta]
    if missing:
        return [f"frontmatter 키 누락: {', '.join(missing)}"], warnings

    m = ID_RE.match(str(meta["id"]))
    if not m:
        return [f"id 형식 오류: {meta['id']!r} (예: E9.01)"], warnings
    kind = KIND_BY_PREFIX[m.group(1)]
    expected_number = f"{int(m.group(2))}.{int(m.group(3))}"
    if not isinstance(meta["number"], str):
        errors.append(f'number {meta["number"]!r} 는 따옴표로 감싼 문자열이어야 함 (예: "{expected_number}")')
    elif meta["number"] != expected_number:
        errors.append(f"number {meta['number']!r} 가 id {meta['id']} 와 안 맞음 (기대: \"{expected_number}\")")
    if meta["kind"] != kind:
        errors.append(f"kind {meta['kind']!r} 가 id 접두어와 안 맞음 (기대: {kind})")
    if path.stem != meta["id"]:
        errors.append(f"파일명 {path.name} 이 id {meta['id']} 와 다름")
    if path.parent.name != kind:
        errors.append(f"폴더 {path.parent.name} 이 kind {kind} 와 다름")
    if kind == "장말문제":
        if meta.get("difficulty") not in (0, 1, 2):
            errors.append("장말문제 difficulty 는 0, 1, 2 중 하나")
        if not isinstance(meta.get("sol"), bool):
            errors.append("장말문제 sol 은 true/false")

    errors += check_body(body, path, kind)

    figures = meta["figures"] or []
    if not isinstance(figures, list):
        errors.append(f"figures 는 목록이어야 함: {figures!r}")
        figures = []
    for fig in figures:
        if not isinstance(fig, dict):
            errors.append(f"figures 항목은 {{id: ..., role: ...}} 형태여야 함: {fig!r}")
            continue
        fig_id = fig.get("id", "")
        if not isinstance(fig_id, str):
            errors.append(f'그림 id {fig_id!r} 는 따옴표로 감싼 문자열이어야 함 (예: "9.30")')
            continue
        if "." not in fig_id:
            errors.append(f"그림 id 형식 오류: {fig_id!r}")
            continue
        if fig.get("role") not in FIGURE_ROLES:
            errors.append(f"그림 {fig_id} role 은 problem/answer")
        crop = fig.get("crop")
        if crop is not None and fig.get("role") == "answer":
            errors.append(f"그림 {fig_id} role answer 항목에는 crop을 달지 않음")
        if crop is not None and not (isinstance(crop, str) and CROP_NAME_RE.fullmatch(crop)):
            errors.append(f"그림 {fig_id} crop {crop!r} 형식 오류 (소문자·숫자만, 예: a)")
            continue
        if not (ch_dir / "figures" / figure_filename(fig_id, crop)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id, crop)}")

    for dep in meta["depends_on"] or []:
        dm = ID_RE.match(str(dep))
        if not dm:
            errors.append(f"depends_on id 형식 오류: {dep!r}")
        elif not (ch_dir / KIND_BY_PREFIX[dm.group(1)] / f"{dep}.md").exists():
            warnings.append(f"depends_on {dep} 파일이 아직 없음")
    return errors, warnings


def md_files(ch_dir):
    return sorted(p for kind in KIND_BY_PREFIX.values() for p in (ch_dir / kind).glob("*.md"))


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 check_md.py <장 폴더>", file=sys.stderr)
        return 2
    ch_dir = Path(argv[1])
    if not ch_dir.is_dir():
        print(f"장 폴더가 없음: {ch_dir}", file=sys.stderr)
        return 2
    files = md_files(ch_dir)
    n_err = 0
    for path in files:
        try:
            errors, warnings = check_file(path, ch_dir)
        except Exception as e:  # 파일 하나가 깨져도 나머지는 계속 검사
            errors, warnings = [f"검사 중 예외 {e!r}"], []
        for e in errors:
            print(f"ERROR {path}: {e}")
        for w in warnings:
            print(f"WARN  {path}: {w}")
        n_err += len(errors)
    print(f"{len(files)}개 파일, 오류 {n_err}개")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
