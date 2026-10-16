---
name: ec2-review-pack
description: 전자회로2 수업의 STT·강의노트·Razavi 교과서로 ELI5 정리노트 HTML(+MD, 그림)을 만들고, 그 수업 범위에 맞는 workbook 문제 약 10개를 골라 복습문제 PDF(문제+답안)를 만들어 검토를 통과한 문제설명 HTML·MD와 함께 복습노트의 날짜별 폴더에 저장한다. "정리노트", "복습문제", "복습팩", "0923 정리해줘"처럼 전자회로2 수업 정리를 요청하거나 /ec2-review-pack [MMDD|MMDD-MMDD] [lite]로 부를 때 사용한다.
---

# 전자회로2 복습팩

수업 녹음 전사(STT)와 강의자료, Razavi 교과서로 한 기간의 정리노트를 만들고, workbook에서 그 범위 문제를 골라 복습문제 PDF와 검토를 통과한 문제설명 HTML·MD를 만든다. 중간에 사용자에게 묻지 않고 끝에 한 번 보고한다. 커밋은 제안만 한다.

**산출물** (`복습노트/<range>/`):
- 맨 위: `정리노트_<range>_<slug>.html`, 그리고 문제가 1개 이상이면 `복습문제_<range>_<slug>-문제.pdf`, `복습문제_<range>_<slug>-답안.pdf`, `문제설명_<range>_<slug>.html`
- `.assets/`: 같은 이름의 `.md`, `figures_<range>/`, 그리고 문제가 1개 이상이면 `problems.txt`, `문제설명_<range>_<slug>.md`, `figures_문제설명_<range>_<slug>/`, `자료_문제설명_<range>_<slug>/`

**폴더 규칙**: 날짜 폴더 맨 위에는 `.pack/`, `*.html`, `*.pdf`, `.assets/`만 둔다. md·그림·목록·데이터 등 나머지는 모두 `.assets/`에 둔다(`tests/test_pack_layout.py`가 실제 `복습노트/`를 검사한다).

**PDF 규격**: 문제지·답안지는 16:9 페이지를 사용한다. 1920×1080 기준 하단 180px는 자막 전용 여백으로 비우고, 본문 기본값은 약 11.34pt이며 제목·수식·힌트도 같은 약 1.134배로 조정해 기존 A4 영상 전체 화면에서 보이던 텍스트 크기를 유지한다. 긴 문항의 기존 축소 배율도 보존한다.

**인자**: `[MMDD | MMDD-MMDD] [lite]`
- `lite`: 작성자·요약 에이전트를 sonnet으로, 6단계 리뷰를 생략한다. 부모 정리노트의 기계 검사와 브라우저 검사는 그대로 한다. 자식 문제설명의 작성자 모델·독립 검산·네 검토는 lite에서도 낮추거나 생략하지 않는다.

**모델 이름**: 이 문서의 opus·sonnet은 Claude 기준이다. Claude가 아닌 환경(GPT)에서는 opus 대신 sol, sonnet 대신 luna를 쓴다.

**진행 표시**: 단계마다 한 줄만 쓴다. 예: `3/10 작성 중: 섹션 5개 (병렬)`

**경로 약속**
- `SKILL` = 이 파일이 있는 폴더(`.claude/skills/ec2-review-pack`)의 절대 경로
- `REPO` = 저장소 루트
- `RUN` = `<scratchpad>/review-pack/<range>/`
- 셸 상태는 Bash 호출 사이에 이어지지 않는다. 아래 명령의 `$SKILL`, `$RUN`, `$REPO`는 실행할 때마다 실제 절대 경로로 바꿔 쓰거나, 같은 명령 앞에 `SKILL=… RUN=… REPO=…`를 붙여 설정한다. `cd`는 쓰지 않고 파일도 절대 경로로 넘긴다.

## 절차

