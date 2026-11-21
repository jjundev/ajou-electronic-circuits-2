# 문항별 회로 실험

새로 만드는 복습팩은 해설 조정자가 후보를 자동으로 검토한다. 기존 팩에는 사용자가 지정한 문항과 승인된 실험의 레이아웃 재발행을 적용한다. 조작과 관찰이 풀이의 판단 한 가지를 해결하는 경우에만 선정한다.

1. 문항 원문·그림과 채택한 해설·독립 풀이를 읽는다. 원문 모델에서 유효한 결선이나 조건 조작, 학생이 볼 전류·전압·파형·부하 변화, 해설에서 이어 쓸 식을 각각 제시할 수 있을 때 후보를 낸다. 정적 그림으로 충분하거나 계산이 길기만 한 문항은 후보에서 제외한다. 원문 가정을 깨는 상황은 조작의 의미를 분명히 표시할 수 있을 때만 실험에 넣는다.
2. 후보를 `BUCKET/lab-candidates.json` 배열로 작성한다. 각 항목에는 `workbook_id`, `subpart`(소문항이 없는 경우 `main`), `section`(`start`, `solve`, `retry` 중 하나), `decision`(학생이 읽을 예측 질문), `action`, `observation`, `return_to`, `label`을 넣는다. 모든 후보가 부적합하면 빈 배열을 쓴다.
3. `python3 "$SKILL/scripts/epe_cli.py" select-lab --run "$RUN"`을 실행한다. 팩별로 최대 한 후보를 `BUCKET/lab/brief.json`에 고정한다. 첫 식에 필요한 판단을 우선하고 같은 구역에서는 문제 목록 순서를 따른다. 후보가 있으면 [ec2-interactive](../../../../.agents/skills/ec2-interactive/SKILL.md)의 문항 모드를 현재 브리프와 근거로 실행한다. 같은 원문 회로·가정·조작을 이미 다룬 실험은 새 브리프에 대해 다시 확인해 재사용할 수 있다.
4. `lab.js`, `index.html`, `lab-validation.json`을 브리프와 같은 폴더에 둔다. 검증 JSON의 `gates`는 `machine`, `numeric_independent`, `probe`, `browser`를 모두 요구한다. `source_sha256`은 `lab.js`, `html_sha256`은 `index.html`, `brief_sha256`은 `brief.json`의 실제 바이트에 대응한다. 검증 실패나 결과 누락은 최종 보고의 실험 보류에 기록한다.
5. 기본 해설과 같은 명령으로 마지막 build·check를 수행한다. 승인된 실험은 `.assets/자료_문제설명_<range>_<slug>/labs/<workbook_id>/`에 들어간다. 해설 HTML과 동반 MD의 해당 문항에서 링크를 확인하고, 새 탭에서 결선을 조작한 다음 원래 풀이 단계로 돌아온다. 브라우저 폭과 테마는 두 스킬의 기존 기준을 따른다. 발행 영수증의 산출물 목록에 실험 네 파일을 포함한다.
