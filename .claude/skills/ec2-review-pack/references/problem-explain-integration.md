# 문제설명 통합 계약

## 부모 복습팩에서 호출

공통 조립·검사는 통합 일곱 구역을 검증하고, 본문의 `data-answer-step`/`data-answer-final` 선택 요소에서 overlay를 추출한다. 새 원고에 구형 route를 요구하지 않는다. 표지 누락·검토 실패 시 설명/답안 발행을 withheld로 보고하며 검사 우회·숨긴 중복 핵심·구버전 승인을 사용하지 않는다. 과거 발행 자료의 구형 추출 검증은 새 저작 승인과 구분한다.

실행 순서는 명세 snapshot → 범위/manifest → 작성/조립 → 문제지만 빌드 → 부모 내용/화면/MD/개인화 감사 + 답안 링크 예비 검사 + 변환 SVG 독립 화면 검토 → 자식 코디네이터의 발행 준비 → 부모의 설명 발행 → 승인 overlay 답안 빌드 → PDF 화면 검토 → 부모의 답안 발행 → 유예 없는 최종 검사다.

1. 부모의 기계 예비 검사·내용 리뷰(lite는 부모 내용 리뷰만 생략)·브라우저·MD 변환과 모든 topic ID의 개인화 감사를 끝낸다. `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md`의 실제 절대 경로와 manifest `learning_style` snapshot이 필수 입력이다.
2. 문제가 0개면 `skipped-no-problems`다. 자식·PDF 없이 현재 snapshot·모든 토픽 감사·유예 없는 최종 노트 검사를 수행한다.
3. manifest `problems`·`RUN/selection.json`·`.assets/selection.json`·`.assets/problems.txt`의 ID·순서를 대조한다. 새 정책의 핵심/추가·학습 목표·소문항 묶음 수·추정 시간도 같은 입력에서 읽고 source 해시에 묶는다. 해설 HTML·동반 MD에는 핵심/추가·소문항 묶음·예상 시간의 학습량 행을 출력하지 않으며 선발 JSON은 유지한다. PDF 표시는 기존 PDF 정책을 따른다. 선택용 JSON은 자식 원문이나 독립 검산 근거를 대신하지 않는다.
4. **필수 하위 스킬: ec2-problem-explain.** 이 부모 통합 호출에서는 자식 코디네이터 한 명에게 형제 `../ec2-problem-explain/SKILL.md`와 필요한 참조를 직접 읽고 아래 발행 준비 절차를 맡긴다. 부모는 자식 원고·풀이·화면을 자기 문맥에 다시 모으지 않고 이 계약과 반환 영수증을 사용한다. 부모 `range`를 명시하고 runner가 브리프에 지정한 새 `EXPLAIN_RUN`을 사용한다. 코디네이터에게 `REPO`, 부모 `RUN`, `EXPLAIN_RUN`, 자식 `SKILL`, `PROFILE`의 실제 절대 경로, 부모 manifest·learning_style snapshot·선발 기록·검증된 두 백업 기록의 경로와 SHA-256을 넘긴다. 아래 변수는 명령 전에 같은 셸에서 실제 절대 경로로 설정한다.
```bash
python3 "$REPO/.claude/skills/ec2-problem-explain/scripts/epe_cli.py" extract --repo "$REPO" --target "$RANGE" --run "$EXPLAIN_RUN"
```
5. 코디네이터가 extract를 실행한다. extract 뒤 정리노트 바이트·목록·참고 자료를 고정한다. 바뀌면 부모 검토를 다시 하고 새 EXPLAIN_RUN으로 시작한다. 자식은 understand → recall → start → solve(`이렇게 풀어요`) → verify → pitfall → retry의 통합 본문 → 독립 검산 → build/check → 네 검토와 전체 개인화 감사까지 수행한다. 마지막 build 뒤의 check·검토 기록이 승인한 산출만 `ready-for-publish`로 반환하며 코디네이터는 publish를 실행하지 않는다. lite도 자식 모델·검토를 유지한다. 아래 위임 경계를 적용한다.
6. 부모가 영수증의 현재 경로·입력/명세/참조/산출/검토 해시와 모든 판정을 확인한 뒤 runner의 `run --action publish-explanation`을 실행한다. 기존 CLI의 전체 발행 게이트를 그대로 통과해야 하며 영수증으로 검사를 대체하거나 발행 권한 우회 옵션을 만들지 않는다. 자식의 `source_visual/content/independent/browser`와 `learning_style_audit`가 모두 실제 pass여야 한다. `publish: … backup: …` 출력과 종료 코드를 부모 실행 기록에 남긴 뒤에만 `published`로 기록한다. 현재 snapshot/전체 감사와 재사용 근거까지 입증된 재사용만 `reused-verified`다. 실패/disputed는 `withheld`이며 아래 전체 팩 복구 계약을 따른다.
7. runner의 `run --action build-answers`로 발행 자료의 `answer-overlay.json`을 소비해 **RUN 안**에 답안 PDF를 만든다. 같은 폴더 `validation.json`이 현재 검토를 승인해야 한다. 원본 MD 참고 풀이로 조용히 대체하지 않는다.
8. 아래 렌더 페이지 검토를 수행하고 runner의 `run --action publish-answer`를 실행한다. 이후 `run --action final-check`로 기존 검사를 **유예 없이** 실행한다. extract 뒤 노트 링크를 자동 삽입하지 않는다.
9. 기본 팩·설명·답안·최종 검사와 복구/withheld 상태를 함께 보고한다. 자식/PDF/최종 검사 실패는 전체 완료가 아니다. 다른 팩은 계속할 수 있다.

