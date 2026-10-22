# 문제설명 통합 계약

## 부모 복습팩에서 호출

공통 조립·검사는 통합 일곱 구역을 검증하고, 본문의 `data-answer-step`/`data-answer-final` 선택 요소에서 overlay를 추출한다. 새 원고에 구형 route를 요구하지 않는다. 표지 누락·검토 실패 시 설명/답안 발행을 withheld로 보고하며 검사 우회·숨긴 중복 핵심·구버전 승인을 사용하지 않는다. 과거 발행 자료의 구형 추출 검증은 새 저작 승인과 구분한다.

실행 순서는 명세 snapshot → 범위/manifest → 작성/조립 → 문제지만 빌드 → 부모 내용/화면/MD/개인화 감사 + 답안 링크 예비 검사 → 자식 → 승인 overlay 답안 빌드 → PDF 화면 검토 → 답안 발행 → 유예 없는 최종 검사다.

1. 부모의 기계 예비 검사·내용 리뷰(lite는 부모 내용 리뷰만 생략)·브라우저·MD 변환과 모든 topic ID의 개인화 감사를 끝낸다. `<REPO>/.claude/skills/ec2-review-pack/references/solution-style.md`의 실제 절대 경로와 manifest `learning_style` snapshot이 필수 입력이다.
2. 문제가 0개면 `skipped-no-problems`다. 자식·PDF 없이 현재 snapshot·모든 토픽 감사·유예 없는 최종 노트 검사를 수행한다.
3. manifest `problems`·`RUN/selection.json`·`.assets/problems.txt`의 ID·순서를 대조한다. 선택용 JSON은 자식 원문이나 독립 검산 근거를 대신하지 않는다.
4. **필수 하위 스킬: ec2-problem-explain.** 형제 `../ec2-problem-explain/SKILL.md`를 읽는다. 부모 `range`를 명시하고 `EXPLAIN_RUN=RUN/problem-explain/<새 실행ID>`를 없거나 빈 폴더로 정한다. 아래 변수는 명령 전에 같은 셸에서 실제 절대 경로로 설정한다.
```bash
python3 "$REPO/.claude/skills/ec2-problem-explain/scripts/epe_cli.py" extract --repo "$REPO" --target "$RANGE" --run "$EXPLAIN_RUN"
```
5. extract 뒤 정리노트 바이트·목록·참고 자료를 고정한다. 바뀌면 부모 검토를 다시 하고 새 EXPLAIN_RUN으로 시작한다. 자식은 understand → recall → start → solve(`이렇게 풀어요`) → verify → pitfall → retry의 통합 본문 → 독립 검산 → build/check → 네 검토와 전체 개인화 감사 → publish까지 수행한다. lite도 자식 모델·검토를 유지한다. 자식은 PDF를 직접 교체하지 않는다.
6. 자식의 `source_visual/content/independent/browser`와 `learning_style_audit`가 모두 실제 pass여야 한다. 성공은 `published`, 현재 snapshot/전체 감사까지 입증된 재사용만 `reused-verified`다. 실패/disputed는 `withheld`이며 아래 전체 팩 복구 계약을 따른다.
7. 부모 SKILL 9단계의 `--mode answers --answer-overlay`로 발행 자료의 `answer-overlay.json`을 소비해 **RUN 안**에 답안 PDF를 만든다. 같은 폴더 `validation.json`이 현재 검토를 승인해야 한다. 원본 MD 참고 풀이로 조용히 대체하지 않는다.
8. 아래 렌더 페이지 검토를 수행하고 부모 SKILL의 `publish_answer.py`를 실행한다. 이후 `check_html.py --repo "$REPO" --manifest "$RUN/manifest.json" --note <실제 노트 절대경로>`를 **유예 없이** 실행한다. extract 뒤 노트 링크를 자동 삽입하지 않는다.
9. 기본 팩·설명·답안·최종 검사와 복구/withheld 상태를 함께 보고한다. 자식/PDF/최종 검사 실패는 전체 완료가 아니다. 다른 팩은 계속할 수 있다.

## 답안 PDF 렌더 검토 기록

부모 SKILL 9단계 빌드의 종료 코드 0과 OVERFLOW 없음을 확인한다. `<range>`, `<slug>`는 실제 값으로 채우고 PDF를 실제 PNG 페이지로 렌더한다.
```bash
mkdir -p "$RUN/answer-pages"
pdftoppm -png -r 120 "$RUN/answers/복습문제_<range>_<slug>-답안.pdf" "$RUN/answer-pages/page"
```
각 PNG를 이미지 도구로 열어 모든 문항/소문항의 핵심 회로·판단·계산·최종 답을 검토한 통합 HTML 본문의 start/solve/verify와 대조한다. 답·단위·조건·근사·그림, 16:9 규격과 하단 180px/1080px 자막 여백, 잘림·겹침·누락을 검토해 `RUN/answer-review.md`에 페이지별 판정과 근거를 쓴다. 검토를 못 하면 보류다.

