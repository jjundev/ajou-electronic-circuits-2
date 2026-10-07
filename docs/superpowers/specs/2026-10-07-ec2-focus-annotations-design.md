# 회로 주석과 풀이 포커스를 연결하는 영상 설계

상태: 2026-10-07 채팅의 grill-yourself 설계를 통합했다. 사용자는 writing-plans를 요청했다. 이전 #7은 주 화면만 번갈아 이동, #14는 주석을 최종 전체 화면 직전까지 누적 유지로 기본 확정했다. 이후 사용자가 Native 구현을 선택했다. 별도 작업트리에 구현하고 개발용 PCM으로 실자료를 검증했다. 유료 호출과 커밋·push·merge는 수행하지 않았다.

## 의도와 범위

학생이 회로의 연결 관계와 풀이식을 연결하도록 회로 확대 → 회로 위에 표시하며 설명 → 풀이로 이동하여 작성 → 표시가 남은 회로로 복귀하는 흐름을 만든다. 회로뿐 아니라 상단의 표·보충 그림을 지원한다. 기존 카메라 흐름에 새 주석 렌더러와 공통 연필 제어를 연결하는 작은 architectural 확장이다. 두 기능이 같은 좌표·타이밍을 사용하므로 하나의 계획으로 구현한다.

처음에는 화살표, 타원/동그라미, 밑줄, 짧은 기호를 지원한다. 실제 손글씨 획순, 회로 소자·배선 변경, 긴 유도식/새 계산, 음성 의미 자동 감지, 학생의 실시간 필기, 회로 상시 썸네일, 기존 영상 일괄 재제작은 제외한다.

## 완료 시 동작

| 설명 | 화면 |
|---|---|
| 저항의 전류 방향 설명 | 회로로 이동한 뒤 화살표를 그림 |
| 노드 전압을 v_x로 명명 | 노드 옆에 본문 v와 첨자 x를 점진 공개 |
| 관계식 작성 | 연필을 숨기고 풀이로 복귀한 뒤 PDF 원문 작성 |
| 앞의 노드 재참조 | 같은 회로에 누적 주석이 남아 있음 |
| 모든 설명·작성 종료 | 주석·연필을 숨기고 원본 답안 전체를 hold |

포커스는 설명 의미에 맞춰 제작 에이전트가 지정한다. 매 풀이 단계마다 기계적으로 왕복하지 않는다. 작성 중에는 카메라를 고정하고 이동 중에는 연필을 숨긴다. 원본 풀이의 기존 글자 추적 이동은 보존한다. 그림이 없거나 연출 파일이 없으면 기존 동작이다. 복수 그림은 영역별로 지정하며 전체 관계를 설명할 때는 하나의 묶음 영역을 저작한다.

## 접근 결정

| 옵션 | 접근 | 장점 | 한계 | 선택 |
|---|---|---|---|---|
| A | 원본 위에 별도 SVG 주석 그룹 | 원본 보존, 확대와 함께 이동, 선명한 경로 | 주석 타이밍과 검증 추가 | 선택 |
| B | 이미지에 주석 합성 | 완성 이미지 처리 단순 | 부분 공개·되감기 제어 번거로움 | 제외 |
| C | 주석을 넣은 PDF 재생성 | PDF 배치로 통합 | 원본과 추가 설명 구분 어려움 | 제외 |

## Global Constraints

