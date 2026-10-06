# EC2 Solution Video Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 문제지·답안 PDF 화면을 보존하고 중앙 풀이를 한 글자씩 공개하는 `ec2-solution-video` 스킬을 만들어, 문항별 하드 자막 MP4를 검증·전달한다.

**Architecture:** PDF를 글자 윤곽이 포함된 SVG로 동결하고 표시 이벤트만 제어한다. 에이전트가 문항·풀이 영역·표시 순서·대본을 작성하고 도우미는 검사·음성·실측 타이밍·렌더를 수행한다. 기존 영상 스킬의 화면 독립적인 TTS/cache/budget만 adapter로 사용하고, PDF 조립·렌더·최종 검증은 독립적으로 구현한다.

**Tech Stack:** Python 3.11+, PyMuPDF(조사 환경 1.27.2.3), Pillow, unittest, 로컬 HyperFrames/GSAP, Node와 puppeteer-core/Chrome, FFmpeg/ffprobe/libass, Vertex AI Express Aoede. 실제 실행 버전·자산 SHA256은 RUN에 동결한다. 기존 노트 템플릿·KaTeX 재조판은 사용하지 않는다.

**Spec:** `docs/superpowers/specs/2026-10-07-ec2-solution-video-design.md`. 실행자는 두 문서를 읽는다. 경로는 REPO 기준이며 REPO는 `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2`이다.

## Global Constraints

- 문제지·답안 PDF를 화면 원본으로 사용한다. 답안에 등장하는 풀이의 문장·기호·수치·순서·줄바꿈을 보존하며, 중앙 풀이공간의 원래 위치에서 한 글자씩 공개한다.
- PDF의 흰 배경·색상·회로도·점 격자를 보존한다. 기존 복습 영상의 다크모드 원칙은 이 스킬에 적용하지 않는다.
- 한국어 Aoede, 1920×1080, 30fps, PCM mono 24kHz를 기본으로 한다.
- 기본 글자 속도는 초당 7글자(권장 조절 범위 6–8글자)다. 완성 음절/조판 기호 단위로 공개한다.
- 공급자 `vertex-ai-express`, 모델 `gemini-2.5-flash-tts`를 기본 설정에 기록하고 자동 대체하지 않는다. 기본 `budget_usd=null`, 요청 전체 ledger 하나를 사용한다.
- 문제별 MP4 한 개씩 제작한다. 문항 ID와 자연스러운 한국어 제목을 사용하고 최종 자막본에 `_자막` 접미사를 붙이지 않는다.
- 영상 길이는 풀이에 맞추며 1–3분을 강제하지 않는다. 단어별 실제 음성 정렬을 주장하지 않는다.
- 글자별 공개 첫 게이트와 현재 내용 검토를 통과하기 전 유료 TTS를 실행하지 않는다. 개발 테스트는 fake API/로컬 PCM을 쓴다.
- 기존 스킬·노트·PDF·영상은 수정하지 않는다. 인증 값을 설정·로그·Git에 저장하지 않는다.
- 커밋은 사용자가 실행 세션에서 허용했을 때 작업별로 수행한다. 이 계획 작성 턴에는 커밋하지 않으며 push/merge는 별도 명시적 지시가 필요하다.

## Review Focus

1. 문항 번호가 같은 예제/장말/기출, Hint 부록 및 범위 중복: 전체 ID로 대응하고 모호한 입력/다른 풀이를 중단해야 한다. Task 2의 `test_ambiguous_pair_and_duplicate_conflict`.
2. 겹친 첨자·분수선·근호선·공유 SVG defs와 클립: 글자 조각 유출 없이 원래 도형을 모두 보존해야 한다. Task 1의 `test_glyph_clip_and_math_primitives`.
3. 회로도 축소·2단 풀이 및 작은 글씨: 답안 좌표와 명시적 단계 순서를 따르며 재조판하지 않아야 한다. Task 3의 `test_two_columns_and_independent_camera`.
4. 음성이 글자 수보다 짧거나 부분 TTS가 실패함: 작성 시간을 확보하고 성공 캐시를 재사용해야 한다. Task 4의 `test_short_pcm_extends_writing`와 `test_partial_voice_retry`.
5. 자막 후 파일 변조·이전 결과 충돌·부분 게시 실패: 실제 최종 파일을 검사하고 이전 latest와 결과를 보존해야 한다. Task 7의 `test_final_tamper_and_publish_rollback`.

---

## 파일 구조와 공통 계약

`S=.agents/skills/ec2-solution-video`로 표기한다. 실행 코드는 기존 `lib`와 충돌하지 않도록 `scripts/solution_video/` 패키지에 둔다.

