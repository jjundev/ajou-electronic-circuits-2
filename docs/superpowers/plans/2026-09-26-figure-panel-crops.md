# 교과서 그림 패널 크롭과 bbox 보정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 교과서 9–11장의 `role: problem` 그림에는 그 문제가 쓰는 패널만 보이게 한다. 잘린 크롭 12장과 참조 문구도 고치고, 문제집 PDF를 다시 만든다.

**Architecture:** `figures.yaml` 그림 항목에 이름 붙은 `crops`를 두고, frontmatter 그림 항목의 `crop:`으로 크롭 PNG(`fig<장>-<NN>-<이름>.png`)를 고른다.
- 도구 4개(자르기, md 검사, 장 검사, 문제집 생성)를 한 브랜치에서 TDD로 고치고, 사용자 확인 후 main에 병합한다.
- 그 뒤 장별 worktree 3개에서 데이터 적용과 opus 리뷰를 병렬로 돌린다.
- 모든 장이 병합되면 마지막으로 "풀이 패널 노출" 검사를 도구에 추가한다. 이 검사를 처음부터 넣으면 데이터 적용 전의 main에서 오류가 나기 때문이다.

**Tech Stack:** Python 3.14 (Homebrew), PyYAML, PyMuPDF(`fitz`), 표준 `unittest`(pytest 없음), `workbook/build_workbook.py`(Playwright와 설치된 Chrome), Agent 도구(subagent, model `opus`).

**Spec:** `docs/superpowers/specs/2026-09-26-figure-panel-crops-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2`. 메인 checkout이고 브랜치는 `main`, 시작 시점은 `402bc38`이다.
- `BOOK` = `교과서/마이크로전자회로` (저장소 루트 기준 상대 경로).
- **도구 브랜치:** Task 1–4는 `MAIN/.claude/worktrees/crops-tools`(브랜치 `claude/crops-tools`)에서 한다.
- **장별 worktree:** Task 5–7은 장마다 `MAIN/.claude/worktrees/crops-ch{09,10,11}`(브랜치 `claude/crops-ch{09,10,11}`)에서 한다. 모두 도구가 병합된 뒤의 `main`에서 만든다.
- **Task 8:** `MAIN/.claude/worktrees/crops-guard`(브랜치 `claude/crops-guard`)에서 한다.
- `.claude/worktrees/hints-ch09`와 `.claude/worktrees/past-exam-tool-minor-fixes-04332f`는 다른 세션의 것이다. 건드리지 않는다.
- 원본 PDF `BOOK/{9,10,11}장.pdf`는 git이 추적한다. worktree에 이미 있으므로 심볼릭 링크가 필요 없다.
- `SCRATCH` = 실행하는 세션의 scratchpad 경로다. 셸 상태가 유지되지 않으므로 셸 명령마다 `export SCRATCH=<경로>`와 `WT=<worktree>`를 앞에 붙인다.
- **크롭 이름:** 정규식 `^[a-z0-9]+$`.
  - 패널 하나는 그 글자(`a`), 여러 패널은 글자를 이어 쓴다(`abc`).
  - 등가회로가 붙은 패널은 대표 패널 이름(`a`), 패널 글자가 없는 분할은 뜻 이름(`ce`, `cs`)으로 쓴다.
- **크롭 파일명:** `fig<장>-<NN>-<이름>.png` (예: `fig10-16-a.png`). 전체 PNG `fig<장>-<NN>.png`는 계속 만든다.
- **frontmatter:** `- {id: "10.16", role: problem, panels: [a], crop: a}`. `panels`의 의미는 바꾸지 않는다. `role: answer` 항목에는 `crop`을 달지 않는다.
- **bbox:** PDF pt 단위이고 원점은 왼쪽 위다. 감사에서 나온 값은 **시작값**일 뿐이다. 절차 M으로 렌더링해서 다시 확정한다.
- **git add:** 항상 경로를 명시한다. `git add -A`, `git add .`는 쓰지 않는다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push는 하지 않는다.** main 병합과 worktree 삭제는 그때마다 사용자에게 묻는다. 멈추는 지점은 Task 4 끝, Task 5·6·7 끝, Task 8 끝이다.
- **테스트 명령과 기대 개수**
  - 교과서 도구: `python3 -m unittest discover -s BOOK/_tools/tests`. 지금 100개 → Task 1 뒤 106 → Task 2 뒤 109 → Task 3 뒤 115 → Task 8 뒤 118.
  - 생성기: `python3 -m unittest discover -s workbook/tests`. 지금 80개 → Task 4 뒤 83.
  - 기출 도구: `python3 -m unittest discover -s from_the_past/md/_tools/tests`. 변하지 않는다.
- **서브에이전트:** `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. worktree 하나에 작성자는 한 번에 한 명뿐이다.

## Review Focus

1. **문제 이미지에 풀이 패널이 남음:** 예제의 problem 항목이나 연습문제가 crop 없이 전체 PNG를 쓰는데, 같은 그림의 answer 패널이 그 안에 있으면 안 된다. 사용자가 이 작업을 요청한 이유다. → Task 8 `test_answer_panel_leak_is_error`, `test_leak_ok_with_crop`, `test_answer_panels_within_problem_panels_ok`
2. **frontmatter는 crop인데 링크는 전체 PNG:** md에서는 옛 그림이 보이는데 문제집에서는 크롭이 보여 서로 어긋난다. → Task 3 `test_link_must_point_to_crop`
3. **크롭 이름을 바꾼 뒤 옛 PNG가 남음:** `fig10-16-a.png`에서 `-abc`로 바꾸면 옛 파일이 남는다. → Task 3 `test_stray_crop_png`와 `test_unused_crop`
4. **잘못된 yaml 입력:** 대문자 이름, 숫자 키(`1:` → int), 3원소 bbox, 페이지 밖 bbox, 리스트로 적은 `crops`가 traceback 없이 오류로 보고돼야 한다. → Task 1 `test_rejects_bad_crop_name`, `test_rejects_crop_bbox_wrong_length`, `test_rejects_crop_bbox_outside_page`, `test_rejects_crops_not_mapping`
5. **같은 그림의 다른 크롭 두 개:** 한 문제가 크롭 `a`와 전체를 같이 쓰면 문제집에 두 장 다 나와야 하고, 같은 `(id, crop)`은 한 장이어야 한다. → Task 4 `test_distinct_crops_kept_same_deduped`

---

## 절차 M — bbox 측정 (Task 5–7)

`$SCRATCH/cropcheck.py`를 한 번 만든다. 이미 있으면 그대로 쓴다.

```python
#!/usr/bin/env python3
"""bbox 후보 확인: <out>-crop.png(288 dpi 크롭)와 <out>-ctx.png(주변 40pt + 빨간 테두리)를 만든다.

사용법: python3 cropcheck.py <pdf> <pdf_page> <x0> <y0> <x1> <y1> <out 접두어>
"""
import sys

import fitz

