# 연필 필기 기능 검증 기록

Native 실행, 관리 워크트리 `ec2-pencil-writing`, 브랜치 `codex/ec2-pencil-writing`. 시작 HEAD는 757fa08이다. 구현·독립 리뷰 당시 변경은 미커밋으로 관리했다. 이후 사용자가 `codex/ec2-solution-video`로 로컬 통합을 선택했다. PDF·기존 영상·ec2-review-video는 변경하지 않는다.

## 구현

원본 SVG 글자에 별도 wrapper/clip을 적용하고 한 장의 PNG를 촉 중심으로 이동·회전·반전한다. 연필은 화면상 160px, 기울기는 ±2°, 신규 기본 최대 5글자/초다. 줄바꿈/단계 이동을 별도 span으로 기록하고 설명/hold/공백에서 숨긴다. PNG/metadata는 실행에 동결하고 검사한다. 글자 윤곽의 왼쪽→오른쪽 공개이며 실제 획순 복원은 아니다.

prepare의 typing 선택과 작성 파일이 없는 legacy 실행을 보존한다. retime은 현재 내용/voice 선행 상태 및 PCM 해시·샘플·형식 확인 후 무료로 timeline을 다시 만든다. 작성 속도/이동/hold는 timing, 크기/각도/PNG/metadata는 composition부터 재개한다.

로컬 실행 버전: Python 3.14.8 / Node 26.4.0 / PyMuPDF 1.27.2.3 / Pillow 12.2.0 / HyperFrames 0.8.137 / FFmpeg 9.0.2(libass). 전역 설치·CLI 업그레이드 없이 기존 런타임을 사용했다.

## 코드 검증

- `EC2_ACCEPTANCE_BATCH=<최종 수용 batch> python3 -m unittest discover -s .agents/skills/ec2-solution-video/tests -v`: 70개 모두 PASS, SKIP 0. 실제 수용 batch가 없으면 미디어 수용 1개가 SKIP된다.
- `node --test .agents/skills/ec2-solution-video/tests/test_writing_runtime.cjs`: 1 PASS.
- `git diff --check`: PASS.
- 기존 baseline은 41개, 40 PASS/1 SKIP. PyMuPDF SWIG 및 Pillow getdata deprecation warning은 기존에도 있었다.
- RED→GREEN: 새 설정/타이밍/renderer/retime/지문/verify 게이트, 실제 HTML의 누출·촉 위치·잔상 변조, 빈 source/HTML timeline, metadata alpha bounds, 수동 카메라/반전, GSAP의 66.999999 프레임 반올림.
- source timeline을 manifest/측정 PCM으로 다시 계산하고 HTML timeline과 대조한다. 직접 렌더뿐 아니라 실제 GSAP 시간 seek도 같은 snapshot이어야 한다.

## Asset

PNG SHA256: `8f09ff6af2689c9cb50bab4382c4d18a46639312ea8d2edf42ad82c774d20269`.
프롬프트 SHA256: `3e53589ff655a4e59ce2186f2b8eccf762b723475919c0f531925ce357f5840e`.
1254×1254 RGBA를 보존했다. tip_px=[114,1171], end_px=[1110,107]. 원본 해상도에서 촉 marker를 직접 확인했다.

## 미디어

짧은 한글·첨자·분수·줄바꿈 샘플은 `.superpowers/sdd/2026-10-07-ec2-pencil-writing/샘플_제작자료/renders/final.mp4`, 124프레임/4.133초다. HyperFrames check/render, libass 자막, 전체 디코드, 1920×1080/30fps/24kHz, A/V 차이<=1프레임을 확인했다. SHA256 `faf317ec9f0f9bad967b0c2a0f884477ee055370dc31304c3af53f36cade96a7`.

최종 E10.11은 `.superpowers/sdd/2026-10-07-ec2-pencil-writing/최종샘플_제작자료/문제풀이영상/1002/1002_제작자료/실행/20261007-021817-3534bc29/videos/problem-21acd093fe13/renders/final.mp4`다. 2890프레임/96.333초, SHA256 `12636c3afb44ecadaae18aa1c02f70480248eed0d2f598352d6ff28c3bb8c51d`.