다음은 해시를 묶는 **미승인** 기록을 만든다. `PDF`, `OVERLAY`는 부모 SKILL에 나온 실제 절대 경로로 설정한다. PNG와 보고서가 실제로 있어야 한다.
```bash
python3 - "$RUN" "$PDF" "$OVERLAY" <<'EOF'
import hashlib, json, sys
from pathlib import Path
run, pdf, overlay = map(Path, sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
images = sorted((run / "answer-pages").glob("page-*.png"))
assert images and (run / "answer-review.md").is_file(), "실제 페이지와 검토 보고서 필요"
data = {"schema_version": 1, "status": "not_run", "reviewer": "", "overflow": [],
    "pdf_sha256": sha(pdf), "overlay_sha256": sha(overlay),
    "learning_style_sha256": json.loads(overlay.read_text(encoding="utf-8"))["learning_style"]["sha256"],
    "evidence": [{"path": p.relative_to(run).as_posix(), "sha256": sha(p)}
                 for p in [*images, run / "answer-review.md"]]}
(run / "answer-review.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
EOF
```
실제 화면 검토자가 `reviewer`와 `status`를 기록한다. 모든 페이지를 통과했을 때만 `pass`, 미실시 `not_run`, 결함 `fail`이다. `overflow=[]`는 실제 빌드/페이지 검토와 일치해야 하며 위 기록 생성은 화면 검토를 대신하지 않는다. PDF/overlay/명세/근거 바이트가 바뀌면 렌더·검토와 기록부터 다시 한다.

## 재생성 전에 기존 설명 다루기

이 절차는 수동 파일 작업 계약이다. 부모가 입력을 처음 변경하기 전(문제지 빌드 포함)에 한 번 수행하며 재조립마다 반복하지 않는다.

1. 팩의 최상위 `문제설명_<range>_*.html`, `.assets/문제설명_<range>_*.md`, `.assets/figures_문제설명_<range>_*`, `.assets/자료_문제설명_<range>_*`만 목록화한다. 정확한 range 접두사와 NFC 이름으로 비교한다. 다른 날짜·인터랙티브·정리노트·PDF·원본 문제는 포함하지 않는다.
2. 모든 대상과 백업의 절대 경로를 resolve해 의도한 팩과 전용 `RUN/previous-explanations-<고유ID>/` 안에 있는지 확인한다. 심볼릭 링크 등 팩 밖으로 나가는 대상은 중단한다.
3. 상대 경로대로 복사하고 원본·백업의 전체 파일 상대 경로 집합과 각 SHA-256이 같은지 확인한다. 빈 폴더도 보존한다. 목록·해시·백업 경로를 `RUN/explanations-backup.json`에 기록한다. 형식은 부모 `basic-pack-backup.json`과 같이 `{range, backup, roots, files, dirs}`다. roots·files·dirs는 팩 상대 경로, files의 값은 SHA-256, backup은 전용 백업 절대 경로다. 대상이 없으면 backup=null, roots=[], files={}, dirs=[]로 기록한다.
4. 검증 후에만 목록화한 설명 소유 파일·폴더를 팩에서 제거한다. 복사·검증 실패면 원본을 유지하고 부모 첫 조립을 중단한다. 제거 도중 실패하면 검증된 백업으로 설명을 복원하고 부모 조립을 중단한다.
5. 이 선제 정리 덕분에 문제 0개 전환·slug 변경·새 설명 보류 시에도 이전 설명이 최신 파일처럼 남지 않는다.
6. 자식/PDF/최종 검사를 포함해 재생성이 실패하면 **이번 실행 전 기본 팩(노트·MD·문제 목록·문제/답안 PDF·노트 그림)부터** 복원하고 그 입력과 대응되는 설명 소유 파일을 복원한다. 기본 팩과 설명 백업은 같은 첫 변경 전 상태여야 한다. 입력 대응을 확인하지 못하면 설명은 백업에 유지하고 전체 보류로 보고한다.
7. 이전 답안의 문제 ID·순서와 새 목록이 다르면 검증된 기본 팩 백업에 이전 답안을 보관하고 발행 위치에서 치운다. 같아도 이전 답안을 이번 승인 답안으로 보고하지 않는다. 새 팩이면 이번 실행이 만든 허용 파일만 RUN/withheld에 옮겨 발행 위치에 미완성 팩을 남기지 않는다. 다른 날짜나 이번 실행 전의 비소유 파일은 건드리지 않는다.

## 실패 시 전체 팩 복구

먼저 두 백업 기록의 range·전체 경로 집합·SHA-256과 실제 백업을 대조한다. 이번 실행에서 만든 같은 range의 허용 산출을 `RUN/withheld/<고유ID>/`에 상대 경로로 보관한 뒤 제거한다. 기본 팩 → 설명 순서로 복원하고 모든 파일 해시를 다시 확인한다. 새 팩은 두 기록이 빈 목록이므로 복원 없이 withheld로 끝난다.