pdf, page_no = sys.argv[1], int(sys.argv[2])
x0, y0, x1, y1 = map(float, sys.argv[3:7])
out = sys.argv[7]
doc = fitz.open(pdf)
page = doc[page_no - 1]
rect = fitz.Rect(x0, y0, x1, y1)
page.get_pixmap(dpi=288, clip=rect).save(out + "-crop.png")
ctx = fitz.Rect(rect.x0 - 40, rect.y0 - 40, rect.x1 + 40, rect.y1 + 40) & page.rect
page.draw_rect(rect, color=(1, 0, 0), width=0.5)   # 메모리에서만 그림, 저장하지 않음
page.get_pixmap(dpi=144, clip=ctx).save(out + "-ctx.png")
print(out + "-crop.png", out + "-ctx.png")
```

1. 시작값으로 `python3 $SCRATCH/cropcheck.py $WT/BOOK/<N>장.pdf <page> x0 y0 x1 y1 $SCRATCH/m/<그림>-<이름>`을 실행한다.
2. 두 PNG를 Read로 연다. 다음 네 가지를 모두 만족할 때까지 값을 1–5pt씩 조정한다.
   - 쓰는 패널의 회로, 라벨, 패널 글자 `(a)`가 온전하다.
   - 다른 패널의 선이나 글자가 한 픽셀도 들어오지 않는다.
   - 캡션 "Figure N.NN" / "그림 N.NN"이 들어오지 않는다. 단, 원래 전체 PNG에 캡션이 포함된 9장 장말문제 그림은 예외다.
   - 본문 글자가 들어오지 않는다.
3. 한 직사각형으로 이 조건을 만족할 수 없으면 크롭하지 않는다. 그 파일은 전체 PNG와 `> 참고:` 줄을 유지하고, 보고서의 "크롭 불가" 목록에 적는다.

## 절차 E — md 한 개에 크롭 적용 (Task 5–7)

대상 md에서 할 일은 네 가지다.

1. **frontmatter:** 해당 problem 항목의 `}` 앞에 `, crop: <이름>`을 넣는다. 예: `- {id: "9.13", role: problem, panels: [a]}` → `- {id: "9.13", role: problem, panels: [a], crop: a}`. answer 항목은 건드리지 않는다.
2. **이미지 링크:** 그 problem 그림의 링크 `](../figures/fig9-13.png)`를 `](../figures/fig9-13-a.png)`로 바꾼다.
   - 링크 앞 alt 글자는 `Fig 9.13(a)`처럼 패널을 적는다.
   - 예제에서 `## 답 (검증용)` 안에 있는 answer 그림 링크는 전체 PNG 그대로 둔다. 이렇게 하면 예제 한 파일에 전체 링크와 크롭 링크가 둘 다 있게 된다.
3. **참고 줄 정리:** 문제 그림 링크 바로 아래의 `> 참고:` 줄 가운데 **쓰지 않는 패널을 설명하는 부분만** 지운다(예: "이미지 오른쪽 (b)는 본문 등가회로", "(b)는 예제 9.7 풀이 그림"). 그림 위치 같은 다른 내용이 같은 줄에 있으면 그 부분은 남긴다. 줄이 비면 줄을 지운다.
4. **다른 곳은 고치지 않는다:** 넷리스트, bullet, 원문, 조건은 그대로 둔다.

## 절차 V — 장 검증 (Task 5–7 끝)

```bash
WT=<worktree>; cd "$WT/교과서/마이크로전자회로"
python3 _tools/crop_figures.py chNN > /dev/null
python3 _tools/check_md.py chNN | tail -1                  # "…개 파일, 오류 0개"
T="$(sed -n '1s/^# \(.*\) — 문제 인덱스$/\1/p' chNN/README.md)"; python3 _tools/make_index.py chNN "$T"
python3 _tools/verify_chapter.py chNN --recrop | tail -1   # "오류 0개"
cd "$WT" && python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK
git -C "$WT" status --short    # 새 PNG와 수정된 md·yaml만 보여야 함. 지운 PNG가 있으면 이유 확인
```

---

### Task 1: `crop_figures.py` — 이름 붙은 크롭

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/crop_figures.py` (전체 51줄)
- Test: `교과서/마이크로전자회로/_tools/tests/test_crop_figures.py`

**Interfaces:**
- Produces:
  - `CROP_NAME_RE = re.compile(r"^[a-z0-9]+$")`
  - `figure_filename(fig_id: str, crop: str | None = None) -> str`
  - `crop_all(ch_dir: Path) -> list[Path]`. 그림마다 전체 PNG 다음에 yaml `crops` 순서대로 크롭 PNG가 온다.
  - 잘못된 입력에는 `ValueError`(한국어 메시지)를 낸다.

- [ ] **Step 0: worktree 만들기**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git -C "$MAIN" status --short | grep -v '^??'     # 비어 있어야 함
git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/crops-tools" -b claude/crops-tools main
```

- [ ] **Step 1: 실패하는 테스트 쓰기.** `test_crop_figures.py`에 추가한다. `FigureFilenameTest`에 메서드 하나를 넣고, 파일 끝의 `if __name__` 앞에 새 클래스를 둔다.

```python
    def test_crop_suffix(self):
        self.assertEqual(figure_filename("10.16", "a"), "fig10-16-a.png")
        self.assertEqual(figure_filename("9.2", "abc"), "fig9-02-abc.png")
```

```python
class CropsTest(unittest.TestCase):
    def crop(self, fig_line):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), "pdf: ../../book.pdf\ndpi: 144\nfigures:\n" + fig_line + "\n")
            outs = crop_all(ch)
            return [(o.name, fitz.Pixmap(str(o)).width, fitz.Pixmap(str(o)).height) for o in outs]

    def test_crops_written_after_whole(self):
        got = self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], '
                        'crops: {a: [0, 0, 36, 36], bc: [36, 0, 72, 18]}}')
        self.assertEqual(got, [("fig9-30.png", 144, 72), ("fig9-30-a.png", 72, 72),
                               ("fig9-30-bc.png", 72, 36)])

    def test_rejects_bad_crop_name(self):
        for name in ("A", "a_b", "1"):          # "1"은 YAML에서 int가 된다
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "크롭 이름"):
                self.crop(f'  "9.30": {{pdf_page: 1, bbox: [0, 0, 72, 36], crops: {{{name}: [0, 0, 10, 10]}}}}')

    def test_rejects_crop_bbox_wrong_length(self):
        with self.assertRaisesRegex(ValueError, "bbox"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: {a: [0, 0, 10]}}')

    def test_rejects_crop_bbox_outside_page(self):
        with self.assertRaisesRegex(ValueError, "범위 밖"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: {a: [0, 0, 300, 50]}}')

    def test_rejects_crops_not_mapping(self):
        with self.assertRaisesRegex(ValueError, "crops"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: [0, 0, 10, 10]}')
```

- [ ] **Step 2: 실패 확인**

Run: `cd $MAIN/.claude/worktrees/crops-tools && python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3`
Expected: FAIL 6개. `figure_filename()`에 인자가 너무 많다는 오류, 그리고 ValueError가 발생하지 않거나 크롭이 없다는 실패가 나온다.

- [ ] **Step 3: 구현.** `crop_figures.py`의 import와 두 함수를 아래처럼 바꾼다(`main`은 그대로 둔다).