### 0. 준비
1. `REPO`에 `STT/`, `강의노트/`, `교과서/마이크로전자회로/`, `workbook/build_workbook.py`가 모두 있는지 확인한다. 하나라도 없으면 "전자회로2 저장소에서만 동작해요"라고 알리고 멈춘다.
2. STT 목록은 NFC로 읽는다. macOS에는 NFD 파일명이 섞여 있다.
   ```bash
   python3 -c "import os,unicodedata as u,re;n=[u.normalize('NFC',f) for f in os.listdir('$REPO/STT')];print(sorted(m.group(1) for f in n if f.endswith('전회2.md') and (m:=re.match(r'(\d{4})',f))))"
   ```
3. 기간을 정한다.
   - 인자가 있으면 그 기간을 쓴다.
   - 인자가 없으면 `복습노트/*/정리노트_<range>_*.html` 중 가장 늦은 끝 날짜를 찾는다(NFD 폴더·파일명도 잡히게 NFC로 비교).
     ```bash
     python3 -c "import os,re,unicodedata as u
     packs=[]
     for d in os.listdir('$REPO/복습노트'):
         for f in os.listdir(os.path.join('$REPO/복습노트', d)):
             if m:=re.match(r'정리노트_(\d{4}(?:-(\d{4}))?)_', u.normalize('NFC', f)):
                 packs.append(m.group(2) or m.group(1))
     print(max(packs) if packs else '없음')"
     ```
     그 뒤의 STT를 모두 쓴다. 팩이 하나도 없으면 사용 가능한 STT 날짜를 보여 주고 "기간을 인자로 넣어 주면 돼요(예: /ec2-review-pack 0923)"라고 알린 뒤 멈춘다.
   - 해당 STT가 하나도 없으면 사용 가능한 날짜를 보여 주고 멈춘다.
   - `range`는 첫 STT 날짜 하나이거나 `첫-끝` 형식이다.
4. 실행 폴더를 만든다. 서브에이전트에게는 `RUN`, `RUN/repo`, `SKILL` 경로만 넘긴다.
   ```bash
   mkdir -p "$RUN"/{summaries,sections,work} && ln -sfn "$REPO" "$RUN/repo"
   ```
   에이전트는 `RUN` 밖에 쓰지 않는다. 임시·보조 파일은 `RUN/work/`에만 둔다. 저장소(`STT/`, `강의노트/`, `교과서/`, `workbook/`, `from_the_past/`)에는 아무도 쓰지 않고, `복습노트/`에는 메인 에이전트만 쓴다.

### 1. 범위 파악
1. **먼저** 관련 `강의노트/2026F_Lec*_*.pdf` 텍스트를 슬라이드 번호와 함께 `RUN/slides.txt`에 추출한다(PyMuPDF, 쪽마다 `=== LNN sK ===`, `LNN`은 파일명의 `LecN`을 두 자리로). 요약 에이전트는 이 파일이 있다고 보고 시작하므로 추출이 끝난 뒤에 띄운다.
   - 관련 PDF: **이번 range의 STT가 실제로 다루는** 슬라이드가 들어 있는 Lec PDF만. 이전 날짜가 이미 다룬 슬라이드는 이전 팩이 있든 없든 이번 range 밖이므로 "안 다룸"이 아니라 그냥 넣지 않는다. 확실하지 않으면 넉넉히 넣는다. 새 강의자료가 방금 올라왔으면(`강의노트/`에 새 Lec PDF) 그것도 관련 PDF 후보에 넣는다 — 수업은 슬라이드 업로드보다 먼저 진행되기도 한다.
   - 추출에 실패하면 STT만으로 진행하고 보고서에 적는다(브리프의 `slides.txt` 줄은 "없음"으로 바꿔 넘긴다).
   - **슬라이드가 없는 날짜**: 이번 range의 날짜 중 그 날 강의 내용을 다루는 Lec PDF가 하나도 없으면(예: 교수님이 업로드된 슬라이드보다 더 나간 경우), 그 날짜를 표시해 둔다. 다음 항목의 브리프에서 쓴다.
