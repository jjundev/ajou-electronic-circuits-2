# 전자회로2 문제풀이 입문 설명(ec2-problem-explain) 설계

## 확정된 의도

머신러닝기초 `ml-problem-explain`(ajou-ml-basics 커밋 `ca3660a`~`d83c64d`)을 전자회로2 로컬 스킬 `ec2-problem-explain`으로 이식한다. 복습팩이 이미 고른 workbook 문제(`복습노트/<range>/problems.txt`의 id → 교과서·기출 문제 md)마다 **문제의 단서 → 떠올릴 개념과 공식 → 첫 줄 → 단계별 이유 → 완성 답 → 검산 → 함정 → 다시 풀기** 일곱 구역을 펼친 설명 HTML+MD를 만든다. 대상은 Razavi 이론은 읽었지만 회로 문제풀이 경험이 적은 학생이다.

완료 기준: `/ec2-problem-explain 1007` → `복습노트/1007/문제설명_1007_Differential_Amplifiers.html/.md`가 네 실제 검토(원문 대조·내용·독립 검산·브라우저)를 통과한 뒤에만 발행되고, 원본 md·PDF·정리노트는 바뀌지 않으며, 스킬 테스트가 모두 통과한다.

사용자 결정: #11 ec2-review-pack 연동 = **이번엔 스킬만 [confirmed]**, #12 대상 = **복습팩 날짜만 [confirmed]**. 나머지는 추천값으로 확정.

## 동작

- `/ec2-problem-explain 1007`: 그 날짜 팩의 problems.txt 순서대로 전 문항.
- `/ec2-problem-explain 0923-1002`: 날짜별 팩을 각각 처리, 팩별 독립 성공/실패. 정확히 같은 이름의 통합 폴더와 개별 폴더가 함께 있으면 후보 목록을 보이고 멈춘다.
- 인자 없음: problems.txt가 있는 팩 중 폴더명 끝 날짜가 가장 늦은 팩.
- problems.txt가 없는 팩(0902·0904)을 명시하면 "문제 없는 팩"으로 멈춘다.
- 각 문항: 왼쪽 목차·이전/다음·우측 요약(떠올릴 개념·공식 / 첫 줄 / 핵심 판단 / 검산)·다크모드, 로컬 KaTeX·Pretendard(오프라인).
- 원문·조건·구할 것·문제 그림은 md에서 그대로 붙인다(재작성 금지).
- md `## 풀이`와 독립 검산이 다르면 해당 팩을 disputed로 보류·보고. md는 고치지 않는다(`workbook-solution` 몫).
- 보고: 팩별 published/withheld, 문항·소문항 수, HTML/MD 링크, RUN, 백업 경로.

## 범위 밖

ec2-review-pack 자동 연동, 기존 팩 backfill 실행, 기출 회차·임의 id 대상, 설계과제, 새 출제·PDF·영상·자동 채점·workbook md 풀이 수정.

## 접근

A(채택): ML 스킬 포크 + 소스 어댑터만 workbook md로 교체 + 발행·백업 계층 이식. 저장소 독립 구조를 유지하며 ML의 계약·검토 게이트·테스트를 물려받는다.

## 구조

- 위치 `.claude/skills/ec2-problem-explain/`, 등록 `.agents/skills/ec2-problem-explain` → `../../.claude/skills/ec2-problem-explain` 상대 심볼릭 링크. 모듈 접두사 `epe_`.
- 재사용(읽기 전용 import): `workbook/problem.py`(`load_problem`, `html_fields`, `problem_figures`, `solution`), `workbook/assemble.py`(`TEXTBOOK_ID_RE`, `EXAM_ID_RE`, `KIND_DIR`), `.claude/skills/ec2-review-pack/scripts/html2md.py`(`Node`, `Ctx`, `convert`, `check_md`), `check_html.math_delimiter_errors`.
- 새로 소유: md 소스 어댑터, 발행(잠금·백업·교체·복구), ML 템플릿+vendor 자원(색 토큰은 EC2 정리노트 템플릿).
- 소문항: `## 구할 것` 최상위 항목의 선두 `(1)`/`(a)` 표지. 없으면 `main`. 섞이면 오류.
- 입력 무결성: problems.txt + 각 md + 각 문제 그림 바이트를 순서대로 묶은 SHA-256. 발행 직전 재추출해 같아야 한다.
- 산출: `복습노트/<range>/문제설명_<range>_<slug>.html/.md`, `figures_문제설명_<range>_<slug>/`, `자료_문제설명_<range>_<slug>/`. slug는 같은 폴더의 `정리노트_<range>_<slug>.html`. 읽음 키 `ec2-problem-explain-review-<range>-<slug>`.
- 저작: 문항마다 opus 작성자 병렬. 독립 검산은 작성자와 다른 에이전트가 SymPy 기호 계산+수치 대입, 증명·정성은 논증 검토. `source_visual`은 frontmatter `pdf_page`와 `workbook/source_pages.py render`로 원본 쪽 대조.
- 회로 문제용 저작 지침: 소신호 등가회로 첫 줄, 하프 서킷, KCL/KVL, $g_m$·$r_o$ 기호 뜻, 근사 조건($\lambda\to0$, $r_o\gg R_D$). verify에 극한 대입·단위·차수·대칭 특수값.