```python
import re
import sys
from pathlib import Path

import fitz
import yaml

CROP_NAME_RE = re.compile(r"^[a-z0-9]+$")


def figure_filename(fig_id: str, crop: str | None = None) -> str:
    chapter, number = fig_id.split(".")
    suffix = f"-{crop}" if crop else ""
    return f"fig{chapter}-{int(number):02d}{suffix}.png"


def _clip(page, bbox, where):
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError(f"{where}: bbox {bbox!r} 는 [x0, y0, x1, y1] 네 값이어야 함")
    rect = fitz.Rect(*bbox)
    if not page.rect.contains(rect):
        raise ValueError(f"{where}: bbox {bbox} 가 쪽 범위 {tuple(page.rect)} 밖")
    return rect


def crop_all(ch_dir: Path) -> list[Path]:
    fig_dir = ch_dir / "figures"
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8"))
    pdf_path = (fig_dir / spec["pdf"]).resolve()
    dpi = spec.get("dpi", 144)
    written = []
    with fitz.open(pdf_path) as doc:
        for fig_id, fig in spec["figures"].items():
            if not isinstance(fig_id, str):
                raise ValueError(f"그림 id {fig_id!r} 는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
            pdf_page = fig["pdf_page"]
            if not isinstance(pdf_page, int) or not 1 <= pdf_page <= len(doc):
                raise ValueError(f"{fig_id}: pdf_page {pdf_page!r} 가 1..{len(doc)} 범위 밖")
            page = doc[pdf_page - 1]
            crops = fig.get("crops") or {}
            if not isinstance(crops, dict):
                raise ValueError(f"{fig_id}: crops 는 매핑(이름: bbox)이어야 함, 받은 값 {crops!r}")
            jobs = [(None, fig["bbox"])] + list(crops.items())
            for name, bbox in jobs:
                if name is not None and not (isinstance(name, str) and CROP_NAME_RE.match(name)):
                    raise ValueError(f"{fig_id}: 크롭 이름 {name!r} 형식 오류 (소문자·숫자만, 예: a, abc, ce)")
                where = fig_id if name is None else f"{fig_id} 크롭 {name}"
                rect = _clip(page, bbox, where)
                out = fig_dir / figure_filename(fig_id, name)
                page.get_pixmap(dpi=dpi, clip=rect).save(out)
                written.append(out)
    return written
```

기존 테스트 `test_rejects_bbox_outside_page`는 메시지 "범위 밖"이 그대로라 계속 통과한다. 모듈 docstring 끝에 한 줄을 추가한다.

```
그림 항목에 crops: {이름: bbox}가 있으면 같은 쪽에서 잘라 fig<장>-<NN>-<이름>.png로도 저장한다.
```

- [ ] **Step 4: 통과 확인**

Run: 같은 명령
Expected: `Ran 106 tests` … `OK`

- [ ] **Step 5: 커밋**

```bash
cd $MAIN/.claude/worktrees/crops-tools
git add 교과서/마이크로전자회로/_tools/crop_figures.py 교과서/마이크로전자회로/_tools/tests/test_crop_figures.py
git commit -m "feat(figures): named per-panel crops in figures.yaml

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: `check_md.py` — frontmatter `crop` 검사

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py:13` (import), `:221-235` (figures 루프)
- Test: `교과서/마이크로전자회로/_tools/tests/test_check_md.py`

**Interfaces:**
- Consumes: `CROP_NAME_RE`, `figure_filename(fig_id, crop)` (Task 1)
- Produces: `check_file`의 오류 문구 두 가지
  - `그림 <id> crop <값> 형식 오류 (소문자·숫자만, 예: a)`
  - `그림 파일 없음: figures/<크롭 파일명>`

- [ ] **Step 1: 실패하는 테스트.** `CheckFileTest` 클래스 끝(`test_unquoted_figure_id_is_error` 뒤)에 추가한다. 모듈 수준 상수 `CROP_MD`는 `make_chapter` 정의 바로 뒤에 둔다.

```python
CROP_MD = (VALID_MD.replace("panels: [a]}", "panels: [a], crop: a}")
           .replace("fig9-02.png)", "fig9-02-a.png)"))
```

```python
    def run_crop_check(self, text, crop_png=True):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": text})
            if crop_png:
                (ch / "figures" / "fig9-02-a.png").write_bytes(b"\x89PNG")
            return check_file(ch / "예제/E9.01.md", ch)

    def test_crop_file_ok(self):
        self.assertEqual(self.run_crop_check(CROP_MD), ([], []))

    def test_bad_crop_value_is_error(self):
        errors, _ = self.run_crop_check(CROP_MD.replace("crop: a}", "crop: A}"))
        self.assertTrue(any("crop" in e and "형식 오류" in e for e in errors), errors)

    def test_missing_crop_png_is_error(self):
        errors, _ = self.run_crop_check(CROP_MD, crop_png=False)
        self.assertTrue(any("그림 파일 없음" in e and "fig9-02-a.png" in e for e in errors), errors)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3`
Expected: FAIL 2개(`test_bad_crop_value_is_error`, `test_missing_crop_png_is_error`). `test_crop_file_ok`는 이미 통과할 수도 있다. 지금 코드는 crop을 무시하고 전체 PNG만 보기 때문이다.

- [ ] **Step 3: 구현.** import를 `from crop_figures import CROP_NAME_RE, figure_filename`로 바꾼다. figures 루프의 마지막 두 줄(파일 존재 검사)을 아래로 바꾼다.

```python
        crop = fig.get("crop")
        if crop is not None and not (isinstance(crop, str) and CROP_NAME_RE.match(crop)):
            errors.append(f"그림 {fig_id} crop {crop!r} 형식 오류 (소문자·숫자만, 예: a)")
            continue
        if not (ch_dir / "figures" / figure_filename(fig_id, crop)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id, crop)}")
```

- [ ] **Step 4: 통과 확인** — Expected: `Ran 109 tests` `OK`