| 새 파일 | 책임 |
|---|---|
| `S/SKILL.md`, `S/agents/openai.yaml` | 호출·경계·원칙·진입 안내 |
| `S/assets/defaults.json`, `S/assets/player.js`, `S/assets/layout.css` | 고정 설정·seek-safe 표시·PDF/자막 배치 |
| `S/scripts/video.py` | 단계 CLI, JSON 결과와 종료 코드 |
| `S/scripts/solution_video/contracts.py`, `__init__.py` | 아래 데이터 계약과 오류 |
| `S/scripts/solution_video/pdf_pages.py` | 원본 SVG export, 표시 도형 분리 |
| `S/scripts/solution_video/sources.py` | 입력 발견·동결·문항 대응 |
| `S/scripts/solution_video/manifest.py` | 에이전트 대본·순서·내용 검토 검사 |
| `S/scripts/solution_video/reveal.py` | 실측 타이밍과 공개 상태 |
| `S/scripts/solution_video/review_adapter.py` | 기존 TTS/cache/budget의 이름 격리 adapter |
| `S/scripts/solution_video/composition.py` | PDF 카메라·장면·편집 소스 조립 |
| `S/scripts/solution_video/media.py`, `subtitles.py` | PDF 전용 렌더·mux·하드 자막 |
| `S/scripts/solution_video/verify.py`, `publication.py`, `state.py` | 검증·게시·지문 기반 재개 |
| `S/references/{pdf-and-coverage,narration-and-timing,verification}.md` | 상세 계약·검토 기준 |
| `S/tests/test_*.py`, `browser_check.mjs`, `fixtures.py` | 의미 있는 회귀·브라우저 검증 |

`contracts.py`는 JSON 직렬화 가능한 TypedDict와 예외 `InputError`, `ExtractionError`, `ReviewError`를 정의한다. 동결 후 경로 문자열은 RUN/batch 안의 상대 POSIX 경로다. discovery는 절대 경로를 반환하고 freeze_sources가 상대 경로로 바꾼다. 영구 원본 위치는 별도 절대 경로 provenance에 둔다. 좌표는 PDF top-left 기준 point(1/72 inch), 페이지 인덱스는 내부 0-based로 통일한다.

- `PageRef={snapshot:str,page_index:int,width_pt:float,height_pt:float}`.
- `PagePair={problem_id:str,problem:PageRef,answer:PageRef,md_snapshot:str|None}`.
- `PageMap={work_bbox:[x0,y0,x1,y1],steps:[{id:str,glyph_ids:list[str],shape_ids:list[str]}],answer_step_id:str}`. 에이전트가 후보 export를 보고 작성한다. 컬럼 순서는 steps 순서다. 회로·조건·Hint 도형은 지정할 수 없다.
- `Glyph={id:str,text:str,bbox:[float,float,float,float],svg_ids:list[str],paint_order:int}`. SVG use 원소가 기준이며 PDF extractor가 합성한 공백을 새로운 글자로 만들지 않는다. 결합 문자/분해 한글의 여러 use가 한 grapheme을 그리면 원래 도형을 svg_ids에 묶어 한 번에 공개한다.
- `Shape={id:str,bbox:[float,float,float,float],svg_ids:list[str],kind:str,paint_order:int}`. kind는 `fraction_bar|radical_bar|step_badge|answer_box|bullet`이다.
- `PageLayers={original_svg:str,animated_svg:str,reference_png:str,glyphs:list[Glyph],shapes:list[Shape],map:PageMap|None}`. export 후보는 전체 페이지 목록과 map=None이고, extract 후 목록은 작성 대상만 포함하며 map은 필수다. DOM의 비대상 요소는 모두 유지한다. original_svg는 수정하지 않는다. animated_svg는 같은 DOM에 안정적인 ID와 표시 속성만 추가한다. defs/clipPath/transform/이미지를 유지한다.
- `Segment={id:str,step_id:str,text:str,source_refs:list[str],kind:str}`. kind는 `problem|reason|write|check|summary`, 원문 대응은 별도 `coverage.json`에 기록한다.
- `CameraKey={at_frame:int,viewbox:[x0,y0,width,height]}`. PDF 단위이며 reveal 시간/배치와 독립적이다.
- `Manifest={schema_version:1,problem_id:str,title:str,segments:list[Segment],reveal_order:list[str],shape_anchors:dict[str,str],cameras:list[CameraKey]}`. reveal_order는 작성 대상 glyph ID를 한 번씩 포함한다. shape_anchors는 도형 ID→같은 단계의 glyph ID이다.
- `AudioRecord={id:str,path:str,samples:int,rate:int,sha256:str}`. adapter의 추가 receipt 필드는 보존한다.
- `RevealEvent={id:str,frame:int,kind:str}`. kind는 `glyph|shape`; frame은 전역 30fps 정수다.
- `Timeline={fps:30,rate:24000,total_samples:int,total_frames:int,segments:list[dict],events:list[RevealEvent],cameras:list[CameraKey]}`. segments에는 Segment 필드와 start_sample/end_sample이 있다.
- `Verification={complete:bool,input_hash:str,checks:dict,evidence:list[str],final_sha256:str|None}`. 자동 구조 검사와 content/audio/visual의 에이전트 의미 검토를 구분한다.