2. 그다음 STT 날짜마다 요약 에이전트 1명을 **병렬로** 띄운다. 브리프는 `references/stt-summary-prompt.md`에 있다.
   - `<2026F_LecN_*.pdf>`: 그 날짜가 다룬 슬라이드가 들어 있는 PDF. 확실하지 않으면 1의 관련 PDF를 모두 적는다. **1에서 "슬라이드 없음"으로 표시한 날짜**는 이 자리에 "없음(이 날짜 슬라이드 미게시)"이라고 적는다 — 요약 에이전트는 STT와 교과서만으로 진행하고, `## 슬라이드 대조표` 대신 `## 교과서 절 대조`만 쓴다(`references/stt-summary-prompt.md`).
   - `<YYYY-MM-DD>`: 연도는 이번 학기 연도(오늘 날짜 기준), 월·일은 `<MMDD>`.
3. **요약이 모두 끝난 뒤** 메인 에이전트는 후보 문제 목록을 만든다(`references/problem-selection.md` 1).
   ```bash
   python3 "$SKILL/scripts/problem_index.py" --repo "$REPO" --used "$REPO/복습노트" --exclude-range <range> --chapters <장> > "$RUN/candidates.tsv"
   ```
   장은 각 요약의 `## 교과서 절 대조`에서 "다룸"·"일부"로 적힌 절 번호마다 **첫 번째 숫자**(예: `9.1.2` → `9`)를 모아 만든 집합이다(슬라이드 제목이 아니다). 어떤 요약에도 Razavi 절이 없으면(순수 전자회로1 복습, Lec1–2뿐) 이 단계를 건너뛴다(문제 0개).

### 2. manifest
- 요약들의 슬라이드 대조표와 용어·식 목록으로 `RUN/manifest.json`을 쓴다. 규칙은 `references/manifest-guide.md`에 있다.
- 첫 섹션은 항상 `why`(토픽 `why-circuit`, "들어가며: 왜 이런 회로를 쓸까")다. 요약의 `## 동기 발언`으로 `required_terms`를 고른다(`references/manifest-guide.md`).
- 문제 선별은 `references/problem-selection.md`를 따른다. 요약의 `## 교과서 절 대조`와 `RUN/candidates.tsv`로 고른다.
- 검증: `python3 "$SKILL/scripts/manifest.py" "$RUN/manifest.json" "$REPO"` 결과가 `OK`여야 한다.

### 3. 작성
- 섹션마다 작성자 1명을 띄운다. 브리프는 `references/content-rules.md`, 위젯 규칙은 `references/widget-rules.md`에 있다.
- 모두 **한 메시지에서 병렬로** 띄운다. 모델은 opus(GPT: sol), `lite`이면 sonnet(GPT: luna)이다. 병렬 작성자끼리 임시 파일이 섞이지 않게 브리프에 각자의 임시 폴더 `<RUN>/work/<sid>/`를 적어 준다.
- 브리프의 `<…>` 자리는 실제 경로, id, 금지어 목록(`<forbidden 목록>`), 예고 토픽 id(`<preview_topic>`), 섹션 작성자에게 필요한 교과서 장 PDF와 쪽(`<N>장.pdf`, `<쪽>`), 그리고 manifest `links` 중 그 섹션 토픽에 속한 것만(`<이 섹션의 links 목록>`) 채워 넣는다. 요약·예고 섹션 작성자에게는 문제 수(0이면 "문제 없음")도 알린다.
- `why` 섹션 작성자도 함께 병렬로 띄운다. 브리프의 `<뒤 섹션 토픽 id·제목 목록>`에 manifest의 나머지 토픽 id와 제목을 모두 적어 준다(링크 대상). 위젯은 두지 않는다.
- 위젯은 팩 전체에 0~2개다. 병렬 작성자끼리는 서로를 모르므로 **메인 에이전트가 띄우기 전에** 위젯을 둘 토픽(0~2개)을 정하고, 그 토픽의 섹션 작성자 브리프에만 `<위젯>` 자리에 "토픽 `<토픽 id>`에 위젯 1개: <무엇을 움직이면 무엇이 보이는지>"를 적는다. 나머지 작성자의 `<위젯>` 자리에는 "위젯 없음"이라고 적는다. 정한 토픽과 이유는 보고서 "스킬이 정한 사항"에 적는다.