## 자식 코디네이터의 위임 경계와 영수증

- **쓰기 경계:** 저장소 발행·기본 팩/설명 선제 정리·제목 맵 갱신·백업 후 제거·복구는 최상위 부모만 수행한다. 코디네이터와 작업자는 할당된 `EXPLAIN_RUN` 안에만 쓰고, 부모가 별도로 지정한 PDF 검토는 해당 부모 `RUN` 안에만 쓴다. `RUN/repo` 같은 링크를 통해 저장소에 쓰지 않는다. 문제 md·그림·정리노트·목록·PDF 등 보호 입력을 고치지 않는다. 자식 스킬의 publish 단계는 이 통합 호출에 한해 부모 실행 요청으로 바꾸며 단독 호출 계약은 바꾸지 않는다.
- **화면 검토 역할:** 이 통합 호출에서 코디네이터는 자식 스킬의 `메인 에이전트` 역할로 stage의 read-only 브라우저 검토와 검토 기록을 담당한다. `references/verification.md`의 모든 크기·테마·원문/문제 탭·링크·클릭·visibility·오류/넘침 기준을 실제 수행하고 증거를 RUN에 남긴다. 부모의 발행 권한과는 별개다. 브라우저 세션·서버·포트는 코디네이터가 소유하고, 다른 작업자의 탭이나 서버를 조작하지 않으며 종료/재개 시 소유권과 정리 상태를 기록한다. 부모가 같은 스크린샷을 모두 다시 읽는 대신 증거 경로·해시·범위·판정을 확인한다.
- **전체 슬롯 최대 4:** 최상위 부모 1 + 자식 코디네이터 1 + leaf 작업자 최대 2로 제한한다. 부모의 이전 작성/검토 작업을 먼저 끝내고, 문항별 작성·독립 검산은 두 자리 안에서 제한된 묶음으로 수행한다. 완료 작업자는 종료해 자리를 반환한 뒤 다음 묶음을 시작한다. 코디네이터 아래에 다른 코디네이터를 만들지 않고 leaf는 재위임하지 않는다. 해당 문항 작성자는 독립 검산자가 될 수 없고, 팩 내용 리뷰어는 그 팩의 어떤 문항도 작성하지 않은 별도 에이전트여야 한다. 독립 검산자에게는 정답·참고 풀이·설명 조각을 제외한 원문/그림/필요 이론만 넘겨 먼저 풀이를 저장하게 한 뒤 코디네이터가 참고 답과 대조한다. 정답 필드가 있는 전체 source.json을 blind 검산 입력으로 넘기지 않는다.
- **중첩 실행 불가 시:** 코디네이터는 역할·읽을 경로·허용 출력 경로·문항/소문항·모델·금지할 정답 입력이 적힌 leaf 브리프와 진행 상태를 EXPLAIN_RUN에 저장해 부모에게 요청한다. 자리가 없으면 코디네이터가 상태를 저장하고 종료한 뒤 부모가 그 브리프로 leaf를 실행한다. leaf가 끝나 자리가 반환되면 코디네이터를 재개하거나 저장 상태를 읽는 후임 한 명으로 교체한다. 기다리는 코디네이터를 계속 중첩 생성하거나, 슬롯 부족을 이유로 작성자에게 자기 검산/내용 리뷰를 맡기지 않는다. 필요한 독립 역할을 확보하지 못하면 `withheld`다.
- **동결·재검토:** 코디네이터는 위임 시작과 반환 시 부모 manifest·snapshot·선발/목록·정리노트·원본/그림·실제 읽은 참조 해시를 확인하고 부모는 발행 직전에 다시 확인한다. 입력 변경은 새 EXPLAIN_RUN과 부모 재검토 대상이다. 조각·evidence·산출 변경은 build부터 다시 하며 build가 초기화한 review.json에 과거 pass를 복사하지 않는다. 마지막 build 뒤 실제 네 검토와 모든 소문항·규칙의 개인화 감사를 기록한다.