테스트 setUp에서 아래 코드의 self 속성을 해당 작업의 입력으로 준비한다. fixtures.py는 `make_fixture_repo(dest:Path)->Path`(합성 대응 PDF/MD/목록), `make_math_page(dest:Path)->tuple[Path,PageMap]`(클립·분수·첨자), `fake_transport(payload:dict)->dict`(24k PCM 응답), `make_audio(segment_id:str,samples:int,run:Path)->AudioRecord`를 정의한다. 실제 1002 파일을 복사하는 수용 데이터와 합성 fixture를 구분한다.

공통 테스트 실행: `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -p 'test_<component>.py' -v`. 브라우저 테스트는 런타임에서 확인한 Node·puppeteer-core·Chrome의 절대 경로를 받는다. PyMuPDF 없는 Python에서 실행하면 준비 단계가 구체적으로 실패해야 하며 자동 전역 설치하지 않는다.

## Task 1: 원본 PDF 도형 공개의 수용 게이트

**Files:** Create `S/scripts/solution_video/{__init__,contracts,pdf_pages}.py`, `S/tests/{fixtures,test_pdf_pages}.py`, `S/tests/browser_check.mjs`(게이트 모드).

**Interfaces:** Consumes `PageRef`, 에이전트가 검토한 `PageMap`. Produces `export_page(pdf:Path,page_index:int,dest:Path)->PageLayers`의 후보 데이터와 `extract_layers(page:PageLayers,mapping:PageMap)->PageLayers`. 후보 map은 None이고 extract가 확정한다. `compare_completed(page:PageLayers,evidence:Path)->dict`는 `{pixel_diff:int,non_target_diff:int,hidden_leaks:int,evidence:list[str]}`를 반환한다. 네이티브 PDF/SVG 시각 검토는 증거를 읽는 에이전트가 별도로 기록한다.

- [x] **Step 1: 실패 테스트 작성.** `test_completed_svg_matches_original`는 숨김→전체 공개 결과의 RGB 픽셀 차이가 0임을 검사한다. `test_glyph_clip_and_math_primitives`는 겹치는 아래첨자, 분수/근호선, defs 공유, clipping이 있는 fixture에서 숨긴 glyph의 그림이 없고 비대상 도형은 동일하며 전체 glyph/shape 공개 후 원본과 같음을 검사한다. scan-only 페이지와 work 밖 ID는 `ExtractionError`다. 합성 fixture는 로컬 PDF 글꼴/도형으로 만들고 실제 한글은 1002 PDF로 검사한다.
```python
def test_completed_svg_matches_original(self):
    layers = extract_layers(export_page(self.pdf, 0, self.dest), self.page_map)
    result = compare_completed(layers, self.evidence)
    self.assertEqual(result['pixel_diff'], 0)
    self.assertEqual(result['non_target_diff'], 0)
    self.assertEqual(result['hidden_leaks'], 0)
```

- [x] **Step 2: red 확인.** 공통 명령의 component=`pdf_pages`. 예상: 새 모듈/함수 미정의로 실패한다. 실제 PDF 게이트는 아직 실행하지 않는다.
- [x] **Step 3: 최소 구현.** PyMuPDF `get_svg_image(text_as_path=True)`의 data-text/use를 glyph ID로 내보낸다. 모든 상위 transform/clip, 공유 defs, embedded 이미지는 그대로 둔다. 도형의 paint order와 bbox를 PDF drawing 정보와 대응하고, 분류 불가능한 작성 요소는 오류로 보고한다. 글자·도형을 숨길 때 부모/이미지/격자를 제거하지 않는다. 이미지 내부 풀이 글자는 지원하지 않는다.
- [x] **Step 4: green과 실제 게이트.** 테스트를 통과한 뒤 1002 E10.11/E10.13/2021-1_중간-Q3를 임시 RUN에서 export하고 검토한 PageMap으로 브라우저의 empty/partial/complete 프레임을 만든다. 동일 브라우저 완료 비교 `pixel_diff=0`, 원본 PDF/SVG 직접 시각 검토, 한글·수식·2단·Hint 보존을 증거로 남긴다. 실패하면 원본 재조판이나 마지막 이미지 교체로 감추지 않고 이 작업에서 중단한다. 유료 요청 수는 0이다.
- [x] **Step 5: 범위 검토·커밋.** 위 파일과 게이트 코드만 검토한다. 커밋 권한이 있으면 `feat(ec2-solution-video): preserve PDF glyphs for reveal`로 커밋하며 임시 RUN과 입력 PDF 복사본은 커밋하지 않는다.

## Task 2: 문항 발견·대응·원자료 동결

**Files:** Create `S/scripts/solution_video/sources.py`, `S/tests/test_sources.py`.