### 4. 조립
- **부모가 problems.txt·slug·정리노트를 처음 변경하기 전에** `references/problem-explain-integration.md`의 기존 설명 백업·정리 절차를 먼저 끝낸다. PDF 선행 빌드도 그 뒤에 한다. 재조립마다 반복하지 않는다. 기본 팩 재생성이 실패하면 해당 참조의 복원 순서를 따른다.
- PDF 빌드는 manifest만 있으면 되므로 3단계 작성자들이 도는 동안 먼저 돌려도 된다(백업·정리는 그보다 먼저 끝내 둔다).
- **처음 조립할 때만**: `복습노트/<range>/`에 이번 `range`의 산출물(맨 위의 `정리노트_<range>_*`·`복습문제_<range>_*`, `.assets/`의 `정리노트_<range>_*`·`problems.txt`·`figures_<range>/`)이 하나라도 있으면 먼저 백업한다. 다시 조립할 때(5~8단계에서 돌아온 경우)는 백업하지 않는다. 이미 스킬이 만든 초안이 백업에 섞이기 때문이다.
  - `RANGE`, `REPO`, `RUN`을 모두 실제 값으로 바꿔 한 명령으로 실행한다. 파일명은 NFC로 비교하므로 NFD 파일명도 잡힌다.
  - 백업은 매번 새 폴더 `RUN/previous-<시각>-<임의>/`에 만든다. `RANGE`가 형식에 안 맞거나, 대상이 있는데 복사된 파일 수가 다르면 종료 코드 1로 멈춘다. 이때는 조립하지 말고 원인을 고친다.
```bash
RANGE=<range> REPO=… RUN=… python3 - <<'EOF'
import os, re, shutil, sys, tempfile, time, unicodedata as u
r, run, repo = os.environ["RANGE"], os.environ["RUN"], os.environ["REPO"]
if not re.fullmatch(r"\d{4}(-\d{4})?", r) or not os.path.isdir(run):
    sys.exit(f"백업 중단: RANGE={r!r} 또는 RUN={run!r} 잘못됨")
if not os.path.isdir(os.path.join(repo, "STT")):
    sys.exit(f"백업 중단: REPO={repo!r} 잘못됨")
notes = os.path.join(repo, "복습노트")
def listdir_nfc(d):  # NFD 폴더명도 찾는다
    return {u.normalize("NFC", n): os.path.join(d, n) for n in os.listdir(d)} if d and os.path.isdir(d) else {}
pack = listdir_nfc(notes).get(r)
top = listdir_nfc(pack)
hits = sorted((n, p) for n, p in top.items() if n.startswith((f"정리노트_{r}_", f"복습문제_{r}_")))
hits += sorted((f".assets/{n}", p) for n, p in listdir_nfc(top.get(".assets")).items()
               if n.startswith(f"정리노트_{r}_") or n in (f"figures_{r}", "problems.txt"))
if not hits:
    print("백업할 기존 팩 없음"); sys.exit(0)
def count(p):
    return sum(len(f) for _, _, f in os.walk(p)) if os.path.isdir(p) else 1
dst = tempfile.mkdtemp(prefix=time.strftime("previous-%Y%m%d-%H%M%S-"), dir=run)  # 항상 새 폴더
for n, a in hits:
    b = os.path.join(dst, n)
    os.makedirs(os.path.dirname(b), exist_ok=True)
    shutil.copytree(a, b) if os.path.isdir(a) else shutil.copy2(a, b)
want_n, got_n = sum(count(a) for _, a in hits), count(dst)
if got_n != want_n:
    sys.exit(f"백업 실패: 파일 {want_n}개 중 {got_n}개만 복사됨 → {dst}")
print(f"백업 {len(hits)}항목(파일 {got_n}개): {dst}", *(a for _, a in hits), sep="\n")
EOF
```
  - 백업 직후(처음 조립이고 백업이 성공했을 때만): 이번 manifest가 만들 이름과 다른, 이번 range의 이전 산출물(문제가 0개로 바뀌었거나 slug가 바뀐 경우의 옛 `정리노트_<range>_*`/`복습문제_<range>_*`)을 지운다. 위에서 이미 백업했으므로 지워도 안전하다.
