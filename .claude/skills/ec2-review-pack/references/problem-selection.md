# 복습문제 선별 규칙 (메인 에이전트)

복습문제는 **workbook에 이미 있는 문제를 고르기만** 한다. 자작·변형 문제는 만들지 않는다. 모든 문제에 `## 풀이`가 있으므로 정답을 따로 계산하지 않는다.

## 1. 후보 목록
```bash
python3 <SKILL>/scripts/problem_index.py --repo <REPO> --used <REPO>/복습노트 --chapters <이번 범위 장, 예: 9,10> > <RUN>/candidates.tsv
```
- 열: `id  kind  secnum  section  difficulty  used  title`
- 종료 코드 1이면 stderr의 `ERROR` md는 후보에서 빠진 것이다. 보고서 "미해결"에 적는다(md는 고치지 않는다).
- `used`가 `USED`인 id는 이전 팩에서 썼으므로 고르지 않는다.

## 2. 범위 맞추기
- 요약의 `## 교과서 절 대조`에서 "다룸"인 절 번호 집합을 만든다(예: `{9.1.1, 9.1.2}`).
- 교과서 문제: `secnum`이 그 집합의 절이거나 그 하위 절(9.1.2 → 9.1.2.x)인 것만 후보다. `secnum`이 `10.2`처럼 상위 절이면 제목과 원문을 읽고 다룬 내용만으로 풀리는지 판단한다.
- `Design Problems`: 도전 문제로 최대 1개. 원문을 읽고 다룬 절만으로 풀리는 것만.
- 기출: `secnum`이 `ch9,10`처럼 장만 알려 주므로 **md 원문(`## 원문`)과 `## 풀이`를 읽고** 배운 내용만으로 풀리는지 확인한다.
- 풀이에 수업에서 안 다룬 개념(예: 아직 안 배운 주파수 응답, 피드백)이 한 단계라도 필요하면 제외.
- `forbidden_outside_preview` 용어가 핵심인 문제는 제외.

## 3. 구성
- 목표 10문항(8~12). 구성: 예제 2~3, 연습문제·장말문제 5~6, 기출 1~2.
- 난이도: `difficulty` 0 위주, 1~2는 한두 개.
- 한 절에 몰리지 않게 "다룸" 절마다 최소 1문항.
- 순서: 토픽(수업) 순서. 같은 토픽 안에서는 예제 → 연습문제 → 장말문제 → 기출.
- 후보가 8개보다 적으면 있는 만큼만 넣는다. 0개면 `problems: []`로 두고 PDF를 만들지 않는다. 채우려고 범위 밖 문제나 자작 문제를 넣지 않는다. 보고서에 "해당 문제 N개뿐"과 이유를 적는다.
- 이번 range의 수업이 전부 전자회로1 복습(Lec1–2)이면 workbook(9~11장) 범위 밖이므로 0개가 정상이다.

## 4. manifest에 적기
각 문제를 `{id, kind, anchor, date, why}`로 적는다(`references/manifest-guide.md`). `why`는 "캐스코드 출력저항 $g_m r_O^2$ 수치 계산"처럼 무엇을 연습하는지 한 줄.

## 5. PDF 만들기 (4단계 조립에서)
```bash
python3 <REPO>/workbook/build_workbook.py --ids <id1,id2,…(manifest 순서)> --name 복습문제_<range>_<slug> \
  --pdf-dir <REPO>/복습노트/<range> --build-dir <RUN>/workbook-build
```
- 결과: `복습노트/<range>/복습문제_<range>_<slug>-문제.pdf`, `-답안.pdf`.
- 종료 코드 2 또는 `ERROR` 줄: 그 id를 후보에서 같은 절의 다른 문제로 바꿔 manifest를 고치고 한 번만 다시 만든다. 또 실패하면 그 id를 빼고 "미해결"로 보고한다.
- `OVERFLOW <파일>: <id>`: PDF는 남는다. 그 문제 쪽이 넘친 것이므로 "미해결"로 보고한다(workbook md 수정은 이 스킬의 일이 아니다).
- 인터넷이 필요하다(Pretendard, KaTeX CDN).