**Interfaces:** Consumes PagePair 계약과 `workbook/assemble.py`의 ID 해석 규칙. Produces `discover(repo:Path,selector:str,problem_ids:list[str]|None)->list[PagePair]`, `freeze_sources(pairs:list[PagePair],batch:Path)->list[PagePair]`, `validate_pairs(pairs:list[PagePair])->None`.

- [x] **Step 1: 실패 테스트 작성.** `test_1002_pairs_skip_hint`는 10쌍과 E10.11 problem/answer page_index=1, Q3 page_index=7, 부록 제외를 검사한다. `test_ambiguous_pair_and_duplicate_conflict`는 E/P/기출의 번호가 같아도 전체 ID로 구분하고, 동일 ID 다른 답안은 `InputError`, 동일 입력 중복은 최초 등장 한 쌍만 남김을 검사한다. 범위 밖 ID·누락 PDF·서로 다른 조건·유효하지 않은 selector도 오류다. NFC/NFD 경로의 동일 파일 발견과 동결 후 원본 변경에도 snapshot 해시 유지도 검사한다.
```python
def test_1002_pairs_skip_hint(self):
    pairs = discover(self.repo_with_1002_copies, '1002', None)
    self.assertEqual(len(pairs), 10)
    match = next(p for p in pairs if p['problem_id'] == 'E10.11')
    self.assertEqual(match['problem']['page_index'], 1)
    self.assertEqual(match['answer']['page_index'], 1)
```

- [x] **Step 2: red 확인.** component=`sources`. 예상: sources 함수 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** `problems.txt`와 실제 PDF 제목/문항·회로·조건을 대응한다. 후보가 복수면 임의 선택하지 않는다. 날짜는 MMDD 또는 MMDD-MMDD로 검증하고 존재하는 폴더만 사용한다. 안전한 내부 키는 표시 제목/원래 ID와 분리한다. 입력 SHA256과 tool provenance를 `batch/source/inputs.json`에 저장하고 PageRef 경로를 snapshot으로 변환한다.
- [x] **Step 4: green 확인.** component=`sources` 통과. 1002 읽기 전용 discovery 결과 10쌍을 확인하고 PDF 파일 해시가 변하지 않았음을 검사한다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): freeze matched problem sources`로 이 작업 파일만 커밋한다.

## Task 3: 풀이 순서·대본·내용 검토 계약

**Files:** Create `S/scripts/solution_video/manifest.py`, `S/tests/test_manifest.py`, `S/references/pdf-and-coverage.md`.

**Interfaces:** Consumes PageLayers와 Manifest. coverage는 `{status,input_hash,pdf_md_agree,rows:[{step_id,source_refs,pdf_text,md_text,meaning_review}]}`, circuit_review는 `{status,input_hash,steps:[{step_id,assumptions,equations,units,evidence}]}`이며 status=passed, pdf_md_agree=true가 필요하다. Produces `validate_manifest(manifest:Manifest,layers:PageLayers,coverage:dict,circuit_review:dict)->None`, `content_fingerprint(manifest:Manifest,layers:PageLayers,coverage:dict)->str`. 지문은 coverage의 status/input_hash를 제외한 원문 대응 rows와 실제 source/manifest/layer 파일만 포함한다. 각 검토의 status/input_hash를 지문에 다시 넣지 않는다.

- [x] **Step 1: 실패 테스트 작성.** `test_exact_glyph_coverage_and_current_review`는 glyph 누락·중복·외부 ID·도형 anchor 누락·답 선공개·오래된 내용 지문을 모두 `ReviewError`로 거부한다. `test_two_columns_and_independent_camera`는 Q3의 단계 1→2→3→4→답 순서를 좌표 정렬과 독립적으로 유지하며, E10.13의 답안 회로 bbox를 사용함을 검사한다. `test_pdf_md_disagreement_blocks_voice`는 수치/부호가 다른 PDF/MD 검토 결과에서 ready가 되지 않음을 검사한다.
```python
def test_exact_glyph_coverage_and_current_review(self):
    missing = dict(self.manifest, reveal_order=self.manifest['reveal_order'][:-1])
    with self.assertRaises(ReviewError):
        validate_manifest(missing, self.layers, self.coverage, self.circuit_review)
    stale = dict(self.circuit_review, input_hash='stale')
    with self.assertRaises(ReviewError):
        validate_manifest(self.manifest, self.layers, self.coverage, stale)
