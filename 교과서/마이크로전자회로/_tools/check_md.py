#!/usr/bin/env python3
"""교과서 문제 md 형식 검사기. 규칙은 ../FORMAT.md.

사용법: python3 check_md.py <장 폴더>    예) python3 check_md.py ../ch09
오류가 하나라도 있으면 종료 코드 1.
"""
import re
import sys
from pathlib import Path

import yaml

from crop_figures import figure_filename

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
    re.compile(rf'^X\w*(\s+{NODE})+\s+box\s+"[^"]+"$'),
]
SPICE_BLOCK_RE = re.compile(r"```spice\n(.*?)\n```", re.DOTALL)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
REQUIRED_BULLETS = ["- 단자:", "- 표시:", "- 배치:"]
NO_CIRCUIT_PREFIX = "## 회로 — 없음"
NO_CIRCUIT_RE = re.compile(r"^## 회로 — 없음 \(.+\)$")


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


def check_body(body, path, kind):
    """본문 절, 넷리스트, bullet, 이미지 링크를 검사한다. 기출 검사기(from_the_past/md/_tools)도 이 함수를 쓴다."""
    errors = []
    headings = [l.strip() for l in body.splitlines() if l.startswith("## ")]
    for h in ("## 조건", "## 구할 것"):
        if h not in headings:
            errors.append(f"절 누락: {h}")
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
        if not (ch_dir / "figures" / figure_filename(fig_id)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id)}")

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