```bash
python3 - "$RUN/manifest.json" "$REPO/복습노트/<range>" <<'EOF'
import json, os, sys, unicodedata as u
m = json.load(open(sys.argv[1], encoding="utf-8"))
r, slug, out = m["range"], m["slug"], sys.argv[2]
keep = {f"정리노트_{r}_{slug}.html", f".assets/정리노트_{r}_{slug}.md"}
if m["problems"]:
    keep |= {f"복습문제_{r}_{slug}-문제.pdf", f"복습문제_{r}_{slug}-답안.pdf"}
removed = []
for sub in ("", ".assets/"):  # 맨 위와 .assets/ 의 파일만 본다
    d = os.path.join(out, sub)
    for n in (os.listdir(d) if os.path.isdir(d) else []):
        nn = u.normalize("NFC", n)
        if nn.startswith((f"정리노트_{r}_", f"복습문제_{r}_")) and sub + nn not in keep and os.path.isfile(os.path.join(d, n)):
            os.remove(os.path.join(d, n))
            removed.append(sub + nn)
print("제거:", ", ".join(removed) if removed else "없음")
EOF
```
- 정리노트를 조립한다.
```bash
python3 "$SKILL/scripts/assemble.py" --run "$RUN" --out "$REPO/복습노트/<range>"
```
- 문제가 1개 이상이면 PDF를 만든다(`references/problem-selection.md` 5). `--ids`는 manifest `problems` 순서대로 쉼표로 잇는다. 값은 아래처럼 manifest에서 그대로 뽑아 쓴다(손으로 다시 나열하지 않는다).
```bash
python3 -c "import json,sys;print(','.join(q['id'] for q in json.load(open(sys.argv[1]))['problems']))" "$RUN/manifest.json"
```
```bash
python3 "$REPO/workbook/build_workbook.py" --ids <위 결과> --name 복습문제_<range>_<slug> --layout video-16x9 --pdf-dir "$REPO/복습노트/<range>" --build-dir "$RUN/workbook-build"
```
  - stderr에 `ERROR <md 경로>: …`(문제 md 자체 오류, 종료 코드 2)가 나오면 해당 id를 같은 절 후보로 한 번 바꿔 manifest를 고치고 2단계 검증부터 다시 하고 이 단계를 다시 한다(백업은 하지 않는다). `ERROR <name>: …`(렌더링·Chrome·네트워크, 종료 코드 1)나 `OVERFLOW`는 md 문제가 아니므로 id를 바꾸지 않고 "미해결"로 보고한다(`references/problem-selection.md` 5).

### 5. 기계 검사
```bash
python3 "$SKILL/scripts/check_html.py" --manifest "$RUN/manifest.json" --note "$REPO/복습노트/<range>/<정리노트>.html"
```
- `FAIL`이면 Problem의 `where`(토픽 id, 섹션 id)로 담당 작성자를 찾는다. `broken-link`가 PDF이면 4단계 PDF 빌드를 확인한다.
- 그 작성자에게 문제 목록을 보내 조각을 고치게 한다(SendMessage, 안 되면 같은 브리프로 새 에이전트).
- 고친 뒤 4단계부터 다시 한다. PDF는 manifest `problems`가 바뀐 경우에만 다시 만든다. HTML·MD 조각만 고쳤으면 조립(`assemble.py`)만 다시 하면 된다. 최대 2회까지이며, 그래도 남으면 "미해결"로 보고한다.