```

- [x] **Step 2: red 확인.** component=`manifest`. 예상: 검사 함수 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** 검사는 구조·대응·현재 지문을 확인한다. 에이전트가 PDF/MD 대조의 근거를 coverage에, 가정·노드·부호·단위·계산 근거를 circuit_review에 기록해야 ready가 된다. 보고서 형식 성공을 의미 검토 승인으로 자동 치환하지 않는다. 풀이의 원문 내용은 도형/coverage에서 확인하고 발화문은 필요한 근거에 연결한다. reference에 작성 절차와 충돌 처리 기준을 적는다.
- [x] **Step 4: green 확인.** component=`manifest` 통과. 대표 실제 문항의 PageMap/Manifest/coverage 검토에서 모든 작성 glyph와 shape가 한 번씩 연결되고 원본 PDF 내용이 빠지지 않았음을 직접 확인한다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): validate exact solution coverage`로 커밋한다.

## Task 4: Aoede 음성과 실측 공개 타이밍

**Files:** Create `S/scripts/solution_video/{review_adapter,reveal}.py`, `S/assets/defaults.json`, `S/tests/{test_voice,test_reveal}.py`, `S/references/narration-and-timing.md`.

**Interfaces:** Consumes validate_manifest와 Segment. Produces `generate_voice(segments:list[Segment],run:Path,config:dict,ledger:Path,transport:Callable|None=None)->list[AudioRecord]`, `build_timeline(manifest:Manifest,layers:PageLayers,audio:list[AudioRecord],config:dict)->Timeline`, `visible_ids(timeline:Timeline,frame:int)->list[str]`(공개된 glyph ID만 반환하며 shape는 events의 kind로 조회한다).

- [x] **Step 1: 실패 테스트 작성.** `test_partial_voice_retry`는 두 문단 중 한 문단 실패 후 재개할 때 성공 문단의 호출 횟수가 1이고 공용 ledger를 사용함을 검사한다. `test_voice_defaults_and_secret_redaction`는 provider/model/Aoede/ko-KR/24000과 config/log의 키 부재를 검사한다. `test_short_pcm_extends_writing`은 N=70 글자·1초 PCM일 때 작성창을 최소 10초 확보하고 음성 속도를 바꾸지 않으며 후행 구간을 밀어 전체 길이를 맞춤을 검사한다. 공간 문자는 시간만 사용하고 초당 7글자를 넘지 않는다. `test_seek_is_pure`는 0→end→middle→0 상태와 각 프레임을 직접 조회한 상태가 같다.
```python
def test_short_pcm_extends_writing(self):
    # setUp: 70 glyphs, one write Segment, one 24000-sample PCM.
    t = build_timeline(self.manifest, self.layers, self.audio, self.config)
    self.assertGreaterEqual(t['total_samples'], 258000)  # 10s + 0.75s
    self.assertEqual((t['fps'], t['rate']), (30, 24000))
    self.assertEqual(visible_ids(t, t['total_frames'] - 1),
                     self.manifest['reveal_order'])
```

- [x] **Step 2: red 확인.** component=`voice`, `reveal` 두 명령. 예상: adapter/timeline 함수 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** adapter는 기존 scripts/lib를 `_ec2_review_video_lib`의 importlib package로 불러 상대 import를 보존하고 전역 `lib` 이름을 건드리지 않는다. cache/budget/vertex_tts만 호출한다. 사용한 소스 파일·기본값 SHA256을 RUN에 기록하고 resume 시 변경을 확인한다. timeline은 정수 샘플/프레임을 사용하고 write 구간 길이를 `max(음성 길이, 글자 수/7)+0.75초 읽기 여유`로 잡는다. 초당 7글자는 프레임 간격으로 보수적으로 올림한다. anchor 도형은 연결 glyph와 같은 프레임에 공개하고 final answer는 마지막 단계다. 예상보다 긴 발화는 잘라내지 않는다.
- [x] **Step 4: green 확인.** 두 테스트 통과. fake PCM으로 30fps 총 프레임=ceil(total_samples×30/24000), 마지막 A/V 차이≤1프레임, 부분 실패 캐시 재사용을 확인한다. 비용과 실제 음성 청취는 검증하지 않았다고 기록한다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): time PDF writing from measured speech`로 커밋한다.

## Task 5: PDF 카메라·커서·HyperFrames 조립

**Files:** Create `S/scripts/solution_video/composition.py`, `S/assets/{player.js,layout.css}`, `S/tests/test_composition.py`; Extend `S/tests/browser_check.mjs`(timeline 모드).

**Interfaces:** Consumes PagePair/PageLayers/Manifest/Timeline. Produces `assemble(pair:PagePair,layers:PageLayers,manifest:Manifest,timeline:Timeline,run:Path,runtime:Path)->list[dict]`. parts 항목은 `{entry:str,first_frame:int,last_frame:int,key:str}`이며 first inclusive/last exclusive다. player는 `window.renderSolutionFrame(frame)`을 노출하고 HyperFrames paused timeline에서 호출한다.

- [x] **Step 1: 실패 테스트 작성.** `test_original_layout_and_caption_safe_area`는 PDF viewport y=0..900, 자막 영역 y=900..1080, viewport clip 적용, 원본 SVG의 좌표/변환 유지, 문제→가린 답안→완료 순서를 검사한다. `test_cursor_removed_and_no_reflow`는 글자 공개 중 모든 glyph bbox가 그대로이며 완료 커서가 없음을 검사한다. `test_browser_seek_and_native_glyphs`는 랜덤 순서 seek 결과가 직접 해당 프레임 렌더와 같고, text/KaTeX 재조판이 없고, 다음 glyph 누출이 없음을 검사한다.
```python
def test_parts_have_exact_frame_coverage(self):
    parts = assemble(self.pair, self.layers, self.manifest, self.timeline,
                     self.run, self.runtime)
    self.assertEqual(parts[0]['first_frame'], 0)
    self.assertEqual(parts[-1]['last_frame'], self.timeline['total_frames'])
    self.assertTrue(all(a['last_frame'] == b['first_frame']
                        for a, b in zip(parts, parts[1:])))