child-receipt의 `bucket`은 bucket 폴더 이름(전체 경로가 아님)이고 `stage`는 현재 승인 HTML의 부모 폴더 절대 경로다. review.json `references`에는 부모 MD가 참조하는 SVG를 빠짐없이 넣는다. 빠지면 references incomplete로 거부된다. 반환 전 `task check`로 receipt를 검증한다.

코디네이터는 `EXPLAIN_RUN/child-receipt.json`에 `{schema_version: 1, status: ready-for-publish|withheld, range, slug, run, bucket, stage, files, input_hash, review_policy_version, counts, reviews, reviewers, unresolved}`를 저장한다. `files`에는 부모 manifest·learning_style snapshot·자식 source.json·stage.json·stage manifest·machine.json·review.json·answer-overlay.json과 실제 원본/참조/산출/evidence를 각각 `{path: 실제 절대 경로, sha256: 현재 바이트 해시}`로 기록한다. `ready-for-publish`는 source의 전체 입력 집합·build의 artifact_hashes·검토의 references와 대응되게 하며 항목을 생략하지 않는다. `withheld`는 확보한 파일만 기록하고 없는 필드/파일과 원인을 unresolved에 밝힌다. `counts`는 문항/소문항 수, `reviews`는 네 검토와 전체 learning_style_audit의 판정·증거 경로, `reviewers`는 실제 역할/문항별 작성자·검산자·내용/화면 검토자의 식별자를 보존한다. 해시나 게이트 값을 임의 갱신하지 않는다. 모든 leaf 브리프에 최종 반환 800자 이하(개행 포함 Python len)·상세 파일 인계 요청을 전파한다. 조정자도 800자 이하로 반환한다. 반환 메시지는 상태·range·문항/소문항 수·영수증 절대 경로와 SHA-256·부모 다음 실행·unresolved 요지만 담는다. 실패는 같은 영수증에 이유와 현재 stage/백업 경로를 남기며 `ready-for-publish`를 발행 완료로 보고하지 않는다. 부모가 설명을 발행한 뒤 실행한 CLI 결과와 백업 경로를 별도 실행 영수증에 남겨 이 영수증과 연결한다.

## 답안 PDF 렌더 검토 기록

runner의 build-answers 종료 코드 0과 OVERFLOW 없음을 확인한다. `REPORT`는 `RUN/answer-review.md`이며 PDF/OVERLAY/REPORT는 현재 PDF QA 브리프의 pdf/overlay/report 실제 절대 경로를 사용하고 PDF를 실제 PNG 페이지로 렌더한다.
```bash
mkdir -p "$RUN/answer-pages"
pdftoppm -png -r 120 "$PDF" "$RUN/answer-pages/page"
```
각 PNG를 이미지 도구로 열어 모든 문항/소문항의 핵심 회로·판단·계산·최종 답을 검토한 통합 HTML 본문의 start/solve/verify와 대조한다. 답·단위·조건·근사·그림, 16:9 규격과 하단 180px/1080px 자막 여백, 잘림·겹침·누락을 검토해 브리프의 `report` 경로에 페이지별 판정과 근거를 쓴다. 검토를 못 하면 보류다.

이 실제 PDF 화면 검토는 별도 검토자에게 위임할 수 있다. 부모가 PDF·승인 overlay·명세·검토한 HTML의 경로/해시와 전체 페이지 목록을 넘기고, 검토자는 부모가 지정한 `RUN/answer-pages/`의 모든 PNG를 실제 열어 대조한 뒤 브리프의 `report` 경로와 `RUN/answer-review.json`만 기록한다. 렌더가 필요하면 위 명령의 RUN 내 렌더 경로만 쓴다. 반환은 PDF/overlay/명세/PNG/보고서 해시·검토자·전체 페이지 판정·unresolved 요지만 담으며 부모가 같은 페이지를 전부 다시 여는 것을 요구하지 않는다. 자동 해시 기록 생성만으로 pass를 부여하지 않고 아래 미승인 기록을 실제 검토자가 완료한다. 부모는 현재 바이트와 전체 페이지 증거·pass를 확인한 뒤에만 runner의 `run --action publish-answer`를 실행하고, 실패 시 아래 전체 팩 복구를 수행한다.