- [ ] **Step 5: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py
git commit -m "feat(check_md): validate figure crop and its png

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 3: `verify_chapter.py` — 크롭 링크·사용·PNG 집합 검사, FORMAT.md 규칙

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/verify_chapter.py:58-111` (`check_figures`)
- Modify: `교과서/마이크로전자회로/FORMAT.md` (18–20행 폴더 트리, 35–41행 frontmatter, 57–59행 회로 절)
- Test: `교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py`

**Interfaces:**
- Consumes: `figure_filename(fig_id, crop)` (Task 1). `check_recrop`은 코드를 바꾸지 않는다. `crop_all`이 크롭 경로도 돌려주므로 크롭까지 자동으로 비교된다.
- Produces: 새 오류 문구 세 가지
  - `<id>: 그림 <fid> 크롭 <이름>이 figures.yaml에 없음`
  - `figures.yaml에만 있고 md가 쓰지 않는 크롭: <fid> <이름>, …`
  - 기존 문구 `<id>: 그림 <fid> 이미지 링크 없음`에 ` (<기대 파일명>)`이 붙는다

- [ ] **Step 1: 실패하는 테스트.** `FigureTest` 뒤에 새 클래스를 추가한다.

```python
class CropTest(ChapterCase):
    def set_crops(self, crops="{a: [0, 0, 36, 36]}"):
        path = self.ch / "figures" / "figures.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "bbox: [0, 0, 72, 36]}", f"bbox: [0, 0, 72, 36], crops: {crops}}}"), encoding="utf-8")
        crop_all(self.ch)

    def use_crop(self, crop="a", link=None, id_="P9.02"):
        text = make_md(id_, figures=["9.2"]).replace("panels: []}", f"panels: [], crop: {crop}}}")
        text = text.replace("(../figures/fig9-02.png)", f"(../figures/{link or figure_filename('9.2', crop)})")
        write_md(self.ch, id_, text=text)

    def test_crop_chapter_passes(self):
        self.set_crops()
        self.use_crop()
        (self.ch / "README.md").write_text(build_index(self.ch, "9장 테스트"), encoding="utf-8")
        self.assertEqual(verify(self.ch, recrop=True), ([], []))

    def test_link_must_point_to_crop(self):
        self.set_crops()
        self.use_crop(link="fig9-02.png")
        self.assertError("P9.02", "9.2", "이미지 링크 없음", "fig9-02-a.png")

    def test_crop_missing_from_yaml(self):
        self.set_crops()
        self.use_crop()
        self.use_crop(crop="b", id_="P9.03")
        self.assertError("P9.03", "크롭 b", "figures.yaml에 없음")

    def test_unused_crop(self):
        self.set_crops()
        self.assertError("md가 쓰지 않는 크롭", "9.2 a")

    def test_stray_crop_png(self):
        self.set_crops()
        self.use_crop()
        shutil.copy(self.ch / "figures" / "fig9-02-a.png", self.ch / "figures" / "fig9-02-old.png")
        self.assertError("figures.yaml에 없는 PNG", "fig9-02-old.png")

    def test_tampered_crop_detected_with_recrop(self):
        self.set_crops()
        self.use_crop()
        fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 5, 5), False).save(str(self.ch / "figures" / "fig9-02-a.png"))
        self.assertError("fig9-02-a.png", "다시 자른 결과와 다름", recrop=True)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3`
Expected: FAIL. 대상은 `test_crop_chapter_passes`(링크 없음 오류와 크롭 PNG가 stray로 잡힘), `test_link_must_point_to_crop`, `test_crop_missing_from_yaml`, `test_unused_crop`이다. `test_tampered_crop_detected_with_recrop`은 Task 1 덕분에 이미 통과할 수 있다.

- [ ] **Step 3: 구현.** `check_figures`에서 `yaml_ids` 수집부터 함수 끝까지를 아래로 바꾼다(앞쪽의 yaml 읽기와 형식 검사는 그대로 둔다).

```python
    errors = []
    yaml_ids, yaml_crops = set(), {}
    for key, fig in figures.items():
        if not isinstance(key, str):
            errors.append(f"figures.yaml 그림 id {key!r}는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
        elif not FIG_ID_RE.match(key):
            errors.append(f"figures.yaml 그림 id {key!r} 형식 오류 (예: \"9.30\")")
        else:
            yaml_ids.add(key)
            crops = fig.get("crops") if isinstance(fig, dict) else None
            yaml_crops[key] = {str(n) for n in crops} if isinstance(crops, dict) else set()
    used, used_crops = set(), set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        figs = fm.get("figures") or []
        if not isinstance(figs, list):
            errors.append(f"{i}: frontmatter figures가 목록이 아님")
            figs = []
        for fig in figs:
            fid = fig.get("id") if isinstance(fig, dict) else None
            if fid is None or not FIG_ID_RE.match(str(fid)):
                errors.append(f"{i}: figures 항목 {fig!r}에 올바른 id가 없음")
                continue
            fid = str(fid)
            used.add(fid)
            crop = fig.get("crop")
            crop = None if crop is None else str(crop)
            if crop is not None:
                used_crops.add((fid, crop))
                if fid in yaml_crops and crop not in yaml_crops[fid]:
                    errors.append(f"{i}: 그림 {fid} 크롭 {crop}이 figures.yaml에 없음")
            expected_link = figure_filename(fid, crop)
            if expected_link not in names:
                errors.append(f"{i}: 그림 {fid} 이미지 링크 없음 ({expected_link})")
        for link in links:
            if not (path.parent / link).exists():
                errors.append(f"{i}: 깨진 이미지 링크 {link}")
    if yaml_ids - used:
        errors.append(f"figures.yaml에만 있고 md가 쓰지 않는 그림: {', '.join(sorted(yaml_ids - used))}")
    if used - yaml_ids:
        errors.append(f"md가 쓰지만 figures.yaml에 없는 그림: {', '.join(sorted(used - yaml_ids))}")
    unused_crops = {(f, n) for f, ns in yaml_crops.items() for n in ns} - used_crops
    if unused_crops:
        errors.append("figures.yaml에만 있고 md가 쓰지 않는 크롭: "
                      + ", ".join(f"{f} {n}" for f, n in sorted(unused_crops)))
    pngs = {p.name for p in fig_dir.glob("*.png")}
    expected = {figure_filename(i) for i in yaml_ids}
    expected |= {figure_filename(f, n) for f, ns in yaml_crops.items() for n in ns}
    if expected - pngs:
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_figures.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    return errors
```

- [ ] **Step 4: 통과 확인** — Expected: `Ran 115 tests` `OK`

- [ ] **Step 5: FORMAT.md 규칙 추가.** 다음 세 곳을 고친다.
  - 18–20행 폴더 트리의 `figures/figures.yaml, figures/fig<장>-<NN>.png` 줄을 `figures/figures.yaml, figures/fig<장>-<NN>.png, figures/fig<장>-<NN>-<크롭>.png`로 바꾼다.
  - 41행("같은 그림 id인데 패널마다 role이 다르면…") 바로 뒤에 아래 불릿을 추가한다.
    ```
    - 이미지에 이 문제가 쓰지 않는 패널(본문 패널, 풀이 패널)이 있으면 `role: problem` 항목에 `crop: <이름>`을 단다. `figures.yaml`의 그 그림 항목에 `crops: {<이름>: [x0, y0, x1, y1]}`(같은 쪽)을 두면 `crop_figures.py`가 `fig<장>-<NN>-<이름>.png`를 만든다
      - 이름은 소문자·숫자만. 패널 하나면 그 글자(`a`), 여럿이면 이어서(`abc`), 등가회로가 붙으면 대표 패널(`a`), 패널 글자가 없는 분할은 뜻 이름(`ce`, `cs`)
      - `panels`는 그대로 문제가 쓰는 패널이다. `crop`은 링크할 이미지만 고른다
      - `role: answer` 항목에는 `crop`을 달지 않는다
      - 쓰는 패널을 한 직사각형으로 깔끔하게 자를 수 없으면 크롭하지 않고 전체 PNG와 `> 참고:` 줄을 둔다
    ```
  - 58–59행 "크롭 이미지에 대한 메모" 불릿 끝에 다음 문장을 추가한다.
    ```
     `crop`이 있으면 이미지 링크는 크롭 PNG(`../figures/fig10-16-a.png`)를 가리키고, 쓰지 않는 패널을 설명하는 참고 줄은 두지 않는다
    ```

- [ ] **Step 6: 실제 장 회귀 확인.** 데이터는 바뀌지 않았으므로 오류가 0개여야 한다.

```bash
cd $MAIN/.claude/worktrees/crops-tools/교과서/마이크로전자회로
for c in ch09 ch10 ch11; do python3 _tools/verify_chapter.py $c --recrop | tail -1; python3 _tools/check_md.py $c | tail -1; done
```
Expected: 여섯 줄 모두 `오류 0개`

- [ ] **Step 7: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py 교과서/마이크로전자회로/FORMAT.md
git commit -m "feat(verify): check crop links, unused crops and crop pngs; document crop rule

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 4: 문제집 생성기가 크롭 PNG를 쓰게 하기, 그리고 도구 병합

**Files:**
- Modify: `workbook/problem.py:130-136` (`problem_figure_ids` → `problem_figures`), `:145`, `:164-181` (`figures`)
- Test: `workbook/tests/test_problem.py` (`TestFigures`)

**Interfaces:**
- Consumes: `textbook_figure_filename(fig_id, crop)` (Task 1의 `figure_filename`)
- Produces: `problem_figures(p) -> list[tuple[str, str | None]]`. 순서를 유지하고 중복을 없앤다. `figures(p)`의 반환 형식은 그대로다.

- [ ] **Step 1: 실패하는 테스트.** `TestFigures`에 추가한다.

```python
    def test_distinct_crops_kept_same_deduped(self):
        make_png(self.root / "ch09" / "figures" / "fig9-02-a.png", 100, 50)
        figs_yaml = ('  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
                     '  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
                     '  - {id: "9.2", role: problem, panels: [b]}\n')
        figs = figures(self.load(textbook_md(figures=figs_yaml)))
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figs], [(17.6, 8.8), (35.3, 32.1)])

    def test_missing_crop_file_raises(self):
        figs_yaml = '  - {id: "9.2", role: problem, panels: [a], crop: a}\n'
        with self.assertRaisesRegex(ProblemError, "fig9-02-a.png"):
            figures(self.load(textbook_md(figures=figs_yaml)))
