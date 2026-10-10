# 나레이션에 맞춘 회로 필기 보강 설계

## 의도와 범위
현재 P10.72 영상의 기존 회로 설명 3곳을 연결·전류 방향·변화량의 순서로 필기하며 설명한다. 기존 주석·카메라·펜 기능을 확장하는 bounded 변경이다. 중앙 원본 풀이, 공개 속도, 나레이션, 자막 내용은 유지한다. 자유곡선 손글씨는 추가하지 않는다.

## 결정
1. 실측 PCM 음성 청크에 주석을 연결한다.
2. 도형별 stroke_width_px는 유한한 숫자 2~12px를 지원한다. boolean/string/NaN/infinity는 거부한다. 기존 생략값은 3px, 새 영상은 4px 보조 표시·6px 전류 화살표·8px 핵심 강조를 명시한다.
3. 파랑 #1565C0은 연결/거울 관계, 주황 #C45100은 M4 출력 유입, 초록 #237A43은 I2 가지, 자주 #8E348E는 RL 결과다. 색과 함께 기호/위치로도 대상을 구분한다.
4. 설명 안에서는 관련 주석을 누적하고 중앙 풀이 복귀 때 숨긴다. 마지막 전체 화면은 원본 답안이다.
5. 원본 회로·풀이·WAV를 보존한다. 추가 필기 때문에 긴 무음을 넣지 않는다.
6. 필기 밀도는 핵심 화살표+짧은 기호로 confirmed by default다. 사용자가 writing-plans를 호출하며 별도 변경값을 주지 않았다.
실행 방식은 이전에 명시한 native를 유지하되 계획 검토를 받은 후 구현한다.

## 주석 계약
annotations.json schema_version=1에 도형별 stroke_width_px와 선택적 chunk_id를 추가한다. 기존 color 필드를 사용한다. label에는 stroke_width_px를 허용하지 않고 runs의 font_size_pt와 color를 사용한다.
chunk_id는 해당 segment의 실제 manifest chunk id다. 지정하면 offset_frames는 청크 시작 기준이며 생략값 0, 정수 >=0이다. 기존 chunk_id 없는 주석의 offset_frames는 segment 기준, 기존 생략/순차 배치/최소12프레임 계약을 유지한다. 같은 segment 안에 두 타이밍 모드를 혼합하면 저작 오류다. 같은 chunk 안에는 저작 순서와 겹치지 않는 offset을 명시한다. 서로 다른 chunk의 offset을 단순 비교하지 않는다.
해당 reason/check segment와 focus region 연결, source_refs, meaning_notes, label 24자 제한은 유지한다. 다른 segment의 chunk, 없는 chunk, legacy manifest의 chunk 지정은 check 단계에서 거부한다.

## 실측 스케줄
30fps/24kHz에서 1프레임=800샘플이다. 청크 start_sample의 ceil(frame)에 offset_frames를 더한 move 시작점을 사용한다. 첫 청크는 segment 시작+12프레임 카메라 이동 종료보다 빠르게 시작하지 않는다. move는8프레임, 도형 draw는 기존 duration_frames(최소18), label은 기존 글자당6프레임이다.
완료는 min(floor(chunk.end_sample/800), segment.end_frame-13) 이내다. 마지막12프레임 복귀 이동 전 최소1프레임의 완성된 근거 화면을 확보한다. 실제 move/draw/space 전체 구간의 중첩, 청크 초과, 숨김이 완료보다 빠른 경우를 거부하며 annotation id와 segment/chunk id를 오류에 담는다. chunk 주석을 위한 추가 silence padding은 만들지 않는다. 기존 focus-only/legacy 최소 길이 동작은 보존한다.
기존 hide_at은 segment 기준 계약을 유지한다. 이번 영상은 해당 reason 다음 write 시작(offset_frames=0)에 숨긴다.

## P10.72 저작
| 구간 | 청크별 표시 |
|---|---|
| reason_0 cue1 | M3 게이트–드레인 연결에 파랑 강조 |
| reason_0 cue2 | 공통 게이트 연결에 파랑 밑줄/화살표 |
| reason_0 cue3 | M3/M4 크기 관계를 짧은 기호로 표시 |
| reason_0 cue4 | M4 유입, I2 가지, RL 가지의 방향 화살표와 짧은 기호 |
| reason_1 cue1 | 같은 크기 1:1 표시 |
| reason_1 cue2 | M4 유입 변화 +ΔI |
| reason_1 cue3 | I2 변화 −ΔI, 전류 화살표 방향은 유지 |
| reason_1 cue4 | RL 변화 2ΔI |
| reason_2 cue1 | 크기 비 2:1 표시 |
| reason_2 cue2 | 거울 비 1/2와 M4 변화 +ΔI/2 |
| reason_2 cue3 | 출력에서 I2를 빼는 두 가지 경로 표시 |
| reason_2 cue4 | I2 변화 −ΔI와 RL 결과 3ΔI/2 |
숫자/기호는 PDF·동결 MD에서 대조한다. 전류 감소를 전류 방향 반전으로 그리지 않는다. 화살표 방향/소자 크기 순서를 원본과 확인한다. text-as-path label의 첨자는 별도 작은 run으로 저작한다.

## 화면/검증
화면상 선 굵기는 카메라 확대와 무관하게 일정하다. 주석 전체 경로, 화살촉, stroke 반경, 펜 여백을 포함한 카메라 경계 검증을 한다. 원본 배선·소자명은 덮지 않고 label은 주변 여백에 둔다. label의 기존 화면상26px 최소 가독성을 유지한다. 동일 시간의 순차 재생/임의 seek 결과가 같다.
12개 청크별 원문 근거·발화·주석 대응을 검토한다. 단순 타원 반복은 대응 근거로 인정하지 않는다. 스킬 지침에 이 저작 기준과 굵기·청크 계약을 반영한다.
원본/연결 WAV66개 해시, 전체 프레임 수, segment 및 caption 경계를 변경 전후 비교한다. paid_requests=0. 실제 음성을 듣지 못하면 live_audio=unverified/complete=false로 검토본만 전달하고 publish/latest는 갱신하지 않는다.
