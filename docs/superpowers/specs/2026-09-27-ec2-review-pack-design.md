# 전자회로2 복습팩 스킬 (`ec2-review-pack`) 설계

## 목적
머신러닝기초 `ml-review-pack`을 본떠 전자회로2 저장소에 복습팩 스킬을 만든다. `/ec2-review-pack [MMDD|MMDD-MMDD] [lite]`를 부르면 `복습노트/<range>/`에 다음이 생긴다.

- **정리노트**: ML과 같은 `note-template.html`로 만든 HTML과 MD. 만드는 과정도 ML과 같다(STT 요약 → manifest → 섹션 작성 → 조립 → 검사 → 리뷰 → 브라우저 검사 → MD 변환).
- **복습문제**: 그 기간 수업 내용에 맞는 workbook 문제 약 10개를 골라 기존 `workbook/build_workbook.py`로 만든 문제 PDF와 답안 PDF.

완료 기준: 0923 한 날짜로 돌렸을 때 위 산출물이 생기고 모든 검사를 통과한다.

## 동작
- `/ec2-review-pack 0923`을 부르면 `복습노트/0923/`에 다음이 생긴다.
  - `정리노트_0923_<slug>.html`, `.md`
  - `복습문제_0923_<slug>-문제.pdf`, `-답안.pdf`
  - `problems.txt`
  - `figures_0923/`(필요할 때만)
- 인자가 없으면 가장 최근 팩의 끝 날짜 다음부터 STT를 모두 쓴다. 팩이 하나도 없으면 사용 가능한 STT 날짜를 보여 주고 멈춘다.
- 정리노트의 마지막 "요약 · 예고" 섹션에 문제 PDF와 답안 PDF 링크를 넣는다.
- 기간에 맞는 workbook 문제가 없으면(예: 0902–0904 Intro, 전자회로1 복습) PDF와 `problems.txt`를 만들지 않고, 보고서에 "해당 문제 없음"과 이유를 적는다. 자작 문제는 만들지 않는다.

## 이번에 하지 않는 것
- ML 스킬과 공용 스킬로 합치기: 잘 돌아가는 ML 파이프라인에 회귀 위험이 생긴다.
- 워크북에 없는 범위의 문제 새로 만들기: "고르기만 한다"는 원칙과 어긋난다.
- 복습문제 HTML(`review-template.html`): PDF로 대체한다.
- `workbook/` 코드 수정: 지금 있는 `--ids/--name/--pdf-dir/--build-dir`로 충분하다.

## 접근
ML 스킬을 복사한 뒤 복습문제 경로(카드, review 템플릿, answers.py)를 빼고 "문제 선별 → build_workbook" 단계를 넣는다(A안). 공용화(B안)는 ML 회귀 위험 때문에, 새로 작성(C안)은 검증 장치를 잃기 때문에 택하지 않았다.

## 구성 (`.claude/skills/ec2-review-pack/`)
| 파일 | 역할 |
|---|---|
| `SKILL.md` | 0~9단계 절차 |
| `assets/note-template.html` | ML 파일을 바이트 그대로 복사 |
| `scripts/manifest.py` | manifest 검증. `problems`는 workbook id 목록. PDF 이름 계산 |
| `scripts/assemble.py` | 정리노트만 조립하고 `problems.txt`를 쓴다 |
| `scripts/check_html.py` | 정리노트만 검사 |
| `scripts/html2md.py` | 정리노트 하나만 MD로 변환 |
| `scripts/problem_index.py` | workbook 문제 목록 TSV. 이전 팩에서 쓴 문제에 `USED` 표시 |
| `references/*.md` | 요약, manifest, 섹션 작성, 위젯, 문제 선별, 리뷰, 브라우저 검사 |
| `tests/` | ML 테스트를 이식하고 새 기능 테스트를 더함 |

## manifest 규약
- 최상위 키: `course, range, slug, note_title, note_subtitle, footer_note, sessions, sections, preview_topic, forbidden_outside_preview, problems, links`
- `problems[]`: `{id, kind, anchor, date, why}`
  - `id`: workbook id(`E9.01`, `X10.03`, `P11.20`, `2023-1_기말-Q1`)
  - `kind`: id에서 정해진다(예제·연습문제·장말문제·기출)
  - 개수: 0~12개
  - 파일 존재 여부는 `manifest.py <manifest> <REPO>`로 검사한다.
- `links`: 문제가 있으면 문제 PDF와 답안 PDF 링크가 모두 있어야 한다. 문제가 없으면 두 링크가 없어야 한다.
- 이름 규칙
  - 정리노트: `정리노트_<range>_<slug>.html`
  - 문제 묶음 이름: `복습문제_<range>_<slug>`
  - PDF: 묶음 이름 + `-문제.pdf`, `-답안.pdf`

## 확정된 결정
| # | 결정 | 값 |
|---|---|---|
| 1 | 위치와 이름 | `전자회로2/.claude/skills/ec2-review-pack` |
| 2 | 템플릿 | `note-template.html`을 바이트 그대로 복사. review 템플릿은 가져오지 않음 |
| 3 | PDF 생성 | `build_workbook.py --ids … --name 복습문제_<range>_<slug> --pdf-dir 복습노트/<range> --build-dir RUN/workbook-build` |
| 4 | 문제 매칭 | md frontmatter의 `section:` 번호와 요약의 슬라이드 대조표. 기출은 원문을 읽고 판단 |
| 5 | 중복 방지 | 팩마다 `problems.txt`(`id \| why`)를 두고 `problem_index.py --used 복습노트`로 확인 |
| 6 | 빌드 실패 | ERROR가 나면 대체 id로 한 번 재시도. OVERFLOW는 미해결로 보고 |
| 7 | 검사 대상 | check_html, 리뷰, 브라우저 검사, html2md 모두 정리노트만 |
| 8 | 인자 없음 + 팩 없음 | STT 날짜만 보여 주고 멈춤 |
| 9 | 과목 정보 | 과목 전자회로2, 교수 권익진, 교재 Razavi *Microelectronics* 2e, 강의노트 `2026F_Lec<N>_*.pdf` |
| 10 | 커밋 | 스킬은 커밋을 제안만 한다 |
| 11 | 답안 PDF | 포함 [confirmed by default] |
| 12 | 기출 | 포함. 1~2개 [confirmed by default] |
| 13 | workbook 범위 밖 기간 | 정리노트만 만듦. 자작 문제 없음 [confirmed by default] |
| 14 | 문항 수와 구성 | 목표 10개(8~12). 예제 2~3, 연습·장말 5~6, 기출 1~2 [confirmed by default] |