```

`TestExam`(`test_problem.py:214`)에 추가한다. setUp이 `self.p = load_problem(exam_dir / "Q1.md")`로 읽으므로, 같은 파일을 덮어쓰고 다시 읽는다.

```python
    def test_exam_crop_rejected(self):
        path = self.p.path
        path.write_text(EXAM_MD.replace("panels: [a, b]}", "panels: [a, b], crop: a}"), encoding="utf-8")
        with self.assertRaisesRegex(ProblemError, "crop"):
            figures(load_problem(path))
```

- [ ] **Step 2: 실패 확인**

Run: `cd $MAIN/.claude/worktrees/crops-tools && python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: FAIL 3개

- [ ] **Step 3: 구현**

```python
def problem_figures(p):
    """문제 그림(role: problem)의 (id, crop) — 순서 유지, 중복 제거. crop이 없으면 None."""
    out = []
    for fig in p.meta.get("figures") or []:
        key = (str(fig.get("id")), fig.get("crop"))
        if fig.get("role") == "problem" and key not in out:
            out.append(key)
    return out
```

`html_fields`의 `if problem_figure_ids(p):`를 `if problem_figures(p):`로 바꾼다. `figures`의 루프 머리를 아래로 바꾼다.

```python
    out = []
    for fig_id, crop in problem_figures(p):
        if p.is_exam:
            if crop is not None:
                raise ProblemError(f"기출 그림 {fig_id}에는 crop을 쓸 수 없음")
            png = p.figures_dir / exam_figure_filename(fig_id)
        else:
            png = p.figures_dir / textbook_figure_filename(fig_id, crop)
        if not png.exists():
            raise ProblemError(f"그림 파일 없음: {png}")
```

`name = …` 줄은 지운다. 나머지(dpi, png_size, out.append)는 그대로 둔다. 다른 곳에서 `problem_figure_ids`를 쓰지 않는지 `grep -rn problem_figure_ids workbook`으로 확인한다. 결과가 비어 있어야 한다.

- [ ] **Step 4: 통과 확인.** Expected: `Ran 83 tests` `OK`. 교과서 도구는 115개, 기출 도구는 기존 개수 그대로 `OK`여야 한다.

- [ ] **Step 5: 커밋**