```

- [x] **Step 2: red 확인.** component=`composition`. 예상: assemble 함수 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** 원본 비율을 유지해 전체 페이지를 viewport에 맞춘다. 작성 중 glyph의 실제 표시 높이가 26px 미만이면 해당 단계 viewbox를 확대하도록 에이전트 카메라를 검사한다. 필요한 조건/회로 확인은 독립 카메라 구간으로 둔다. Manifest.cameras가 비어 있으면 실측 Timeline의 단계 시작과 PageMap bbox로 기본 카메라 키를 생성한다. 명시적인 키가 있으면 이를 검사하고 사용한다. 카메라와 커서 외의 새 카드·색상·수식을 만들지 않는다. 원본/animated SVG만 사용한다. 로컬 GSAP와 자산을 RUN에 동결하며 외부 URL·타이머·난수는 허용하지 않는다.
- [x] **Step 4: green 확인.** Python 테스트와 `node S/tests/browser_check.mjs --mode timeline --run RUN --puppeteer-package ABS_PACKAGE_JSON --chrome ABS_CHROME`를 통과시킨다. 장면별 편집 소스에 로컬 HyperFrames `check`를 실행한다. 대표 empty/partial/final 프레임을 직접 확인한다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): assemble seek-safe PDF scenes`로 커밋한다.

## Task 6: 흰 PDF 렌더·하드 자막·최종 검증

**Files:** Create `S/scripts/solution_video/{media,subtitles,verify}.py`, `S/tests/{test_media,test_verify}.py`, `S/references/verification.md`.

**Interfaces:** Consumes parts/Timeline/AudioRecord. Produces `render_master(parts:list[dict],timeline:Timeline,audio:list[AudioRecord],run:Path,hyperframes_entry:Path)->Path`, `write_srt(timeline:Timeline,dest:Path)->Path`, `burn_subtitles(master:Path,srt:Path,dest:Path,font:Path)->Path`, `verify_run(run:Path,hyperframes_entry:Path)->Verification`.

- [x] **Step 1: 실패 테스트 작성.** `test_white_pdf_renders_and_captions_stay_outside`는 흰 페이지가 오류로 거부되지 않고 자막 박스 전체가 y≥900임을 검사한다. `test_final_media_checked_after_burn`은 자막본 누락/자막 영역 침범/해시 변경을 거부하며 마스터만으로 complete가 되지 않음을 검사한다. `test_source_timeout_and_missing_reviews`는 HyperFrames check timeout과 현재 content/audio/visual 증거 부재를 unverified로 분류한다. 짧은 무음 PCM은 자동 미디어 검사용이며 실제 음성 의미 검토 통과로 사용하지 않는다.
```python
def test_final_media_checked_after_burn(self):
    # setUp: valid master only; final MP4 and current reviews absent.
    report = verify_run(self.run, self.hyperframes_entry)
    self.assertFalse(report['complete'])
    self.assertIsNone(report['final_sha256'])
```