- PDF 답안의 문장·기호·수치·순서·줄바꿈·윤곽을 보존하며 완성 화면은 원본과 같아야 한다. 재조판·원본 이미지 교체로 결함을 숨기지 않는다.
- 1920×1080 / 30fps / mono PCM 24kHz를 유지한다. PDF 전체의 기존 16:9 또는 legacy 배치를 유지하고 자막 예약 영역은 하단 180px다.
- 원본 풀이 작성 본문은 화면상 최소 26px, 기존 연필 기본 길이는 160px, 기울기는 최대 ±2°다. 연필 전체는 1920×900 안에 있어야 한다.
- 전환 기본은 12프레임(0.4초), 작성 후 확인 시간은 최소 30프레임(1초), 주석 대상 간 연필 이동은 8프레임이다.
- 주석 도형 기본 작성 시간은 18프레임(0.6초), 명시적 시간도 18프레임 이상이다. 주석 글자는 초당 최대 5글자(글자당 6프레임: 이동 1 + 공개 5)다.
- 주석 기본 색은 #1565C0, 도형 선 두께는 화면상 3px다. 원본 기호를 덮지 않도록 실제 PDF에서 위치와 의미를 검토한다.
- 주석은 최종 전체 화면 직전까지 누적 유지한다. 명시적 hide_at을 지정한 주석만 더 일찍 숨긴다.
- TTS 공급자·모델·Aoede 설정은 유지한다. retime과 개발 검증은 유료 호출 0이며 fake PCM을 production 게시/실제 음성 검토로 승인하지 않는다.
- 자동 전역 설치·CLI 업그레이드를 하지 않는다. 실행 시 로컬 의존성 경로를 확인하고 누락은 명시적으로 보고한다.
- 기존 production 영상·PDF·노트·ec2-review-video 코드는 수정하지 않는다. 해당 스킬의 기존 로컬 글꼴만 읽기 전용으로 재사용한다.
- 구현 커밋은 사용자 커밋 권한이 있을 때만 수행한다. push/merge는 별도 명시 요청이 있어야 한다.

## 데이터 계약

두 파일 모두 선택적이다. annotations.json만 있거나 잘못된 파일이 있으면 기존 모드로 조용히 대체하지 않고 실패한다. focus.json만 있으면 주석 없는 포커스 이동을 지원한다. 파일이 모두 없거나 두 목록이 비었으면 기존 타임라인과 동작을 유지한다.

`source/focus.json`:

```json
{
  "schema_version": 1,
  "source_sha256": "답안 PDF 해시",
  "regions": [{"id": "main_circuit", "bbox": [100, 60, 500, 190]}],
  "cues": [{"segment_id": "explain_connection", "target": "main_circuit"}]
}
```

`source/annotations.json`:

```json
{
  "schema_version": 1,
  "source_sha256": "답안 PDF 해시",
  "items": [{
    "id": "current_arrow",
    "region_id": "main_circuit",
    "segment_id": "explain_connection",
    "kind": "arrow",
    "geometry": {"from": [210, 100], "to": [210, 150]},
    "source_refs": ["answer:2"],
    "meaning_notes": "원문의 기준 전류 방향을 표시한다."
  }]
}
```

좌표는 예시다. 실제 PDF point 좌표로 작성한다. ID는 영문으로 시작하는 ASCII 안전 문자열이며 목록 내 중복을 허용하지 않는다. source_sha256은 layers.metadata.source_sha256과 일치해야 한다. region은 양의 면적이며 페이지 안에 있고 work_bbox와 겹치지 않는 상단 그림 영역이다. geometry와 새 기호는 region 밖으로 일부 확장할 수 있으나 페이지 안에 있고 work_bbox와 겹치면 안 된다. 확장 부분은 포커스 계산에 포함한다.

cue는 reason 또는 check segment 하나에 한 개이며 segment ID/target이 실제로 존재해야 한다. focus가 활성인 실행에서 manifest.cameras와 혼용하면 충돌 오류다. 주석은 같은 segment와 region의 cue가 반드시 있어야 한다. 원문에 없는 새 계산은 허용하지 않으며 source_refs와 meaning_notes를 실제 자료에 대조한다.

지원 geometry:

- arrow, underline: `{from:[x,y],to:[x,y]}`. 길이 0은 오류. arrow는 shaft를 그리고 끝에서 머리 두 선을 순서대로 그린다.
- ellipse: `{bbox:[x0,y0,x1,y1]}`. 양의 면적. 시계 방향이며 위쪽 중앙에서 시작한다.
- label: `{runs:[{text:"v",origin:[x,y],font_size_pt:12},{text:"x",origin:[x,y],font_size_pt:8}]}`. origin은 baseline 좌표. run 순서가 공개 순서이며 첨자를 작은 별도 run으로 지정한다. 전체 비공백 글자는 최대 24개, 줄바꿈/LaTeX/제어 문자는 불허하고 글꼴에 없는 문자는 명시적으로 실패한다. 공백은 필기 없이 6프레임을 소비한다.