```bash
git add workbook/problem.py workbook/tests/test_problem.py
git commit -m "feat(workbook): print per-problem figure crops

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: 병합 확인 (멈춤).** 사용자에게 다음을 보여 준다.
  - `git -C $MAIN log --oneline main..claude/crops-tools`
  - 테스트 결과 세 줄
  
  그리고 "main에 fast-forward 병합하고 crops-tools worktree를 지울까요?"라고 묻는다. 승인하면 아래를 실행한다.

```bash
git -C $MAIN merge --ff-only claude/crops-tools
git -C $MAIN worktree remove $MAIN/.claude/worktrees/crops-tools && git -C $MAIN branch -d claude/crops-tools
```

---

### Task 5: ch09 데이터 적용

**Files:**
- Modify: `교과서/마이크로전자회로/ch09/figures/figures.yaml`, 부록 D9의 md 파일들, `ch09/figures/*.png`(재생성과 신규)
- Modify: `workbook/pdf/ch09-문제.pdf`, `workbook/pdf/ch09-답안.pdf`
- Create: `docs/superpowers/reports/crops/ch09.md` (리뷰 보고서)

**Interfaces:**
- Consumes: Task 1–4의 크롭 형식(`crops:`, `crop:`, `fig9-NN-<이름>.png`)
- Produces: `verify_chapter.py ch09 --recrop` 오류 0. 그리고 부록 D9의 모든 problem 항목이 crop을 가지거나 보고서의 "크롭 불가" 목록에 있다.

실행 방식: 작성자 subagent(opus, foreground)가 Step 1–6을 하고, 리뷰어 subagent(opus)가 Step 7을 한다. Task 5·6·7은 서로 다른 worktree이므로 **동시에** 띄운다.

- [ ] **Step 1: worktree 만들기**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/crops-ch09" -b claude/crops-ch09 main
```

- [ ] **Step 2: 잘린 크롭 bbox 보정 (부록 D9 표 1).** 행마다 절차 M으로 확인한 뒤 `figures.yaml`의 bbox를 고친다. 그다음 `python3 _tools/crop_figures.py ch09`를 실행하고 bbox 보정 PNG를 Read로 연다. 이것만 먼저 커밋한다.

```bash
git add 교과서/마이크로전자회로/ch09/figures/figures.yaml 교과서/마이크로전자회로/ch09/figures/fig9-*.png
git commit -m "fix(ch09): widen clipped figure bboxes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: 크롭 정의 (부록 D9 표 2).** 행마다 절차 M으로 bbox를 확정하고, 그 그림 항목에 `crops: {…}`를 추가한다. 그다음 `crop_figures.py ch09`를 실행한다.
- [ ] **Step 4: md 적용.** 표 2의 "사용 파일"마다 절차 E를 적용한다.
- [ ] **Step 5: 참조 문구 수정 (부록 D9 표 3).**
- [ ] **Step 6: 검증, PDF 재생성, 커밋.** 절차 V를 돌려 오류가 0개인지 확인한다. 이어서 아래를 실행한다.

```bash
cd $MAIN/.claude/worktrees/crops-ch09
python3 workbook/build_workbook.py ch09 2>&1 | tail -5     # OVERFLOW·ERROR 줄 없음, 종료 코드 0
git add 교과서/마이크로전자회로/ch09/figures/figures.yaml 교과서/마이크로전자회로/ch09/figures/*.png \
        교과서/마이크로전자회로/ch09/예제/*.md 교과서/마이크로전자회로/ch09/연습문제/*.md \
        교과서/마이크로전자회로/ch09/장말문제/*.md 교과서/마이크로전자회로/ch09/README.md
git commit -m "feat(ch09): per-problem figure crops and reference wording

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git add workbook/pdf/ch09-문제.pdf workbook/pdf/ch09-답안.pdf
git commit -m "build: regenerate ch09 pdfs with figure crops

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: 리뷰 (opus 리뷰어, 읽기 전용).** 리뷰어는 아래를 하고 `docs/superpowers/reports/crops/ch09.md.part`에 쓴 뒤, 끝나면 `.md`로 이름을 바꾼다.
  1. 표 2의 모든 크롭 PNG를 Read로 열고, 사용 파일 md의 `panels`, 원문, 넷리스트 절과 대조한다. 다음을 확인한다.
     - 쓰는 패널이 온전한지
     - 다른 패널이 섞이지 않았는지
     - 캡션이나 본문이 섞이지 않았는지
  2. `git diff main -- '*.md'`를 보고 절차 E를 벗어난 수정이 없는지 확인한다. 넷리스트나 원문이 바뀌었으면 안 된다.
  3. 표 1의 PNG 가장자리를 확인한다.
  4. `workbook/build/pdf`가 아닌 `workbook/pdf/ch09-문제.pdf`에서 표 2 문제 3개 이상의 쪽을 PNG로 렌더링해서 확인한다. `fitz`로 해당 쪽을 `$SCRATCH`에 렌더링한다.
  5. 보고서 형식: `파일 | 그림 | 문제 | 제안` 표 한 개. 문제가 없으면 "지적 없음".

  작성자가 보고서를 반영한다. 반영 커밋 메시지는 `fix(ch09): apply crop review`이고, 필요하면 PDF도 다시 만든다. 보고서 파일도 함께 커밋한다(`git add docs/superpowers/reports/crops/ch09.md`).
- [ ] **Step 8: 병합 확인 (멈춤).** 사용자에게 `git log --oneline main..claude/crops-ch09`, 절차 V 결과, 리뷰 요약을 보여 주고 병합 여부를 묻는다. 승인하면 `main`에 rebase한 뒤 ff 병합한다(다른 장이 먼저 병합됐을 수 있다). 이어서 worktree와 브랜치를 지운다.

```bash
git -C $MAIN/.claude/worktrees/crops-ch09 rebase main
git -C $MAIN merge --ff-only claude/crops-ch09
git -C $MAIN worktree remove $MAIN/.claude/worktrees/crops-ch09 && git -C $MAIN branch -d claude/crops-ch09
```

### Task 6: ch10 데이터 적용

Task 5와 같은 절차를 `ch10`에 적용한다. 단계를 모두 다시 적는다.

**Files:** `ch10/figures/figures.yaml`, 부록 D10의 md, `ch10/figures/*.png`, `workbook/pdf/ch10-문제.pdf`, `workbook/pdf/ch10-답안.pdf`, `docs/superpowers/reports/crops/ch10.md`

**Interfaces:**
- Consumes: Task 1–4의 형식
- Produces: `verify_chapter.py ch10 --recrop` 오류 0

- [ ] **Step 1:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/crops-ch10" -b claude/crops-ch10 main`
- [ ] **Step 2:** 부록 D10 표 1의 bbox를 절차 M으로 보정하고 `crop_figures.py ch10`을 실행한다. 커밋 `fix(ch10): widen clipped figure bboxes`에는 `ch10/figures/figures.yaml`과 `ch10/figures/fig10-*.png`를 넣는다.
- [ ] **Step 3:** 부록 D10 표 2의 `crops`를 절차 M으로 확정해 yaml에 넣고 `crop_figures.py ch10`을 실행한다.
- [ ] **Step 4:** 표 2의 사용 파일마다 절차 E를 적용한다.
- [ ] **Step 5:** 부록 D10 표 3의 문구를 고친다.
- [ ] **Step 6:** 절차 V(chNN=ch10)로 오류 0개를 확인한다. `python3 workbook/build_workbook.py ch10`을 실행한다. 커밋은 두 개다. 하나는 `feat(ch10): per-problem figure crops and reference wording`(ch10의 yaml, png, md, README), 다른 하나는 `build: regenerate ch10 pdfs with figure crops`(ch10 PDF 두 개)다.
- [ ] **Step 7:** 리뷰어(opus)가 Task 5 Step 7의 1–5를 ch10에 대해 하고 `docs/superpowers/reports/crops/ch10.md`에 쓴다. 작성자가 반영해 `fix(ch10): apply crop review`로 커밋한다.
- [ ] **Step 8:** 병합 여부를 묻는다(멈춤). 승인하면 `rebase main` → `merge --ff-only claude/crops-ch10` → worktree와 브랜치 삭제.

### Task 7: ch11 데이터 적용

Task 5와 같은 절차를 `ch11`에 적용한다. 단계를 모두 다시 적는다. ch11에는 bbox 보정이 없다.

**Files:** `ch11/figures/figures.yaml`, 부록 D11의 md, `ch11/figures/*.png`, `workbook/pdf/ch11-문제.pdf`, `workbook/pdf/ch11-답안.pdf`, `docs/superpowers/reports/crops/ch11.md`

**Interfaces:**
- Consumes: Task 1–4의 형식
- Produces: `verify_chapter.py ch11 --recrop` 오류 0

- [ ] **Step 1:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/crops-ch11" -b claude/crops-ch11 main`
- [ ] **Step 2:** 부록 D11 표 2의 `crops`를 절차 M으로 확정해 yaml에 넣고 `crop_figures.py ch11`을 실행한다. 11.31의 `ce`/`cs`는 가운데 경계에서 두 회로가 선을 공유하지 않는지 ctx 이미지로 확인한다. 공유하면 "크롭 불가"로 둔다.
- [ ] **Step 3:** 표 2의 사용 파일마다 절차 E를 적용한다.
- [ ] **Step 4:** 절차 V(chNN=ch11)로 오류 0개를 확인한다. `python3 workbook/build_workbook.py ch11`을 실행한다. 커밋은 `feat(ch11): per-problem figure crops`(ch11의 yaml, png, md, README)와 `build: regenerate ch11 pdfs with figure crops`(ch11 PDF 두 개)다.
- [ ] **Step 5:** 리뷰어(opus)가 Task 5 Step 7의 1–5를 ch11에 대해 하고 `docs/superpowers/reports/crops/ch11.md`에 쓴다. 반영 커밋은 `fix(ch11): apply crop review`다.
- [ ] **Step 6:** 병합 여부를 묻는다(멈춤). 승인하면 `rebase main` → `merge --ff-only claude/crops-ch11` → worktree와 브랜치 삭제.

### Task 8: 풀이 패널 노출 검사 (세 장이 모두 병합된 뒤)

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/verify_chapter.py` (`check_figures` 끝에 검사 추가)
- Modify: `교과서/마이크로전자회로/FORMAT.md` (Task 3에서 넣은 crop 불릿 아래)
- Test: `교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py`

**Interfaces:**
- Consumes: Task 3의 `check_figures`
- Produces: 오류 문구 `<id>: 그림 <fid> 문제 이미지에 풀이 패널 <패널들>이 보임 (crop 필요)`

- [ ] **Step 0:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/crops-guard" -b claude/crops-guard main`
- [ ] **Step 1: 실패하는 테스트.** `CropTest` 뒤에 추가한다.

```python
class AnswerLeakTest(ChapterCase):
    def write_pair(self, problem_extra="", answer_panels="[b]", problem_panels="[a]", link="fig9-02.png"):
        e = make_md("E9.01", figures=["9.2"]).replace(
            '  - {id: "9.2", role: problem, panels: []}',
            f'  - {{id: "9.2", role: problem, panels: {problem_panels}{problem_extra}}}\n'
            f'  - {{id: "9.2", role: answer, panels: {answer_panels}}}')
        e = e.replace("(../figures/fig9-02.png)", f"(../figures/{link})\n![답](../figures/fig9-02.png)")
        write_md(self.ch, "E9.01", text=e)

    def test_answer_panel_leak_is_error(self):
        self.write_pair()
        self.assertError("E9.01", "9.2", "풀이 패널 b", "crop 필요")

    def test_leak_ok_with_crop(self):
        path = self.ch / "figures" / "figures.yaml"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "bbox: [0, 0, 72, 36]}", "bbox: [0, 0, 72, 36], crops: {a: [0, 0, 36, 36]}}"), encoding="utf-8")
        crop_all(self.ch)
        self.write_pair(problem_extra=", crop: a", link="fig9-02-a.png")
        errors, _ = verify(self.ch)
        self.assertFalse(any(e.startswith("E9.01") and "풀이 패널" in e for e in errors), errors)

    def test_answer_panels_within_problem_panels_ok(self):
        self.write_pair(answer_panels="[a, b]", problem_panels="[a, b]")
        errors, _ = verify(self.ch)
        self.assertFalse(any(e.startswith("E9.01") and "풀이 패널" in e for e in errors), errors)
```

X9.01도 같은 그림 9.2를 crop 없이 `panels: []`로 쓰므로 첫 테스트에서 X9.01도 걸린다. 이것이 의도한 동작이다. 연습문제에도 정답이 보이기 때문이다. 그래서 세 테스트 모두 E9.01에 대한 오류만 본다.

- [ ] **Step 2: 실패 확인** — `test_answer_panel_leak_is_error`가 FAIL
- [ ] **Step 3: 구현.** `check_figures`에서 `return errors` 바로 앞에 추가한다.

```python
    answer_panels = {}
    for _, fm, _ in docs.values():
        for fig in fm.get("figures") or []:
            if isinstance(fig, dict) and fig.get("role") == "answer" and isinstance(fig.get("panels"), list):
                answer_panels.setdefault(str(fig.get("id")), set()).update(map(str, fig["panels"]))
    for i, (_, fm, _) in sorted(docs.items()):
        for fig in fm.get("figures") or []:
            if not isinstance(fig, dict) or fig.get("role") != "problem" or fig.get("crop") is not None:
                continue
            panels = fig.get("panels") if isinstance(fig.get("panels"), list) else []
            leak = answer_panels.get(str(fig.get("id")), set()) - set(map(str, panels))
            if leak:
                errors.append(f"{i}: 그림 {fig.get('id')} 문제 이미지에 풀이 패널 {', '.join(sorted(leak))}이 보임 (crop 필요)")
```

`docs`가 비었거나 frontmatter figures가 목록이 아니면 앞의 루프가 이미 오류를 보고한다. 여기서는 `or []`와 isinstance로 건너뛴다. 단, `fm.get("figures")`가 문자열이면 문자 단위로 돌게 되므로 `isinstance(fig, dict)`로 막는다.

- [ ] **Step 4: 통과 확인.** 테스트는 `Ran 118 tests` `OK`여야 한다. 이어서 실제 세 장을 확인한다.

```bash
cd $MAIN/.claude/worktrees/crops-guard/교과서/마이크로전자회로
for c in ch09 ch10 ch11; do python3 _tools/verify_chapter.py $c --recrop | tail -1; done
```
Expected: 모두 `오류 0개`. 오류가 나면 Task 5–7에서 빠진 파일이다. 해당 장을 절차 M·E로 이 브랜치에서 고치고, 그 장 PDF를 다시 만들어 같은 커밋에 넣는다.

- [ ] **Step 5: FORMAT.md.** Task 3에서 넣은 crop 불릿 목록 끝에 한 줄을 추가한다.

```
  - 같은 그림의 `role: answer` 패널이 이 문제 `panels`에 없는데 `crop`이 없으면 `verify_chapter.py`가 오류로 본다 (문제 이미지에 풀이가 보이면 안 됨)
```

- [ ] **Step 6: 커밋, 전체 리뷰, 병합 확인 (멈춤)**

```bash
git add 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py 교과서/마이크로전자회로/FORMAT.md
git commit -m "feat(verify): flag answer panels visible in problem figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

opus 리뷰어 한 명에게 `git diff 402bc38..claude/crops-guard` 전체를 리뷰하게 한다. 도구 코드, FORMAT, 장별 보고서 반영 여부를 본다. 그 결과를 사용자에게 보여 주고 병합 여부를 묻는다. 승인하면 `merge --ff-only claude/crops-guard`를 하고 worktree와 브랜치를 지운다.

---

## 부록 D9 — ch09 데이터

**표 1. bbox 보정 (전체 PNG, 시작값)**
| 그림 | 쪽 | 현재 bbox | 시작값 | 증상 |
|---|---|---|---|---|
| 9.60 | 25 | [100,305,182,428] | [93,305,183,431] | V_in의 V가 왼쪽에서 잘림 |
| 9.76 | 28 | [322,134,398,233] | [322,129,400,236] | V_CC 위가 닿음 |
| 9.63 | 26 | [46,42,212,110] | y1 113 | 접지 아랫줄 |
| 9.64 | 26 | [84,218,178,306] | y1 309 | 접지 아랫줄 |
| 9.65 | 26 | [81,373,175,459] | y1 462 | 접지 아랫줄 |
| 9.72 | 27 | [256,428,362,513] | y1 516 | 접지 아랫줄 |
| 9.77 | 28 | [312,310,406,438] | y1 441 | 캡션 아랫부분 |
| 9.82 | 29 | [286,161,475,259] | y1 262 | 캡션 아랫부분 |
| 9.84 | 29 | [314,526,444,612] | y1 615 | 캡션 아랫부분 |
| 9.85 | 30 | [264,46,439,180] | y1 183 | 캡션 아랫부분 |

**표 2. 크롭 (이름 → 시작값, "측정"은 절차 M으로 새로 잰다)**
| 그림 | 쪽 | 현재 bbox | 크롭 | 사용 파일 |
|---|---|---|---|---|
| 9.2 | 2 | [850,40,1045,138] | a → [850,40,950,138] | E9.01, E9.02, E9.03, X9.01, X9.02, X9.03, P9.01 |
| 9.13 | 6 | [195,508,400,596] | a → [195,508,286,596] | E9.07(problem 항목), X9.07 |
| 9.15 | 7 | [135,148,465,238] | a → [135,148,228,238] | E9.08(problem 항목), X9.08 |
| 9.16 | 7 | [790,386,1040,500] | b → [938,386,1040,500] | E9.09, X9.09, P9.22 |
| 9.19 | 8 | [760,485,1080,637] | b → [972,485,1080,637] | E9.10, X9.10, P9.26 |
| 9.20 | 9 | [822,488,1015,642] | a → 측정 (왼쪽, x1≈919) / b → [919,488,1015,642] | a: P9.29, P9.30, P9.31 / b: E9.11, X9.11, P9.33 |
| 9.24 | 12 | [105,545,470,648] | c → [320,545,470,648] | E9.19, X9.19 |
| 9.34 | 15 | [755,530,1075,634] | c → [936,530,1075,634] | E9.17, X9.17 |
| 9.36 | 17 | [106,292,460,390] | c → 측정 | P9.53 |
| 9.38 | 18 | [175,100,430,302] | a → [175,100,430,189] | E9.21(problem 항목), X9.21, P9.51 |
| 9.74 | 28 | [36,245,211,347] | b → 측정 | P9.55 (P9.54는 a·b 둘 다라 전체 유지) |

**표 3. 참조 문구**
| 파일 | 수정 |
|---|---|
| P9.06 | 상속·참조의 Fig 9.43 줄에 `이 파일의 그림 목록에는 넣지 않음, 크롭은 fig9-43.png` 추가 |
| P9.38, P9.39 | Fig 9.24(b) 줄의 "크롭 안 함"을 `이 파일의 그림 목록에는 넣지 않음, 크롭은 fig9-24.png`로 바꿈 |

## 부록 D10 — ch10 데이터

**표 1. bbox 보정**
| 그림 | 쪽 | 현재 bbox | 시작값 | 증상 |
|---|---|---|---|---|
| 10.19 | 13 | [785,138,1060,265] | x1 1068 | (b) v_out이 오른쪽 끝에 닿음 |
| 10.97 | 42 | [64,90,204,195] | y1 190 | 캡션 윗부분이 들어옴 |
| 10.98 | 42 | [70,269,198,371] | y1 374 | 접지 아랫줄 |

**표 2. 크롭**
| 그림 | 쪽 | 현재 bbox | 크롭 | 사용 파일 |
|---|---|---|---|---|
| 10.1 | 2 | [135,482,525,628] | a → [135,482,525,575] (확인 필요) | E10.01(problem 항목), P10.01 |
| 10.3 | 3 | [105,440,485,630] | b → [322,440,485,562] / c → [230,562,365,630] | b: E10.03, X10.03 / c: E10.02 |
| 10.11 | 7 | [738,42,1112,182] | a → [738,42,915,182] / b → [930,42,1112,182] | a: P10.14, P10.16 / b: P10.15 |
| 10.16 | 11 | [735,430,1100,640] | abc → [735,430,1100,540] / a → [735,450,855,570] (둘 다 측정) | abc: E10.09(problem 항목), X10.09 / a: P10.23, P10.25, P10.26 |
| 10.18 | 13 | [145,378,460,497] | a → [145,378,292,497] | E10.10(problem), X10.10 |
| 10.19 | 13 | (표 1 반영 후) | a → [785,138,990,265] | E10.11(problem), X10.11 |
| 10.21 | 14 | [150,185,430,330] | a → [150,185,342,330] | E10.12(problem), X10.12 |
| 10.22 | 14 | [150,503,430,650] | a → [150,503,347,650] | E10.13(problem), X10.13 |
| 10.23 | 14 | [752,255,1090,476] | ab → [752,255,1090,375] | E10.14(problem), X10.14 |
| 10.36 | 21 | [795,132,1045,248] | a → [795,132,952,248] | E10.22(problem), X10.22 |
| 10.37 | 21 | [762,478,1085,628] | a → [762,478,947,628] | E10.23(problem), X10.23 |
| 10.38 | 22 | [155,212,438,352] | a → [155,212,352,352] | E10.24(problem), X10.24 |
| 10.41 | 23 | [172,140,414,348] | a → [172,140,338,348] | E10.25(problem), X10.25 |
| 10.44 | 24 | [172,96,410,250] | a → [172,96,337,250] | E10.26(problem), X10.26 |
| 10.58 | 29 | [770,42,1052,282] | a → [770,42,1052,182] ((a)와 (a-eq) 포함) | E10.29, X10.29 (P10.76은 전체 유지) |

**표 3. 참조 문구**
| 파일 | 수정 |
|---|---|
| E10.11 | Fig 10.18(a) 상속·참조 줄에 `이 파일의 그림 목록에는 넣지 않음, 크롭은 fig10-18.png` 추가. `연결:` 목록은 FORMAT 54행 형식(`Q_1: C = …, B = …, E = …`)으로 fig10-18.png를 보고 적음 |
| P10.20, P10.22 | "크롭은 문제 10.18 등에 있음"을 `이 파일의 그림 목록에는 넣지 않음, 크롭은 fig10-14.png`로 바꿈 |
| P10.59 | Fig 10.82 줄에 `이 파일의 그림 목록에는 넣지 않음, 크롭은 fig10-82.png` 추가 |
| P10.76 | frontmatter `refs`에 `"그림 10.58"` 추가 |

## 부록 D11 — ch11 데이터

**표 2. 크롭** (ch11에는 표 1과 표 3이 없다)
| 그림 | 쪽 | 현재 bbox | 크롭 | 사용 파일 |
|---|---|---|---|---|
| 11.4 | 3 | [162,575,425,655] | a → x 162–285 (측정) | E11.06, X11.06 |
| 11.5 | 3 | [780,52,1075,145] | a → x 780–900 (측정) | E11.04, E11.07, X11.04, X11.07 |
| 11.16 | 8 | [780,168,1070,280] | a → 측정 | E11.10(problem), X11.10 |
| 11.24 | 12 | [168,383,407,550] | a → 측정 | E11.12(problem), X11.12 |
| 11.28 | 13 | [63,304,482,470] | a → 측정 | E11.13(problem), X11.13 |
| 11.31 | 16 | [105,75,275,160] | ce → x 105–190 / cs → x 190–275 (측정) | ce: E11.15, X11.15 / cs: E11.16, E11.18, X11.16, X11.18 (P11.35, P11.39는 전체 유지) |
| 11.33 | 18 | [85,500,490,645] | a → 측정 | E11.17(problem), X11.17 |
| 11.38 | 20 | [765,333,1100,456] | a → 측정 | E11.19(problem), X11.19 |
| 11.43 | 23 | [158,136,430,274] | a → 측정 | E11.22(problem), X11.22 |
| 11.49 | 25 | [174,280,425,378] | a → 측정 | E11.24(problem), X11.24 |
| 11.56 | 28 | [104,516,492,652] | a → 측정 | E11.27(problem), X11.27 |
| 11.59 | 29 | [798,45,1080,216] | a → y 45–150 (측정) | E11.28(problem), X11.28 |
| 11.60 | 30 | [86,312,500,550] | a → 측정 | E11.29(problem) |

**크롭하지 않는 것**
- **P11.49 (Fig 11.50):** 참고용 본문 그림이라 FORMAT 55행 규칙에 맞는다.
- **X11.03 / E11.03 (Fig 11.3):** problem 패널 (a, b)와 answer 패널이 같다.
