---
name: ec2-concept-check
description: 전자회로2 수업의 새 개념을 확인하는 즉시 채점 HTML(확인문제)을 기존 복습팩 근거로 만들 때 사용한다. 인자는 MMDD 또는 MMDD-MMDD다. 병렬 부모에서는 검토된 후보로 일찍 준비하고 부모 최종 검사 뒤 발행한다.
---
# 전자회로2 확인문제

한 복습팩에서 처음 배운 개념을 5~10분 안에 확인하는 HTML을 만든다. 자구알 `ds-concept-check`와 같은 템플릿·채점·힌트·복기 동작을 사용한다. 날짜 범위는 폴더 이름과 같다. 공개 정리노트 또는 부모가 검토한 후보와 수업 전사를 읽어 이번 범위를 정한다.

- 공개 HTML은 `복습노트/<범위>/확인문제_<범위>_<slug>.html`에 둔다.
- 근거·문항·검사 기록은 같은 팩의 `.pack/자료_확인문제_<범위>_<slug>/`에 둔다.
- 작성·검토·화면 검사는 저장소 밖의 고유 RUN에서 수행한다. 발행 명령이 이전 산출을 백업한 뒤 통과한 후보를 반영한다.

## 실행

아래에서 `C`는 `<REPO>/.agents/skills/ec2-concept-check/scripts/concept.py`의 절대 경로, `RUN`은 `~/.cache/ec2-concept-check/<범위>-<고유 실행명>`의 절대 경로다. 독립 풀이자에게는 이 RUN과 별개인 임시 폴더를 할당한다.

문항 작성자와 독립 풀이자(재풀이 포함)에게는 현재 실행 환경이 서브에이전트에 지정할 수 있는 모델 중 **두 번째로 높은 등급의 모델**을 사용한다. 선택 가능한 모델이 하나면 그 모델을 사용한다. 환경이 제공하는 등급 순서를 확인할 수 없으면 환경의 기본 모델을 사용하고 이유를 최종 보고에 적는다. 단독 실행과 신규 복습팩에서의 호출 모두에 적용한다.

1. `python3 "$C" prepare <범위> --repo "$REPO" --run "$RUN"`을 실행한다. 부모가 부르면 여기에 `--parent-run "$PARENT_RUN"`을 붙여 현재 최종 검사와 manifest·날짜별 STT 요약을 연결한다. 준비가 실패하면 원인과 경로를 보고한다.
2. `$RUN/source.json`의 정리노트 HTML·MD, 전사 및 신규 팩의 요약을 읽고 `$RUN/objectives.json`을 작성한다. [문항 규칙](references/items.md)을 적용해 회고·예고·보충을 걷어 내고, 토픽 ID·날짜·슬라이드·STT 위치를 기록한다. 보통 6~16문항을 확보하고, 근거가 있는 목표가 적으면 실제 확보한 수와 이유를 보고한다.
3. 새 컨텍스트의 문항 작성자 한 명에게 [문항 규칙](references/items.md), `source.json`, `objectives.json`을 넘겨 `$RUN/items.json`을 작성하게 한다. 메인은 출제 근거, 정답 유도, 보기의 오개념, 기존 복습문제와 중복, 힌트의 적절성을 검토한다. `python3 "$C" check --run "$RUN"`을 통과시킨다.
4. `python3 "$C" blind-make --run "$RUN" --out "$BLIND"`로 사본을 만든다. 작성자와 다른 새 컨텍스트의 독립 풀이자 한 명에게 `$BLIND/문제.md`와 딸린 SVG만 전달한다. SVG는 실제로 열어 보게 한다. 답안표는 `| ID | 답 | 이의 |` 형식으로 별도 파일에 받는다. 이의가 없으면 빈 칸을 둔다. `python3 "$C" blind-record --run "$RUN" --answers "$ANSWERS" --round 1` 뒤 `python3 "$C" blind-status --run "$RUN"`을 확인한다. 불일치·이의는 근거를 대조해 문항을 고친 뒤 `blind-make --only q…`로 해당 문항을 새 풀이자에게 검토받는다. 전체 최대 3회이며 이의가 남으면 보류한다.
5. `python3 "$C" build --run "$RUN"`과 `python3 "$C" browser --run "$RUN"`을 순서대로 실행한다. 로컬 Playwright Chromium에서 데스크톱·모바일, 밝은·어두운 테마를 검사한다. `$RUN/shots/`의 네 모드 스크린샷을 열어 수식, 회로도, 힌트·복기 창의 잘림과 가독성을 확인한다. 내용을 다시 빌드하면 화면 검사를 다시 한다.
6. `python3 "$C" publish --run "$RUN"`으로 발행한다. 공개 HTML, 검증 기록, 문항 수와 형식, 블라인드 회차별 결과, 화면 검사와 이전본 백업 경로를 보고한다. 부모 호출에서 끝내 통과하지 못하면 `python3 "$C" withhold --parent-run "$PARENT_RUN" --reason "<실제 보류 이유>"`로 남기고 부모 보고를 계속한다. 커밋은 제안만 한다.