다음은 해시를 묶는 **미승인** 기록을 만든다. `PDF`, `OVERLAY`, `REPORT`는 위 현재 브리프의 실제 절대 경로로 설정한다. PNG와 보고서가 실제로 있어야 한다.
```bash
python3 - "$RUN" "$PDF" "$OVERLAY" "$REPORT" <<'EOF'
import hashlib, json, sys
from pathlib import Path
run, pdf, overlay, report = map(Path, sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
images = sorted((run / "answer-pages").glob("page-*.png"))
assert images and report.is_file(), "실제 페이지와 검토 보고서 필요"
data = {"schema_version": 1, "status": "not_run", "reviewer": "", "overflow": [],
    "pdf_sha256": sha(pdf), "overlay_sha256": sha(overlay),
    "learning_style_sha256": json.loads(overlay.read_text(encoding="utf-8"))["learning_style"]["sha256"],
    "evidence": [{"path": p.relative_to(run).as_posix(), "sha256": sha(p)}
                 for p in [*images, report]]}
(run / "answer-review.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
EOF
```
실제 화면 검토자가 `reviewer`와 `status`를 기록한다. 모든 페이지를 통과했을 때만 `pass`, 미실시 `not_run`, 결함 `fail`이다. `overflow=[]`는 실제 빌드/페이지 검토와 일치해야 하며 위 기록 생성은 화면 검토를 대신하지 않는다. PDF/overlay/명세/근거 바이트가 바뀌면 렌더·검토와 기록부터 다시 한다.

## 재생성 전에 기존 설명 다루기

`pack_files.prepare_pack`이 기본 팩과 설명에 함께 적용하는 파일 작업 계약이다. 부모가 입력을 처음 변경하기 전(문제지 빌드 포함)에 한 번 수행하며 재조립마다 반복하지 않는다.

1. 팩의 최상위 `문제설명_<range>_*.html`, `.assets/문제설명_<range>_*.md`, `.assets/figures_문제설명_<range>_*`, `.assets/자료_문제설명_<range>_*`만 목록화한다. 정확한 range 접두사와 NFC 이름으로 비교한다. 다른 날짜·인터랙티브·정리노트·PDF·원본 문제는 포함하지 않는다.
2. 모든 대상과 백업의 절대 경로를 resolve해 의도한 팩과 전용 `RUN/previous-explanations-<고유ID>/` 안에 있는지 확인한다. 심볼릭 링크 등 팩 밖으로 나가는 대상은 중단한다.
3. 상대 경로대로 복사하고 원본·백업의 전체 파일 상대 경로 집합과 각 SHA-256이 같은지 확인한다. 빈 폴더도 보존한다. 목록·해시·백업 경로를 `RUN/explanations-backup.json`에 기록한다. 형식은 부모 `basic-pack-backup.json`과 같이 `{range, backup, roots, files, dirs}`다. roots·files·dirs는 팩 상대 경로, files의 값은 SHA-256, backup은 전용 백업 절대 경로다. 대상이 없으면 backup=null, roots=[], files={}, dirs=[]로 기록한다.
4. 검증 후에만 목록화한 설명 소유 파일·폴더를 팩에서 제거한다. 복사·검증 실패면 원본을 유지하고 부모 첫 조립을 중단한다. 제거 도중 실패하면 검증된 백업으로 설명을 복원하고 부모 조립을 중단한다.
5. 이 선제 정리 덕분에 문제 0개 전환·slug 변경·새 설명 보류 시에도 이전 설명이 최신 파일처럼 남지 않는다.
6. 자식/PDF/최종 검사를 포함해 재생성이 실패하면 **이번 실행 전 기본 팩(노트·MD·문제 목록·표시 제목 맵·문제/답안 PDF·노트 그림)부터** 복원하고 그 입력과 대응되는 설명 소유 파일을 복원한다. 기본 팩과 설명 백업은 같은 첫 변경 전 상태여야 한다. 입력 대응을 확인하지 못하면 설명은 백업에 유지하고 전체 보류로 보고한다.
7. 이전 답안의 문제 ID·순서와 새 목록이 다르면 검증된 기본 팩 백업에 이전 답안을 보관하고 발행 위치에서 치운다. 같아도 이전 답안을 이번 승인 답안으로 보고하지 않는다. 새 팩이면 이번 실행이 만든 허용 파일만 RUN/withheld에 옮겨 발행 위치에 미완성 팩을 남기지 않는다. 다른 날짜나 이번 실행 전의 비소유 파일은 건드리지 않는다.

