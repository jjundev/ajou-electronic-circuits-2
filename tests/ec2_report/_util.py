import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# 테스트는 실제 .claude/과목정보.md 대신 이 가짜 값을 쓴다 — 실제 파일을 고쳐도 테스트가 깨지지 않게.
FAKE = {
    "department": "테스트학과",
    "course": "전자회로2",
    "course_code": "ECE305",
    "professor": "테스트 교수님",
    "class_section": "Z999",
    "semester": "2026-2",
    "student_id": "20990001",
    "student_name": "홍길동",
    "date_format": "%Y.%m.%d",
    "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"],
    "notion_parent_page_id": None,
}


def make_root(d, drop=(), **override) -> Path:
    """tmp 디렉토리 d 에 가짜 과목정보와 설계과제/과제1/report 를 만든다."""
    root = Path(d)
    info = {k: v for k, v in {**FAKE, **override}.items() if k not in drop}
    (root / ".claude").mkdir(exist_ok=True)
    text = "---\n" + yaml.safe_dump(info, allow_unicode=True, sort_keys=False) + "---\n"
    (root / ".claude" / "과목정보.md").write_text(text, encoding="utf-8")
    (root / "설계과제" / "과제1" / "report").mkdir(parents=True, exist_ok=True)
    return root