### 병렬 부모의 후보로 일찍 준비하기

`concept_contract=1`인 병렬 부모에서는 `pack_cli.py next`가 `concept-draft`를 제시하면 `pack_cli.py run --run "$PARENT_RUN" --action concept-draft`를 실행한다. 부모가 승인한 HTML·MD·SVG·선발 자료, manifest·STT 요약과 공개 퀴즈가 사용할 로컬 폰트·스크립트를 묶는다. 직접 준비할 때는 `prepare`에 `--parent-run "$PARENT_RUN" --candidate-pack "$CANDIDATE"`를 지정한다. `CANDIDATE`는 부모의 현재 `actions.convert-md.candidate_root`다. 최종 검사 이후에는 후보 인자를 생략해 공개본으로도 준비할 수 있다. 이 부모가 소유하는 날짜에 공개할 때는 현재 부모의 `concept-review` 승인과 `concept-publish` 실행 회차가 필요하다. 외부 RUN에서 준비한 초안도 현재 worker의 RUN에서 검토·승인한다.

1. `concept-review`를 claim·bind한다. brief의 `quiz_run`을 위 절차의 `RUN`으로 사용한다. 메인이 화면 검토를 맡은 환경에서는 메인이 이 역할을 수행한다. 재시도 시 brief의 `retained_quiz`에는 이전 승인에서 원본 해시를 다시 확인해 가져온 문항 파일, 독립 풀이 문항 ID, 화면 기록이 표시된다. 누락되거나 수정된 부분을 검토하고, 미리보기 HTML은 현재 RUN에서 다시 빌드한다.
2. 작성자와 다른 독립 풀이자에게 매번 새 폴더에 만든 문제·SVG만 전달한다. `blind-record`에 `--packet "$BLIND" --author "$AUTHOR_ID" --solver "$SOLVER_ID"`를 함께 넘긴다. 이의를 해결한 문항은 `blind-make --only q…`로 새 패킷을 발급하고, 새 풀이자가 낸 답을 다음 회차로 기록한다.
3. `build`와 `browser` 후 `shots/`에서 네 화면의 문항, 힌트, 복기 창과 마지막 화면을 실제로 확인한다. `visual-review.json`에 `reviewer`와 `views`를 기록한다. 각 키는 `browser.json`의 모드 이름(예: `1280x900 light`)이다. 각 값에는 `status`, 실제로 관찰한 `observation`, 해당 모드의 파일명과 SHA-256을 담은 `screenshots`가 필요하다. 수정한 화면은 재검사한다.
4. `python3 "$C" evidence --run "$RUN"`으로 같은 입력에 대한 문항·독립 답·네 화면·사람의 판정을 확인하고 `concept-review` 영수증을 제출한다. 독립 답이나 화면 판정이 끝내 통과하지 못하면 `withheld` 영수증의 `unresolved`에 문항과 이유를 기록한다.
5. 부모의 `final-check`와 확인문제 검토가 함께 통과하면 `pack_cli.py run --run "$PARENT_RUN" --action concept-publish`를 실행한다. 발행기는 날짜 잠금 안에서 부모 발행 회차, 실제 공개 입력, 풀이와 화면 기록을 다시 대조한다. 부모 보고서의 `concept_check`에서 공개·대기·보류 사유를 확인한다. 부모 교체 시 발행 기록과 파일 해시로 소유권을 확인한 HTML과 근거 폴더는 부모 발행 저널의 `before/`에 보관된다. 수동 파일이 새 확인문제 경로와 겹치면 충돌 사유와 경로를 확인한다.