## 실패 시 전체 팩 복구

표시 제목 맵 `.assets/display-titles.json`과 새 선발 기록 `.assets/selection.json`도 기본 팩 입력이다. 두 파일을 같은 백업·복원·실패 시 withheld 절차에 포함한다. `.pack/selection-review.json`도 실행 전 백업하고 실패 시 이전 기록으로 복원한다. 기존 맵은 문제 목록과 함께 백업·복원하고, 실행 전 없던 새 맵은 실패 시 withheld로 보관한 뒤 발행 위치에서 제거한다. 제목 맵을 먼저 변경하지 않는다.

먼저 두 백업 기록의 range·전체 경로 집합·SHA-256과 실제 백업을 대조한다. 이번 실행에서 만든 같은 range의 허용 산출을 `RUN/withheld/<고유ID>/`에 상대 경로로 보관한 뒤 제거한다. 기본 팩 → 설명 순서로 복원하고 모든 파일 해시를 다시 확인한다. 새 팩은 두 기록이 빈 목록이므로 복원 없이 withheld로 끝난다.

다음 명령은 위 두 기록을 입력으로 삼는다. `REPO`, `RUN`, `RANGE`는 실제 값으로 채운다. 백업 기록과 prefix allowlist가 다른 파일, symlink, 팩 밖 경로, 해시 불일치는 변경 전에 중단한다. 이번 실행 중 외부에서 같은 팩을 편집했다면 이 명령을 실행하지 않고 대응을 확인한다.
최상위 부모가 [runner 복구 명령](runner-contract.md)의 `recover --run <RUN>`을 실행한다. 복구 직전에 inventory를 새로 캡처해 외부 편집 검사를 우회하지 않는다.
복사·제거 뒤 I/O 오류가 나면 RUN의 검증된 백업을 유지하고 같은 allowlist로 복원을 마친다. 중간 상태는 성공으로 보고하지 않는다.

## 기존 팩 보충

- 실제 날짜 폴더별 `problems.txt`를 조사한다. 없거나 문항이 0개인 팩은 `skipped-no-problems`다.
- 부모 전체를 재생성하지 않고 설명 스킬만 실행한다. 정리노트 HTML·MD, 문제/답안 PDF, 목록, 원본 문제 md·그림을 그대로 보존한다.
- 입력을 바꾸지 않으므로 기존 설명을 선제 제거하지 않는다. 정상 교체는 publish의 백업·복구를 사용한다.
- 기존 설명은 검토 기록·현재 입력·참조·산출 해시·원래 저작 조각·문항/소문항 대응이 모두 입증되는 경우에만 `reused-verified`다. 원래 RUN이나 조각이 없어 input_hash를 재현하지 못하면 추측하지 말고 재생성한다.
- 재사용 검증 실패 시 기존 설명을 위 절차대로 백업·검증해 발행 경로에서 치운 뒤 재생성한다. 한 팩 실패는 그 팩만 보류하고 나머지 팩과 원본은 유지한다.

부모 통합 실행은 [runner 계약](runner-contract.md)을 따른다. EXPLAIN_RUN은 runner 상태/브리프의 새 경로를 사용하고 최상위 부모만 `run --action publish-explanation`, `build-answers`, `publish-answer`, `final-check`, `recover`를 실행한다. 위 자식 extract/실제 PDF 검토 명령은 담당 작업의 의미를 설명하며 부모의 이중 실행 경로로 사용하지 않는다.

자식 실행의 phase 8 선행조건은 convert-md 성공과, SVG가 있는 경우 standalone-svg-qa의 현재 receipt다. 모든 변환 SVG의 실제 독립 화면·폰트 검토를 끝내기 전에는 EXPLAIN_RUN을 할당하거나 extract하지 않는다. 실제 성공 변환에서 SVG가 0개인 경우만 이 역할을 생략한다. 변환 MD/SVG가 바뀌면 부모 검토와 자식 근거도 stale이며 기존 새 EXPLAIN_RUN 규칙을 따른다.