- [x] **Step 2: red 확인.** component=`media`, `verify`. 예상: 함수 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** FFmpeg CPU/NVENC 지원을 실제 짧은 로컬 probe로 시험하고 지원되는 인코더를 기록한다. 장면 렌더와 PCM을 결합하며 전역 GPU 설정은 바꾸지 않는다. PDF 전용 자막은 Pretendard Bold/FontSize=14/Alignment=2/MarginV=22/Outline=4/Shadow=0/BorderStyle=3/흰 글자/검정 약70% 박스, 한 줄 약34자를 사용한다. 문장을 작은 TTS 단위로 구성하고 긴 한 덩어리는 34자 이하로 분리해 두 줄 자막이 PDF를 침범하지 않게 한다. libx264 crf18·오디오 복사로 굽는다. 흰 화면 검사에 기존 dark_failures를 호출하지 않는다. 전체 decode·1920×1080·30fps·24k PCM provenance·최종 시간차≤1프레임·해시·현재 검토를 검사한다.
- [x] **Step 4: green 확인.** 두 테스트와 로컬 PCM의 5–15초 샘플 렌더를 통과시킨다. 최종 MP4의 실제 자막 구간 프레임/ffprobe/전체 decode를 검사한다. exporter/HTML 검증과 미디어·내용·음성 의미 검토를 구분한 report를 작성한다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): verify captioned PDF videos`로 커밋한다.

## Task 7: 재개·묶음 게시·CLI

**Files:** Create `S/scripts/solution_video/{state,publication}.py`, `S/scripts/video.py`, `S/tests/{test_state,test_publication,test_cli}.py`.

**Interfaces:** Consumes 앞 작업의 함수. Produces `stage_fingerprint(run:Path,stage:str)->str`, `recover_run(run:Path)->str|None`, `finish_stage(run:Path,stage:str,outputs:list[Path])->None`(state.py), `prepare_batch(repo:Path,selector:str,problem_ids:list[str]|None,review:bool)->Path`, `resume_batch(batch:Path)->dict`(문항별 next/status), `publish_batch(batch:Path)->dict`(`complete:bool,published:list[str],errors:list[dict]`), `main(argv:list[str]|None=None)->int`.

- [x] **Step 1: 실패 테스트 작성.** `test_first_invalid_stage_and_voice_preservation`은 PageMap 변경 시 layers부터, 음성 설정 변경 시 voice부터, captions 파일 변경 시 captions부터 무효화하고 영향 없는 음성 캐시를 보존함을 검사한다. `test_final_tamper_and_publish_rollback`은 최종 파일 변조·같은 제목 충돌·두 번째 파일 이동 실패 때 이전 결과/latest를 보존하고 첫 파일의 이전버전도 복구함을 검사한다. 부분 성공은 verified 파일만 게시하며 batch complete=false/latest 불변이다. `test_review_gate_and_zero_paid_prepare`는 review 모드의 현재 script_hash 승인 전 TTS 차단, 기본 모드 불필요 승인 없음, prepare/extract/check 유료 요청 0을 검사한다.
```python
def test_final_tamper_and_publish_rollback(self):
    before = self.latest.read_bytes()
    self.final_mp4.write_bytes(b'changed-after-verification')
    result = publish_batch(self.batch)
    self.assertFalse(result['complete'])
    self.assertEqual(self.latest.read_bytes(), before)
```

- [x] **Step 2: red 확인.** component=`state`, `publication`, `cli`. 예상: 함수/CLI 미정의로 실패한다.
- [x] **Step 3: 최소 구현.** 상태는 `inputs,layers,script,voice,timing,composition,render,captions,verify,publish`와 입출력 해시를 기록한다. 동결 snapshot/도구/adapter 변경이 resume 지문에 반영되어야 한다. 지문은 생성할 report/reviews/run 상태 파일 자체를 포함하지 않아 순환하지 않으며, 검토에는 그 지문과 증거 파일 해시를 기록한다. CLI는 `prepare SELECTOR --repo --problems --review`, `extract/check/tts/assemble/render/captions/verify --run`, `resume-set/publish-set --batch`를 제공한다. tts에는 `--config`, `--env-file`, `--approve-review`를, assemble에는 `--runtime`, render/verify에는 `--hyperframes-entry`를 제공한다. prepare는 동결 페이지를 export_page로 후보 SVG/목록까지 내보내어 에이전트가 PageMap을 작성할 수 있게 한다. extract는 작성한 PageMap으로 확정하고 현재 지문의 게이트 증거를 저장한다. tts는 해당 증거와 validate_manifest를 다시 확인한다. 에이전트 PageMap/Manifest가 없는 상태는 author-required이며 자동 창작하지 않는다. 출력 JSON은 passed/author-required/awaiting-review/failed와 paid_requests를 포함한다. 실패 종료코드=1, 사용자 작성/검토 대기=0이다. 게시 시 같은 파일시스템 staging·backup·journal로 이전버전 보존/복구를 수행하고 final MP4 해시를 catalog.json/README.md에 기록한다. 날짜 루트에는 최종 MP4와 제작자료 폴더만 두며 캐시 마스터는 RUN 안에 남긴다.
- [x] **Step 4: green 확인.** 세 테스트 통과. 실행 중단·해시 변경·부분 성공·게시 이동 실패를 주입해 resume 및 rollback을 확인한다. snapshot과 자막본을 마스터 입력으로 혼동하지 않는다.
- [x] **Step 5: 범위 검토·커밋.** 권한이 있으면 `feat(ec2-solution-video): resume and publish problem batches`로 커밋한다.

## Task 8: 스킬 진입·전체 수용 검증

**Files:** Create `S/SKILL.md`, `S/agents/openai.yaml`, `S/tests/test_acceptance.py`; Finalize 앞 작업의 references와 defaults.

**Interfaces:** Consumes 전체 CLI. Produces 사용자 호출에 따라 원자료 읽기→PageMap/대본 작성→CLI 제작→검증·전달을 수행할 수 있는 발견 가능한 프로젝트 로컬 스킬.

- [x] **Step 1: 실패 수용 테스트 작성.** `test_fake_pcm_end_to_end_problem_batch`는 1002 대표 3문항을 별도 임시 출력 repo에서 fake TTS로 제작해 MP4=3, 각 problem_id=1, 하드 자막본 SHA256과 catalog 일치, latest가 검증된 batch를 가리킴을 검사한다. 원본 PDF·기존 스킬 해시는 동일하고 유료 요청=0이어야 한다. 이 자동 검사는 실제 음성 청취 검토를 대체하지 않는다.
```python
def test_fake_pcm_end_to_end_problem_batch(self):
    # setUp: full local pipeline for 3 problems, fake PCM, isolated repo.
    result = publish_batch(self.completed_batch)
    self.assertTrue(result['complete'])
    self.assertEqual(len(result['published']), 3)
    self.assertEqual(len(list(self.output_dir.glob('*.mp4'))), 3)
    self.assertEqual(self.fake_transport_live_calls, 0)
