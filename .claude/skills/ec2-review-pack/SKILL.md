---
name: ec2-review-pack
description: 전자회로2 수업의 STT·강의노트·Razavi 교과서로 ELI5 정리노트 HTML(+MD, 그림)을 만들고, 수업 범위에 맞는 미사용 workbook 문제를 기출 우선 최대 20개 선발해 복습문제 PDF(문제+답안)와 검토를 통과한 문제설명 HTML·MD를 날짜별 폴더에 저장한다. 참고 풀이 없는 문제도 직접 풀고 독립 검증한다. "정리노트", "복습문제", "복습팩", "0923 정리해줘" 또는 /ec2-review-pack [MMDD|MMDD-MMDD] [lite]에 사용한다.
---
# 전자회로2 복습팩

인자 `[MMDD | MMDD-MMDD] [lite]`를 유지한다. STT·강의자료·Razavi로 ELI5 정리노트 HTML/MD·그림, 미사용 기출 우선 최대 20문항의 문제/승인 답안 PDF와 문제설명을 만든다. 중간 질문 없이 진행하고 끝에 한 번 보고한다. 커밋은 제안만 한다.

메인은 배치·예외 판단·최상위 발행을 맡는다. 먼저 [실행·역할 계약](references/delegation.md)을 읽는다. 실행기는 에이전트나 모델을 호출하지 않는다. 원문·전체 후보·작업자 보고·스크립트 구현·다른 날짜 예시를 메인에 일괄 적재하지 않는다.

1. [준비](references/execution-guide.md)의 `0. 준비`에서 REPO·기간·새 RUN을 정한다. 실제 브라우저/PDF 도구 접근성을 확인한다. [runner 계약](references/runner-contract.md)의 시작 명령으로 `init`한다. RUN은 `--run`을 빼서 `~/.cache/ec2-review-pack/<range>-<시각>`에 둔다. `/tmp`는 재부팅 때 지워지므로 쓰지 않는다. REPO는 디스크 표기 그대로 넘기면 되고, 실행기와 작업자는 경로를 NFC로 쓰고 비교한다. 새 RUN 또는 보류된 RUN에서 이어받은 새 RUN만 지원하며 기존 수기 상태/승인을 변환하지 않는다. 보류 뒤 다시 돌릴 때는 runner 계약의 `이어받기`를 따른다.
2. 같은 CLI의 `status --run <RUN>` 및 `next --run <RUN> --slots <현재 가용 작업자 수>`로 현재 근거와 다음 행동을 받는다. `dispatch`는 claim→새 컨텍스트 spawn→bind→receipt accept, 동시 작업자는 기본 5명이다. spawn 지시문은 [작업자 템플릿](references/worker-prompt.md)을 채워 쓴다. `run`은 요청된 action 한 개, `review_locally`는 메인의 실제 검사다. 상세 인자는 runner 계약의 해당 절만 읽는다.
3. 작업자는 생성 브리프의 참조 절·고정 입력·허용 출력·PROFILE 전체를 직접 읽는다. 작성자는 [내용 규칙](references/content-rules.md), 요약자는 [STT 지시문](references/stt-summary-prompt.md)을 따른다. 상세 보고는 RUN에 두고 반환은 **800자 이하**로 task/status/receipt 경로를 보낸다. 자식 조정자는 모든 leaf 브리프에도 같은 제한을 전파한다.
4. 각 역할은 인계 전에 [역할·파일 인계 계약](references/delegation.md)의 `인계 전 묶음 점검`을 수행하고 기존 보고에 근거·미해결을 남긴다. 이 자체 점검은 독립 검산·최종 화면 검토를 대체하지 않는다.
5. 수정/재개·중단·복구는 runner 계약을 따른다. 내용 수정은 감사·리뷰 결함 전체(노트 밖 문제 ID 포함)를 한 요청에 담고, 일부러 뺀 항목은 `waived`에 이유와 함께 적는다. 내용 수정 최대 1회, 기계/브라우저 수정은 **공통 최대 2회**다. 현재 입력 변경은 관련 승인을 무효화한다. 최초 두 백업을 덮거나 상태 JSON을 손으로 완료 처리하지 않는다.
6. [문제설명 통합](references/problem-explain-integration.md)은 해당 역할/발행 때만 읽는다. 문제 0개는 PDF·자식을 생략하되 모든 토픽 감사와 유예 없는 final-check가 필요하다. lite는 부모 내용 리뷰만 생략하며 **부모 개인화 감사는 메인이 실제 수행**한다. 자식 독립 검산·네 검토·전체 감사와 실제 전 페이지 PDF 검토는 유지한다.
7. 신규 팩은 일반·lite 및 문제 0개 모두 `next.kind=concept_check`에서 [ec2-concept-check](../../../.agents/skills/ec2-concept-check/SKILL.md)를 같은 범위로 실행한다. 이 단계는 현재 `final-check` 성공 뒤에 열린다. `next.parent_run`을 넘겨 별도 RUN에서 작성·독립 풀이·브라우저 검사·발행 또는 보류 기록까지 이어간다.
8. `report`로 파일·검사·발행·백업/복구·withheld를 집계한다. 확인문제는 발행·보류 사유를 별도로 보고한다. 실제 발행 게이트와 유예 없는 최종 검사가 현재 바이트에 통과해야 완료다. 미실시 검토·실패·withheld는 일부 완료로 보고한다.

PDF는 16:9, 1920×1080 기준 하단 180px 자막 여백을 유지한다. 원문 MD 오류 외 렌더/OVERFLOW 때문에 문항을 교체하지 않는다. 원본은 읽기 전용이며 작업자는 지정 RUN만 쓴다. `RUN/repo` 링크도 예외가 아니다. 발행·전체 복구는 최상위 메인만 실행한다.

기존 팩에 왜 페이지 붙이기는 [상세의 해당 절](references/execution-guide.md#기존-팩에-왜-페이지-붙이기)만 따른다. 기존 교육·검토 기준을 줄이지 않는다.