### 6. 리뷰 (`lite`면 생략)
- 리뷰어 1명을 띄운다. 브리프는 `references/review-prompt.md`에 있다.
- Critical과 Important는 모두, Minor는 쉬운 것만 고친다. 문제 선별 지적은 메인 에이전트가 manifest를 고치고 PDF를 다시 만든다.
- 담당 작성자별로 **한 번에 모아서** 수정을 요청한다. 수정은 한 번만 한다.
- 수정 후 4~5단계를 다시 한다. 문제 선별(manifest `problems`)을 고쳤을 때만 PDF를 다시 만들고, 정리노트 조각만 고쳤으면 조립만 다시 한다. 반영하지 않은 항목은 보고서에 적는다.

### 7. 브라우저 검증
- `references/browser-check.md`대로 한다.
  - http.server를 빈 포트에 띄운다.
  - 확인: KaTeX 오류 0, 남은 `$` 없음, 375px에서 가로 스크롤 없음, 다크모드, 위젯, 링크(복습문제 PDF 포함), 콘솔 오류
- 결함은 5단계와 같은 방식으로 작성자에게 되돌린다(정리노트 조각만 고치므로 조립만 다시 하면 된다). 이것도 최대 2회 규칙에 포함된다.
- 끝나면 서버를 종료한다.

### 8. MD 변환
```bash
python3 "$SKILL/scripts/html2md.py" "$REPO/복습노트/<range>/<정리노트>.html" --check
```
- `OK`가 나와야 한다.
- 누락이 나오면 대부분 HTML 조각의 마크업 문제다(수식이 `svg`나 `.controls` 안에 있는 경우 등). 조각을 고치고 4단계부터 다시 한다.

### 9. 문제설명
- `references/problem-explain-integration.md`의 부모 호출 계약을 따른다.
- 확정한 manifest `problems`가 1개 이상이면 형제 `ec2-problem-explain` 스킬의 전체 절차를 실행한다. MD 변환 이후이며 최종 보고 이전이다.
- 문제가 0개이면 `skipped-no-problems`다. lite여도 설명 검토는 생략하지 않는다.

### 10. 보고
다음 형식으로 끝낸다.
```
## 복습팩 <range> <완료 | 일부 완료>
- 파일: 복습노트/<range>/… (기본 팩 html 1·md 1·pdf <0|2>, 설명 published이면 html 1·md 1·그림/자료 폴더, 그 외에는 상태와 보류 경로)
- 기본 팩: <완료 | 미해결 — 이유>
- 문제설명: <published | withheld | skipped-no-problems | reused-verified> — <문항/소문항 수, HTML·MD 또는 stage, 검토·disputed·백업 경로>
- 범위: 배운 슬라이드 … / 교과서 절 … / 예고만: …
- 문제 N개: P9.05(장말, 9.1.2) — <why>, … (문제가 0개면 "없음 — <이유>")
- 스킬이 정한 사항: slug, 섹션 구성, 위젯, 문제 구성, 뺀 내용과 이유
- 미해결: … (없으면 "없음")
- 커밋 제안: git add 복습노트/<range> && git commit -m "docs(notes): add review pack <range>"
```
실행 폴더 경로(`RUN`, `EXPLAIN_RUN`)도 적는다. 설명이 withheld이면 제목은 "일부 완료"이며 전체 완료라고 쓰지 않는다. 수정 시 부모는 4~8단계부터, 설명은 자식 절차에 따라 다시 실행한다. extract 뒤 부모 입력·참고 자료가 바뀌면 새 EXPLAIN_RUN에서 시작한다.

