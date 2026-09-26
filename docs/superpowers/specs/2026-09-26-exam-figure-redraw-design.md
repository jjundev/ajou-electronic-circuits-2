# 기출 회로도 다시 그리기 설계

## 목적
기출 4회차(2021-1 중간·기말, 2023-1 중간·기말)의 문제 그림 18장을 schemdraw로 다시 그려 문제집 PDF에 넣는다.
- 2023 그림 8장(중간 Q2·Q3·Q4, 기말 Q1–Q5)은 채점된 답안지 스캔이라 손글씨 풀이, 커패시턴스 라벨, X 표시가 겹쳐 있다.
- 2021 그림 10장(중간 Q2–Q5, 기말 Q1–Q6)은 깨끗하지만 문제집 전체 스타일을 맞추려고 같이 다시 그린다.

끝난 모습: 기출 4회차 문제지가 모두 같은 스타일의 깨끗한 회로도로 나오고, 원본(Razavi 시험지)과 배치·라벨 위치가 같다.

분류: architectural. 그림을 만드는 새 경로(코드 → PNG)를 더하고 문제집 생성기의 그림 고르기를 바꾼다.

## 동작
- `python3 from_the_past/md/_tools/draw_exam.py <시험 폴더>`: `figures/redrawn/fig-Q<n>.py`마다 `draw()`를 불러 `fig-Q<n>.png`를 만든다.
  - 그리기 코드가 실패하면 `ERROR <파일>: <이유>` 줄을 찍고 종료 코드 1로 끝난다. 나머지 그림은 계속 그린다.
  - 문제집에 찍힐 라벨 글자 크기가 7–11pt를 벗어나면 `WARN` 줄을 찍는다.
- `--compare <out.png>`: 크롭(위)과 다시 그린 그림(아래)을 같은 폭으로 쌓은 대조 시트를 만든다.
- `verify_exam.py`: `redrawn/`의 `.py`와 `.png` 짝, figures.yaml id를 검사한다. `--redraw`는 코드로 다시 그려 바이트가 같은지 본다.
- `build_workbook.py`: 기출에서 `figures/redrawn/fig-<id>.png`가 있으면 그것을 넣고, 없으면 크롭을 넣는다.

## 이번에 하지 않는 것
- 교과서 문제 그림: 오염되지 않았다.
- 넷리스트에서 자동 배치: MOS 회로를 원본처럼 자동 배치하기 어렵고, 그림도 18장뿐이다.
- md의 이미지 링크와 `> 참고: 답안지 손글씨가 겹침` 줄: md는 원본을 옮긴 기록이라 크롭을 그대로 가리킨다.

## 방식
| 선택지 | 방식 | 장점 | 단점 | 채택 |
|---|---|---|---|---|
| A | schemdraw로 그림마다 손으로 코딩. md의 넷리스트·표시·배치 bullet이 명세 | 깨끗하고 다시 만들 수 있음. mathtext 첨자 | 18장 수작업 | ✔ |
| B | 이미지 처리로 잉크 제거 | 빠름 | 손글씨가 인쇄와 같은 검정 펜이라 회로 선도 지워짐 | — |
| C | lcapy/circuitikz 자동 렌더링 | 넷리스트 재사용 | LaTeX 없음, 자동 배치가 원본과 다름 | — |
| D | hwp에 든 원본 그림 추출 | 원본 그대로 | 깨끗한 원본은 기말 Q1(b) 하나뿐 | 대조 참고로만 |

## 구현
- `from_the_past/md/_tools/schem_style.py`: 공통 스타일.
  - `nmos`, `pmos`: 벌크 없음, 소스 화살표, `mirror`(게이트 오른쪽).
  - `save_png`: 432 dpi, 흰 배경, 메타데이터 없음 → 같은 코드면 같은 바이트.
- `from_the_past/md/<시험>/figures/redrawn/fig-Q<n>.py`: `def draw() -> schemdraw.Drawing`. 여러 패널은 한 Drawing에 나란히 그리고 `(a)`, `(b)` 캡션을 붙인다.
- `from_the_past/md/_tools/draw_exam.py`: 위 '동작'.
- `verify_exam.py`: `check_redrawn`과 `--redraw`(`check_redraw`)를 추가한다. 기존 `check_figures`는 `fig_dir.glob("*.png")`로 바로 아래만 보므로 영향이 없다(`_tools/verify_exam.py:100`).
- `workbook/problem.py` `figures()`: 인쇄 폭은 크롭 PNG의 w_mm, 높이는 다시 그린 그림의 비율로 정한다. 크롭은 크기 기준이라 계속 있어야 한다.
- 의존성: `pip3 install --user --break-system-packages schemdraw matplotlib` (schemdraw 0.23, matplotlib 3.11에서 확인).

## 그림 내용의 기준
- 연결은 md `## 회로` 넷리스트, 모양은 `- 단자:`·`- 표시:`·`- 배치:` bullet을 따른다. 크롭은 배치를 눈으로 참고할 때만 쓴다.
- 2023 기말 Q1(b)는 hwp에서 뽑은 원본 그림(`2023 전회2 기말.hwp`의 BinData `BIN0001.PNG`)도 대조한다.
- `> 참고:` 줄에 적힌 손글씨 획은 그리지 않는다.
- 2023 중간 Q2의 ③번 접속점(점 여부 판독 불가)은 점을 찍는다. T자 분기라 뜻이 같다.

## 프로토타입에서 확인한 schemdraw 사실 (0.23)
- `AnalogNFet`/`AnalogPFet`의 기본 방향은 게이트가 오른쪽이다. `.reverse()`로 게이트를 왼쪽에 둔다.
- `offset_gate=False`를 줘야 게이트가 채널 가운데에 온다.
- `.right()`를 주지 않으면 앞 요소의 진행 방향(예: `Line().up()`)을 물려받아 기호가 90° 돈다.
- `d.add()` 뒤에 `.anchor().at()`을 불러도 위치가 바뀌지 않는다. 방향과 위치는 add 전에 정한다.
- `Drawing.save()`는 매번 다른 바이트를 낸다. `drawing.draw(show=False).fig.savefig(..., metadata={"Software": None})`는 같은 바이트를 낸다.

## 결정
| # | 결정 | 답 |
|---|---|---|
| 0 | 방식 | A |
| 1 | 대상 | 4회차 18장 [확정] |
| 2 | 크롭 | 지우지 않음. 다시 그린 그림은 `figures/redrawn/` |
| 3 | 그림 고르기 | redrawn 파일이 있으면 우선 |
| 4 | 인쇄 크기 | 폭 = 크롭 w_mm, 높이 = 다시 그린 그림 비율 |
| 5 | 연결의 기준 | md 넷리스트와 배치 bullet |
| 6 | 판독 불가 접속점 | 점을 찍음 |
| 7 | md 이미지 링크 | 그대로 |
| 8 | 의존성 | `--user --break-system-packages` |
| 9 | 그림 모양 | 원본 배치·라벨 위치 재현 [확정] |
| 10 | 2021 포함 | 포함 [확정] |
