"""기출 도구 테스트 공용 픽스처."""
from pathlib import Path

import fitz


def make_pdf(path: Path, pages: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=200, height=100)
    doc.save(str(path))


VALID_Q1 = """---
id: 2021-1_중간-Q1
kind: 기출
exam: "2021-1 중간고사"
number: "1"
points: 20
source: ../../src/a.pdf
pdf_page: 1
source_lang: ko
figures: []
textbook_chapters: [9]
depends_on: []
refs: []
---
# 기출 2021-1 중간 1 — 서술형

## 조건
- 주어진 값 없음

## 구할 것
- (1) 개념 설명

## 회로 — 없음 (서술형)
"""

VALID_Q2 = """---
id: 2021-1_중간-Q2
kind: 기출
exam: "2021-1 중간고사"
number: "2"
points: 20
source: ../../src/a.pdf
pdf_page: 1
source_lang: ko
figures:
  - {id: "Q2", role: problem, panels: [a]}
textbook_chapters: [9, 10]
depends_on: []
refs: []
---
# 기출 2021-1 중간 2 — 캐스코드 출력 저항

## 조건
- $I_D = 1$ mA

## 구할 것
- (1) 출력 저항

## 회로 — 그림 (a)
```spice
M1  out  Vin  0  nmos
```
- 단자: Vin = 입력 (개방 원)
- 표시: 노드 라벨 Vin
- 배치: M1 하나

![Q2](figures/fig-Q2.png)
"""


def make_exam(root: Path, files: dict, with_png: bool = True) -> Path:
    make_pdf(root / "src" / "a.pdf")
    exam = root / "md" / "2021-1_중간"
    (exam / "figures").mkdir(parents=True)
    if with_png:
        (exam / "figures" / "fig-Q2.png").write_bytes(b"\x89PNG")
    for name, text in files.items():
        (exam / name).write_text(text, encoding="utf-8")
    return exam