`acceptance.py --dest <최종샘플_제작자료> --hyperframes-entry <로컬 HyperFrames/bin/hyperframes.mjs> --problems E10.11`: 실제 original/partial/precomplete/complete, direct·GSAP seek, bounds/order/샘플/해시/자막/전체 디코드 PASS. 촉 오차 최대 0.0049964px, 모든 diff=0, final_visible=false. 유료 호출 0, live_audio=unverified, production_publish_blocked=true. verification/writing-frames에 528개 PNG 증거를 저장했다.

원본 native PNG와 MP4의 시작/첫 작성/중간/긴 이동/최종 hold를 직접 확인했다. 현재 글자는 읽을 수 있고 연필이 촉 경계를 따라가며 자막 영역을 침범하지 않는다. 마지막은 원본 배치를 복구하고 연필이 사라진다. 작성 중 확대는 주변 문장을 화면 밖으로 보낼 수 있으며 현재 글자의 가독성과 원본 좌표를 우선한다. 최종 수용 batch를 EC2_ACCEPTANCE_BATCH에 지정한 suite를 실행해 실제 저장 미디어도 확인한다.

현재 wide PDF의 대표 세 문항 map을 native 화면에 대조해 갱신했다. 세 문항 모두 extract/content 검사 PASS이고 실제 MP4 수용 렌더는 E10.11만 수행한다. 입력 PDF와 ec2-review-video 파일의 해시 보존을 수용 runner에서 확인한다.

개발용 무음 PCM으로 실제 Aoede 음성 품질·발음·청취를 확인하지 않았다. complete=false이며 production 게시하지 않는다.

## 독립 리뷰

executing-plans의 최종 전체 리뷰 규칙에 따라 gpt-6-astra 독립 리뷰어에게 읽기 전용으로 전체 변경을 전달했다. Critical 0 / Important 1 / Minor 0. 리뷰어가 임시 fixture에서 길이 120px/기울기 0° 변경 후 composition부터 재개해도 기존 160px/2°가 남는 문제를 재현했다. 독립 Python 67 PASS/1 SKIP, Node 1 PASS, diff check PASS.

두 회귀 테스트에서 먼저 160!=120 및 writing_animation=unverified 실패를 확인했다. 현재 설정의 시각 값은 조립에 다시 동결하고, 타이밍 projection은 state/assemble/verify가 공유하도록 수정했다. source/timeline.json·voice/timing stage 기록·audio.json·WAV 해시를 보존하며 CLI assemble paid_requests=0도 검사한다. 실제 browser writing gate는 원문/PCM으로 재계산한 현재 설정과 비교한다. 타이밍 값이 바뀌면 assemble 전에 retime을 요구한다.

실제 Aoede 청취는 리뷰 범위 밖으로 분리했다. 이 판단은 승인된 무료 개발 검증 범위에 따른 것이며 실제 음성 승인 전에는 게시가 계속 차단된다. 두 회귀 RED→GREEN, 최종 Python 70/70 PASS·Node 1/1 PASS·diff check PASS를 확인했다. 수정 후 기존 E10.11 MP4의 원본/연필/HyperFrames/최종 미디어/자막 게이트도 다시 PASS했다. 기본 160px/2°의 출력 동작은 같아 긴 MP4를 추가 재인코딩하지 않았다. 재리뷰는 추가하지 않았으며 미룬 Minor는 없다.

## 실행 중 판단과 보존

- 커밋 권한이 없어 미커밋으로 보존했다. 커밋 기록 대신 작업 diff와 ledger를 유지한다.
- 기존 A4 수용 좌표를 현재 와이드 native PDF로 갱신했다. PDF 배치가 다시 바뀌면 fixture 좌표를 재검토해야 한다.
- commit-range 전용 review-package는 빈 범위를 지원하지 않아 `git diff 757fa08`와 모든 신규 소스를 묶어 독립 검토했다. 통합 전까지 ledger와 자료를 보존한다.
- 실제 Aoede 청취는 승인된 무료 개발 검증 범위에서 제외했다. production 사용 전 실제 음성 검토가 필요하다.

사용자가 로컬 병합을 승인해 이 기능을 하나의 커밋으로 통합한다. 기존 미커밋 asset/spec/plan은 원래 체크아웃의 `.superpowers/merge-backups/`에 보존한다. 샘플·ledger·검증 자료는 호스트가 관리하는 `/Users/hyunjun_macbook_pro/.codex/worktrees/ec2-pencil-writing/전자회로2`에 유지하며 이 문서의 `.superpowers/sdd/` 상대 경로는 그 워크트리 기준이다. 원격 푸시와 production 게시는 이 선택의 범위에 포함하지 않는다.
