"""문제 md의 하위 문법 → HTML (문제집 템플릿의 html 필드용).

다루는 문법 (FORMAT.md의 조건·구할 것·원문·힌트·풀이 본문에서 쓰는 것만):
- `- ` 목록. 2칸 들여쓰기마다 한 단계 깊어진다
- 목록 항목 아래 들여쓴 목록 아닌 줄(`  $$…$$`, `  설명`)은 그 항목에 공백으로 이어 붙인다
- 들여쓰지 않은 일반 줄은 문단(<p>)이고, 빈 줄이 블록을 나눈다
- `**굵게**` → <b> (수식 밖만)
수식($…$, $$…$$)은 그대로 둔다(템플릿의 KaTeX auto-render가 그림). & < > 는 수식 안팎 모두
이스케이프한다. KaTeX는 텍스트 노드를 읽으므로 수식 안의 &lt; 도 < 로 읽힌다.
"""
import html
import re

MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITEM_RE = re.compile(r"^( *)- (.*)$")


def _plain(text):
    return BOLD_RE.sub(r"<b>\1</b>", html.escape(text, quote=False))


def inline(text):
    """한 줄 글 → HTML 조각."""
    out, last = [], 0
    for m in MATH_RE.finditer(text):
        out.append(_plain(text[last:m.start()]))
        out.append(html.escape(m.group(0), quote=False))
        last = m.end()
    out.append(_plain(text[last:]))
    return "".join(out)


def _render_list(items):
    out, depth = [], -1
    for level, text in items:
        level = min(level, depth + 1)          # 들여쓰기를 두 단계 이상 건너뛰어도 한 단계만 깊어진다
        if level > depth:
            out.append("<ul>")
        else:
            out.append("</li>" + "</ul></li>" * (depth - level))
        out.append("<li>" + inline(text))
        depth = level
    out.append("</li>" + "</ul></li>" * depth + "</ul>")
    return "".join(out)


def to_html(md):
    """md 조각 → HTML. 빈 입력이면 빈 문자열."""
    blocks = []                                # ["ul", [[level, text], …]] | ["p", [줄, …]] | None(빈 줄)
    for raw in md.splitlines():
        line = raw.rstrip()
        cur = blocks[-1] if blocks else None
        if not line.strip():
            blocks.append(None)
            continue
        m = ITEM_RE.match(line)
        if m:
            if not (cur and cur[0] == "ul"):
                cur = ["ul", []]
                blocks.append(cur)
            cur[1].append([len(m.group(1)) // 2, m.group(2)])
        elif line.startswith(" ") and cur and cur[0] == "ul":
            cur[1][-1][1] += " " + line.strip()
        else:
            if not (cur and cur[0] == "p"):
                cur = ["p", []]
                blocks.append(cur)
            cur[1].append(line.strip())
    return "".join(_render_list(b[1]) if b[0] == "ul" else f"<p>{inline(' '.join(b[1]))}</p>"
                   for b in blocks if b)


def answer_html(md):
    """답 칸용. 비어 있지 않은 줄이 하나면(목록 한 개 포함) 태그 없이 글만, 여러 줄이면 to_html."""
    lines = [line for line in md.strip().splitlines() if line.strip()]
    if len(lines) == 1:
        return inline(re.sub(r"^- ", "", lines[0].strip()))
    return to_html(md)
