---
name: ec2-concept-check
description: 전자회로2 수업의 새 개념을 확인하는 즉시 채점 HTML(확인문제)을 기존 복습팩 근거로 만들 때 사용한다. 인자는 MMDD 또는 MMDD-MMDD다. 신규 ec2-review-pack의 최종 검사 후에도 실행한다.
---
# 전자회로2 확인문제

한 복습팩에서 처음 배운 개념을 5~10분 안에 확인하는 HTML을 만든다. 자구알 `ds-concept-check`와 같은 템플릿·채점·힌트·복기 동작을 사용한다. 날짜 범위는 폴더 이름과 같다. 이미 발행된 정리노트와 수업 전사를 읽어 이번 범위를 정한다.

- 공개 HTML은 `복습노트/<범위>/확인문제_<범위>_<slug>.html`에 둔다.
- 근거·문항·검사 기록은 같은 팩의 `.pack/자료_확인문제_<범위>_<slug>/`에 둔다.
- 작성·검토·화면 검사는 저장소 밖의 고유 RUN에서 수행한다. 발행 명령이 이전 산출을 백업한 뒤 통과한 후보를 반영한다.

## 실행

아래에서 `C`는 `<REPO>/.agents/skills/ec2-concept-check/scripts/concept.py`의 절대 경로, `RUN`은 `~/.cache/ec2-concept-check/<범위>-<고유 실행명>`의 절대 경로다. 독립 풀이자에게는 이 RUN과 별개인 임시 폴더를 할당한다.

1. `python3 "$C" prepare <범위> --repo "$REPO" --run "$RUN"`을 실행한다. 부모가 부르면 여기에 `--parent-run "$PARENT_RUN"`을 붙여 현재 최종 검사와 manifest·날짜별 STT 요약을 연결한다. 준비가 실패하면 원인과 경로를 보고한다.
2. `$RUN/source.json`의 정리노트 HTML·MD, 전사 및 신규 팩의 요약을 읽고 `$RUN/objectives.json`을 작성한다. [문항 규칙](references/items.md)을 적용해 회고·예고·보충을 걷어 내고, 토픽 ID·날짜·슬라이드·STT 위치를 기록한다. 보통 6~16문항을 확보하고, 근거가 있는 목표가 적으면 실제 확보한 수와 이유를 보고한다.
3. 새 컨텍스트의 문항 작성자 한 명에게 [문항 규칙](references/items.md), `source.json`, `objectives.json`을 넘겨 `$RUN/items.json`을 작성하게 한다. 메인은 출제 근거, 정답 유도, 보기의 오개념, 기존 복습문제와 중복, 힌트의 적절성을 검토한다. `python3 "$C" check --run "$RUN"`을 통과시킨다.
4. `python3 "$C" blind-make --run "$RUN" --out "$BLIND"`로 사본을 만든다. 작성자와 다른 새 컨텍스트의 독립 풀이자 한 명에게 `$BLIND/문제.md`와 딸린 SVG만 전달한다. SVG는 실제로 열어 보게 한다. 답안표는 `| ID | 답 | 이의 |` 형식으로 별도 파일에 받는다. 이의가 없으면 빈 칸을 둔다. `python3 "$C" blind-record --run "$RUN" --answers "$ANSWERS" --round 1` 뒤 `python3 "$C" blind-status --run "$RUN"`을 확인한다. 불일치·이의는 근거를 대조해 문항을 고친 뒤 `blind-make --only q…`로 해당 문항을 새 풀이자에게 검토받는다. 전체 최대 3회이며 이의가 남으면 보류한다.
5. `python3 "$C" build --run "$RUN"`과 `python3 "$C" browser --run "$RUN"`을 순서대로 실행한다. 로컬 Playwright Chromium에서 데스크톱·모바일, 밝은·어두운 테마를 검사한다. `$RUN/shots/`의 네 모드 스크린샷을 열어 수식, 회로도, 힌트·복기 창의 잘림과 가독성을 확인한다. 내용을 다시 빌드하면 화면 검사를 다시 한다.
6. `python3 "$C" publish --run "$RUN"`으로 발행한다. 공개 HTML, 검증 기록, 문항 수와 형식, 블라인드 회차별 결과, 화면 검사와 이전본 백업 경로를 보고한다. 부모 호출에서 끝내 통과하지 못하면 `python3 "$C" withhold --parent-run "$PARENT_RUN" --reason "<실제 보류 이유>"`로 남기고 부모 보고를 계속한다. 커밋은 제안만 한다.