옵션: color는 #RRGGBB 형식이며 기본값 사용, offset_frames는 연필 이동 시작의 segment 상대 프레임(12 이상), 도형의 duration_frames는 18 이상, hide_at은 `"final"` 또는 `{segment_id,offset_frames}`다. 숨김 시점은 작성 완료 이후이며 final보다 늦을 수 없다. label에 duration_frames를 지정하면 속도 계약과 충돌하므로 오류다.

주석 순서는 segment의 manifest 순서와 items 목록 순서를 따른다. offset 생략 시 첫 이동은 frame 12, 다음 주석 이동은 이전 주석 작성 종료 직후다. 명시적 offset이 이전 작성과 겹치거나 순서를 뒤집으면 오류다. 타이밍 숫자는 bool이 아닌 정수이며 좌표/크기는 유한수다.

## 시간과 카메라

저장된 WAV의 실측 샘플 수로 segment 길이를 구한다. cue가 있는 설명 구간은 `max(음성 프레임 수, 마지막 주석 완료 프레임 + 30 + 12)`로 늘린다. 주석이 없으면 12 + 30 + 12 = 54프레임을 확보한다. 추가 시간은 segment 뒤의 무음이다. 음성은 segment 시작에서 재생하며 진입 12프레임과 겹칠 수 있다. 단어별 동기화를 주장하지 않는다. 이후 segment, 글자/도형 완료 이벤트, writing_spans, 최종 hold를 같은 시간 축으로 이동한다.

공통 cameraAt(frame)은 이전 viewbox에서 새 viewbox로 12프레임 동안 `u*u*(3-2*u)`로 보간한다. 키는 `{at_frame,viewbox,transition_frames?,mirror?}`이며 at_frame은 전환 시작이다. 기존 키는 transition_frames=0이다. 중복 키는 마지막 적용 상태 하나로 정규화하고 전환 구간끼리 겹치면 실패한다.

그림 cue 진입은 segment 시작, 복귀는 segment 종료 12프레임 전이다. 복귀 목적지는 다음 write의 첫 move 시작 시 카메라(pencil) 또는 첫 글자 공개 시 카메라(typing)다. 복귀 완료부터 첫 작성까지 목적지 카메라를 유지한다. 다음 write가 없으면 전체 페이지다. 처음 problem 페이지에는 새 주석을 보이지 않는다. 최종 hold 시작에서 전체 페이지와 주석 숨김을 적용한다.

현재 그림 + 현재 구간에서 새로 그릴 주석 + 이미 표시되어 있고 같은 region에 속하는 주석의 bounds를 합친다. 중요한 원본 이름·수치를 영역에서 빠뜨리지 않는다. 선 두께 여백, label 본문 최소 26px 및 연필 envelope를 포함해 1920×900에 맞춘다. 모든 조건을 함께 충족할 수 없으면 해당 region/주석 ID와 가독성·경계 충돌 이유를 보고한다. 잘라내기·필기 과속으로 해결하지 않는다. 작성 중 카메라를 바꾸지 않으며 mirror는 주석 오브젝트 시작에서 정하고 그리는 동안 고정한다.

## 주석 표시와 공통 연필

답안 SVG에 `g#teaching-annotations`를 추가한다. 원본 SVG 파일은 보존하고 조립본에만 그룹을 추가한다. 경로와 글자는 PDF 좌표로 배치되어 viewBox를 공유한다. 도형은 경로 길이로 점진 공개하며 촉은 공개 경로 끝을 따라간다. label은 로컬 Pretendard-Bold.ttf로 만든 SVG 윤곽을 글자별로 왼쪽→오른쪽 공개한다. 임시 PDF/SVG는 제작자료 안에서만 만들고 글꼴 해시와 완성 label bbox를 동결한다.

