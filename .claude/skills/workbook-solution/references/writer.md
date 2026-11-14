# 풀이 작성 — <<LABEL>> 배치 <<BATCH>>

당신은 작성 에이전트다. 작업 폴더는 <<WT>>이고 모든 명령은 여기서 실행한다(cd <<WT>>).
먼저 읽는다: <<SKILL>>/references/rules.md, <<SKILL>>/references/lessons.md, 교과서/마이크로전자회로/FORMAT.md의 '문제집용 절'. 기출이면 from_the_past/md/FORMAT-EXAM.md도 읽는다.

## 0. 리뷰 반영 (반영할 보고서: <<REPORTS>>, "없음"이면 건너뜀)
- 지적마다 직접 다시 계산해 판단한다. 동의하면 고치고, 동의하지 않으면 고치지 않고 이유를 최종 메시지에 적는다.
- 조건 문제 지적을 받아들이면 `## 조건`·`## 구할 것`을 고친다(원문에 없는 보충은 FORMAT.md대로 `(원문에 없음)`). 그리고 풀이 첫 단계의 가정 줄을 지운다.
- 검사(3)를 돌린다.
- 조건을 고쳤으면 그 md만 먼저 커밋한다: git commit -m "docs(<<LABEL>>): fix 조건 for <ids>"
- 나머지와 보고서를 커밋한다: git commit -m "docs(<<LABEL>>): apply review fixes to solutions batch <보고서 글자들>". 고친 것이 없어도 보고서는 커밋한다.

## 1. 대상 (<<TARGETS>>, "없음"이면 4의 최종 메시지로)
md마다 다음을 한다.
- md 전체를 읽는다: 원문, 조건, 구할 것, 회로 넷리스트와 단자·배치 설명, 상속·참조, 답 (검증용), 힌트.
- 이미지 줄(![Fig …](…png))이 가리키는 그림을 Read로 연다(md 기준 상대 경로).
- 원본 쪽이 필요하면 python3 workbook/source_pages.py render <md> --out <<PAGES>> 로 그려 본다.
- 푼다. 모든 수치를 **검산**한다: <<PAGES>>/calc-<id>.py에 식을 적어 python3로 돌리고, 풀이의 숫자는 그 출력에서 옮긴다. 검산 파일은 md에 넣지 않는다.
- 예제는 rules.md '예제'대로 `## 답 (검증용)`과 대조한다.

## 2. 쓰기
- rules.md를 따른다. `## 풀이`는 파일 맨 끝(`## 힌트`가 있으면 그 뒤)에 빈 줄 하나를 두고 붙인다.
- md의 다른 절은 고치지 않는다. 조건 문제는 rules.md '조건이 모자라거나 틀릴 때'대로 한다.

## 3. 검사
<<CHECK_CMD>>
python3 workbook/build_workbook.py --ids <대상 id들, 쉼표로> --name 풀이-<<LABEL>>-<<BATCH>> --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"
검사 오류가 0이고 빌드 출력이 빌 때까지 고친다. OVERFLOW는 rules.md '분량'대로 줄인다.

## 4. 커밋
git add <대상 md 경로들>
git commit -m "docs(<<LABEL>>): add solutions batch <<BATCH>> (<첫 id>–<끝 id>)"
git add에는 경로를 명시한다(-A나 . 금지). push하지 않는다.

## 최종 메시지
- 커밋 해시(조건 수정, 반영, 배치 커밋)
- 예제 대조: "<id> — 일치 | 다름 (교재 <값>, 계산 <값>, <이유>)" (예제가 없으면 생략)
- 애매한 곳: "<id> — <무엇을 어떻게 해석·가정했는지>" (없으면 "없음")
- 조건 문제: "<id> — <무엇이 모자라거나 틀린지, 둔 가정>" (없으면 "없음")
- 반영하지 않은 지적과 이유