## 기존 팩에 왜 페이지 붙이기
첫 섹션 `why`가 생기기 전에 만든 팩에는 다시 조립하지 않고 조각만 끼워넣는다. 기존 토픽 id(`s0-…`)는 그대로라 팩 사이 링크와 읽음 표시가 유지된다.
1. 대상 팩의 `정리노트_*.html`과 `.assets/정리노트_*.md`를 scratchpad에 백업한다(NFC로 찾는다).
2. 팩마다 작성자 1명(opus, 병렬)에게 `references/content-rules.md`의 작성자 브리프를 섹션 `why`로 채워 넘긴다. manifest 대신 기존 노트를 계약으로 삼는다: 근거는 노트 자체(읽기 전용), 그 날짜 STT, 노트 태그의 강의자료, Razavi 장 도입부이고, `<뒤 섹션 토픽 id·제목 목록>`은 노트에서 `article class="topic" id=…`를 뽑아 채운다. 출력은 scratchpad의 `why.html` 한 파일이다.
3. 끼워넣는다. 이미 why 섹션이 있으면 교체하므로 다시 실행해도 된다.
```bash
python3 "$SKILL/scripts/insert_why.py" --note "$REPO/복습노트/<range>/<정리노트>.html" --fragment <why.html>
```
4. `python3 "$SKILL/scripts/check_html.py" <정리노트>.html`이 `OK`, `html2md.py <정리노트>.html --check`가 `OK`(`.assets/`의 md와 `.assets/figures_<range>/fig-why.svg`를 새로 만든다)여야 한다. 커밋할 때 이 svg도 함께 넣는다.
5. 7단계처럼 브라우저로 본다: 표지 다음 첫 화면이 why 토픽인지, 오른쪽 요약 패널, 링크 이동, 다크모드, 375px.

## 오류 처리
| 상황 | 동작 |
|---|---|
| 저장소가 아님 | 알리고 멈춤 |
| 기간에 해당하는 STT 없음 / 인자 없음 + 팩 없음 | 사용 가능한 날짜를 보여 주고 멈춤 |
| PDF 텍스트 추출 실패 | STT만으로 진행하고 보고서에 표시 |
| 범위가 workbook(9~11장) 밖 | 문제 0개, PDF 없이 정리노트만. 보고서에 이유 |
| `problem_index.py`가 ERROR md를 냄 | 그 md는 후보에서 빼고 "미해결"에 적음 |
| `build_workbook.py`가 `ERROR <md 경로>: …` 를 내거나 종료 코드 2 | 문제 md 자체의 오류다. 해당 id를 같은 절 후보로 한 번 교체해 재빌드. 또 실패하면 그 id를 빼고 "미해결" |
| `build_workbook.py`가 `ERROR <name>: …` (렌더링·Chrome·네트워크) 를 내거나 종료 코드 1 (OVERFLOW 없이) | md 문제가 아니므로 id를 바꾸지 않는다. "미해결"에 적고 다음 단계로 진행 |
| `OVERFLOW <파일>: <id>` | 종료 코드 1이지만 PDF는 남음. id를 바꾸지 않고 "미해결"에 적음 |
| 포트 사용 중 | 다른 빈 포트 사용 |
| 문제설명 검산·검토 실패 / disputed | 해당 팩의 설명만 withheld로 기록하고 기본 팩을 유지한다. 다른 팩은 계속한다 |
| 기존 설명 백업·해시 검증 실패 | 원본을 유지하고 부모 첫 조립을 중단한다 |
| 같은 range의 팩이 이미 있음 | 4단계 첫 조립 전에 기존 html·pdf와 `.assets/`의 md·`problems.txt`·`figures_<range>/`를 같은 상대 경로로 새 폴더 `RUN/previous-<시각>-<임의>/`에 복사하고(다시 조립할 때는 복사하지 않음) 백업 경로를 보고서에 적음. 백업 명령이 실패하면 조립하지 않고 원인을 고친다 |
| `insert_why.py`가 `insert_why 실패: …` | 노트는 그대로다. 메시지대로 why 조각을 고쳐 다시 실행 |
| 검사 2회 실패 | 멈추지 않고 나머지 단계를 끝낸 뒤 "미해결"로 보고 |