원본 풀이 렌더러와 주석 렌더러는 각각 화면 좌표의 PenState를 반환한다. player의 공통 연필 제어부가 한 번만 적용한다. 원본 풀이 작성과 주석 작성이 겹치면 실패한다. 이동/설명/완료에서는 해당 작성 span이 있을 때만 연필이 나타난다. typing 풀이에서도 주석에는 동일한 연필 asset을 사용한다. PNG 누락·손상은 실패이며 대체하지 않는다.

프레임은 유일한 시계다. 매 호출에서 모든 주석의 공개/부분/완료/숨김 상태를 재구성한다. 과거 호출 누적, 실제 시간, setTimeout, 랜덤에 의존하지 않는다.

## 재개와 검증

연출의 시간 지문은 cue/segment 연결, offset, 길이, label 공개 단위 수, hide_at을 포함하고 좌표·색·font_size·source_refs·meaning_notes는 포함하지 않는다. 시간 변경은 timing부터, 시각 변경은 composition부터 재개한다. 두 파일의 추가/삭제도 지문에 반영한다. 기존 script/voice 지문과 WAV는 연출 파일만 바꿀 때 유지한다. 변경된 module/asset/font 해시도 해당 단계 지문에 포함한다.

현재 source/timeline의 core 및 teaching schedule을 현재 입력에서 독립 재생성해 비교한다. 실제 composition의 camera와 주석 geometry/연필 상태도 검사한다. camera만 빼고 비교하는 현행 방식에 주석 schedule을 무조건 제외해 결함을 감추지 않는다.

원본 gate는 변경하지 않는다. 주석을 숨긴 조립본은 각 표본 프레임에서 원본의 동일 공개 상태와 비교한다. 별도로 도형 경로/label 윤곽의 독립 기준, 누적/명시 숨김, camera 이동, 촉 오차 ≤1px, 연필 길이 160px±0.5, 전체 경계, 임의/GSAP seek를 검사한다. 누락 주석, 촉 위치 변조, 미래 주석 선공개, 최종 hold 주석 잔류는 verify 실패다.

브라우저 증거와 해시를 verification/teaching.json 및 teaching-frames에 저장한다. 최종 하드 자막 MP4의 전체 디코드, 프레임/샘플 동기, 자막 영역, 실제 설명과 표기의 의미·방향·단위를 검토한다. fake PCM 개발 테스트는 production 검증 완료로 보고하지 않는다.

대표 실자료는 1002 E10.11, E10.13(문제/답안 회로 크기 차이), 2021-1_중간-Q3(긴 2단 풀이)다. 표·복수 그림·그림 없음·가장자리 주석은 synthetic fixture로 보완한다.

## 근거와 결정

- `workbook/templates/answer.html:575`: 상단 figure band와 아래 solutionArea를 구분한다.
- `scripts/solution_video/pdf_pages.py:58`(ec2-solution-video): writing은 work_bbox 안의 원본만 처리한다.
- `assets/writing.js:47`: 현행 연필은 glyph 공개 경계를 따라가므로 새 path 작성과 공통 제어가 필요하다.
- `scripts/solution_video/reveal.py:41`, `media.py:34`, `subtitles.py:21`: segment의 start/end sample을 공유해 추가 무음을 전체 타이밍으로 반영할 수 있다.
- `scripts/solution_video/state.py:15`, `verify.py:43`: 누적 stage 지문과 expected timeline 검사를 확장해야 한다.
- 2026-10-07 읽기 전용 확인: 로컬 Pretendard-Bold.ttf가 v/x/o/i/숫자/+ /−/α/β/한글 글리프를 가진다. 새 outline exporter와 렌더 충실도는 구현 시 검증한다.

이전 #1–6의 의미 기반 cue·PDF 좌표·필기 전 복귀·0.4초 전환·연출 분리·legacy 호환을 유지한다. #7은 주 화면만 번갈아 이동 [기본 확정]. 추가 #0=A, #8=기본 도형/짧은 기호, #9=PDF 좌표, #10=공통 연필, #11=작성과 이동 분리, #12=무음 연장/WAV 재사용, #13=원본/주석 별도 검증. #14는 최종 직전까지 누적 유지 [기본 확정].