```

- [x] **Step 2: red 확인.** component=`acceptance`. 예상: 아직 준비되지 않은 CLI 연동/문항 수용 데이터로 실패한다. 외부 서비스 비용은 발생시키지 않는다.
- [x] **Step 3: 스킬 작성.** 설명에는 PDF 복습문제 풀이 영상, 글자별 공개, 날짜/ID/재개/review 호출과 개념 복습 영상의 경계를 넣는다. 본문에 원본 보존 원칙, 단계 작성·내용 검토, 첫 게이트, 기본 Aoede·길이·출력, 실패·재개, 실행 명령을 적는다. 목소리 변경·스캔 자동 처리·추가 풀이 작성은 지원한다고 쓰지 않는다. references를 필요한 단계에서만 읽게 연결한다. agents/openai.yaml은 정상 자동 발견을 유지한다.
- [x] **Step 4: 전체 green과 검토.** `python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`, 기존 `python3 -m unittest discover -s .agents/skills/ec2-review-video/tests -v`, skill-creator의 `quick_validate.py`를 실행한다. 대표 3문항의 실제 최종 프레임·재생과 source check를 확인한다. 실제 Aoede 운영 샘플은 구현 요청의 비용/범위가 이를 포함할 때 수행하고 청취·동기화를 기록한다. 실행하지 않았다면 live_audio=unverified로 명시하고 실제 음성 제작까지 완료했다고 보고하지 않는다.
- [x] **Step 5: 범위 검토·커밋 및 전달.** 권한이 있으면 새 스킬 파일만 `feat(skills): add PDF solution video workflow`로 커밋한다. 설치된 스킬, 실제 검증 범위, 미확인 실제 음성 항목, 요청한 산출물만 절대 경로로 전달한다. Git push/merge는 수행하지 않는다.

## 자체 검토와 실행 인계

- 설계 요구 대응: PDF 보존/글자 공개→Task 1·5, 문항/원자료→Task 2, 내용/계산→Task 3, 음성/타이밍→Task 4, 자막/최종 검증→Task 6, 재개/출력→Task 7, 호출/발견→Task 8.
- Review Focus 다섯 항목은 각 소유 작업의 명시적 테스트에 반영했다. 선언한 반환 타입과 다음 작업의 입력 타입을 일치시켰다.
- 계획은 구현 본문을 대신 쓰지 않는다. 에이전트가 작성할 문항별 PageMap·Manifest·대본은 원자료 검토 때 만든다.
- PDF 도형 분류와 SVG 충실도는 Task 1의 실제 게이트까지 미검증이다. 다른 제작 단계가 성공해도 이 게이트 실패를 우회하지 않는다.
- 추천 실행 방식: **Native**. 8개 작업이 같은 문항/글자/타이밍 계약을 이어 사용하므로 한 실행자가 인터페이스를 유지하며 구현하고 마지막에 독립 리뷰를 받는 방식이 적합하다. 사용자가 Subagent-driven을 선택하면 작업별 구현·독립 리뷰를 수행한다.
- 사용자가 계획을 검토하고 실행 방식을 선택한 다음 구현을 시작한다. 이번 턴에는 이 계획과 설계 문서만 저장한다.

## Native 실행 결과

새 프로젝트 로컬 스킬과 실행 도우미를 구현했다. 최종 37개 테스트(실제 PDF 로컬 PCM 수용 포함), 기존81개 테스트(ffmpeg-full 지정), 스킬/YAML 및 공백 검사를 통과했다. 독립 리뷰의6건을 재현 테스트로 수정했다. 실제 Aoede 호출/청취는 이번 구현 범위에서 실행하지 않았다. 조건부 커밋 단계는 권한이 없어 범위 검토만 수행했다. 구현 판단과 검증 범위는 `../reviews/2026-10-07-ec2-solution-video.md`에 기록했다.