다음 명령은 위 두 기록을 입력으로 삼는다. `REPO`, `RUN`, `RANGE`는 실제 값으로 채운다. 백업 기록과 prefix allowlist가 다른 파일, symlink, 팩 밖 경로, 해시 불일치는 변경 전에 중단한다. 이번 실행 중 외부에서 같은 팩을 편집했다면 이 명령을 실행하지 않고 대응을 확인한다.
```bash
python3 - "$REPO" "$RUN" "$RANGE" <<'EOF'
import hashlib, json, re, shutil, sys, tempfile, unicodedata as u
from pathlib import Path
repo, run = [Path(p).resolve() for p in sys.argv[1:3]]
r = sys.argv[3]
assert re.fullmatch(r"\d{4}(-\d{4})?", r)
pack = repo / "복습노트" / r
assert not pack.is_symlink() and not (pack / ".assets").is_symlink()
def allowed(rel):
    rel = u.normalize("NFC", rel)
    parts = Path(rel).parts
    if len(parts) == 1:
        return bool(re.fullmatch(rf"(?:정리노트|문제설명)_{r}_[^/]+\.html|복습문제_{r}_[^/]+-(?:문제|답안)\.pdf", rel))
    if len(parts) >= 2 and parts[0] == ".assets":
        name = parts[1]
        return (len(parts) == 2 and (name == "problems.txt" or bool(re.fullmatch(rf"(?:정리노트|문제설명)_{r}_.+\.md", name)))
            or name == f"figures_{r}" or name.startswith((f"figures_문제설명_{r}_", f"자료_문제설명_{r}_")))
    return False
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records = []
for record_name in ("basic-pack-backup.json", "explanations-backup.json"):
    record = json.loads((run / record_name).read_text(encoding="utf-8"))
    assert record["range"] == r
    roots, files, dirs = record["roots"], record["files"], record["dirs"]
    assert all(allowed(n) and not Path(n).is_absolute() and ".." not in Path(n).parts for n in [*roots, *files, *dirs])
    if record["backup"] is None:
        assert not roots and not files and not dirs
    else:
        backup = Path(record["backup"])
        assert not backup.is_symlink() and backup.resolve().is_relative_to(run)
        actual_files, actual_dirs = {}, []
        for rel in roots:
            target = backup / rel
            assert target.exists()
            for item in [target, *(target.rglob("*") if target.is_dir() else [])]:
                assert not item.is_symlink() and item.resolve().is_relative_to(backup.resolve())
                name = item.relative_to(backup).as_posix()
                if item.is_file(): actual_files[name] = sha(item)
                elif item.is_dir(): actual_dirs.append(name)
        assert actual_files == files and sorted(actual_dirs) == sorted(dirs), "백업 경로/해시 불일치"
    records.append(record)
current = []
for base in (pack, pack / ".assets"):
    for target in (base.iterdir() if base.is_dir() else []):
        if allowed(target.relative_to(pack).as_posix()):
            for item in [target, *(target.rglob("*") if target.is_dir() else [])]:
                assert not item.is_symlink() and item.resolve().is_relative_to(pack.resolve())
            current.append(target)
withheld = Path(tempfile.mkdtemp(prefix="withheld-", dir=run))
# Copy and verify every new file before removing any published path.
for target in current:
    dest = withheld / target.relative_to(pack)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(target, dest) if target.is_dir() else shutil.copy2(target, dest)
    for item in (target.rglob("*") if target.is_dir() else [target]):
        if item.is_file(): assert sha(item) == sha(withheld / item.relative_to(pack))
for target in current:
    shutil.rmtree(target) if target.is_dir() else target.unlink()
for record in records:  # basic pack first, then its corresponding explanations
    if record["backup"] is None: continue
    for rel in record["roots"]:
        source, dest = Path(record["backup"]) / rel, pack / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, dest) if source.is_dir() else shutil.copy2(source, dest)
    assert all(sha(pack / rel) == digest for rel, digest in record["files"].items())
print("복구/withheld:", withheld)
EOF
```
복사·제거 뒤 I/O 오류가 나면 RUN의 검증된 백업을 유지하고 같은 allowlist로 복원을 마친다. 중간 상태는 성공으로 보고하지 않는다.

## 기존 팩 보충

- 실제 날짜 폴더별 `problems.txt`를 조사한다. 없거나 문항이 0개인 팩은 `skipped-no-problems`다.
- 부모 전체를 재생성하지 않고 설명 스킬만 실행한다. 정리노트 HTML·MD, 문제/답안 PDF, 목록, 원본 문제 md·그림을 그대로 보존한다.
- 입력을 바꾸지 않으므로 기존 설명을 선제 제거하지 않는다. 정상 교체는 publish의 백업·복구를 사용한다.
- 기존 설명은 검토 기록·현재 입력·참조·산출 해시·원래 저작 조각·문항/소문항 대응이 모두 입증되는 경우에만 `reused-verified`다. 원래 RUN이나 조각이 없어 input_hash를 재현하지 못하면 추측하지 말고 재생성한다.
- 재사용 검증 실패 시 기존 설명을 위 절차대로 백업·검증해 발행 경로에서 치운 뒤 재생성한다. 한 팩 실패는 그 팩만 보류하고 나머지 팩과 원본은 유지한다.
