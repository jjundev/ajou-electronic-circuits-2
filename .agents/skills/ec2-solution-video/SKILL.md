---
name: ec2-solution-video
description: 전자회로2 복습문제의 문제지·답안 PDF 원본 화면을 사용하고 중앙 풀이를 한 글자씩 공개하는 한국어 문제풀이 영상을 만든다. 날짜·문항 ID·재개·대본 검토 요청 또는 /ec2-solution-video에 사용한다. 개념 복습 영상은 ec2-review-video를 사용한다.
---

# PDF 문제풀이 영상

문제지로 조건과 구할 것을 확인한 뒤, 중앙 풀이를 숨긴 답안 페이지의 **원래 위치**에서 풀이를 한 글자씩 공개한다. 답안의 문장·기호·수치·줄바꿈·순서를 그대로 유지한다. PDF 원본의 글자 윤곽을 사용하며 HTML/KaTeX로 다시 쓰지 않는다. 완성 화면은 원본 답안과 같아야 한다.

## 호출과 기본값

- `/ec2-solution-video 1002`: 해당 날짜 모든 문항, 문제별 MP4.
- `/ec2-solution-video 1002 --problems E10.11,P10.62`: 선택한 문항.
- `/ec2-solution-video 0923-1002 --review`: 범위 문항의 대본을 묶어 한 번 사용자 검토.
- `/ec2-solution-video 1002 --writing-mode typing`: 기존 타이핑 방식 선택. 신규 실행은 pencil이 기본이다.
- 재개 요청: 이전 batch의 `resume-set`으로 처음 무효인 단계를 확인한다.

한국어 Aoede / Vertex AI Express / gemini-2.5-flash-tts, 1920×1080/30fps, mono PCM 24kHz. 연필 작성 기본 초당 5글자 이하, 음성이 짧으면 작성 시간을 늘린다. 배경음·필기·타이핑 소리는 없음. 예산 상한 없음이며 요청 전체 사용량을 공용 ledger에 기록한다. 공급자·모델을 자동 대체하지 않는다.

연필 PNG 한 장을 촉 중심으로 움직이며 원본 윤곽을 왼쪽에서 오른쪽으로 공개한다. 실제 한글·수식 획순을 복원하는 연출은 아니다. 연필 길이는 촉부터 지우개 끝까지 화면상 160px이며 확대와 무관하다. 줄바꿈에서는 들어 옮기고 작성 완료·설명·최종 hold에서는 숨긴다. 분수선·근호선·단계 배경·답 상자는 기존 anchor 글자 완료 시점에 공개한다.

PDF 흰 화면과 회로·격자·조건·Hint를 보존한다. 기본 복습문제는 하단 180px를 비운 16:9 PDF다. PDF 전체를 1920×1080에 맞춘 뒤 예약 영역만 자막으로 덮는다. 1920×900에 다시 축소하지 않는다. 기존 A4 입력은 원본 비율을 유지해 호환한다. 새 PDF는 약 11.34pt 본문과 같은 비율로 조정한 제목·수식·힌트를 사용해 기존 A4 전체 화면의 텍스트 표시 크기를 유지한다. 영상에서 추가 글꼴 재조판 없이 그 PDF의 글자를 그대로 공개한다. 작성 중 작은 글자는 원래 배치 그대로 확대한다. 입력 문제지와 답안의 회로도 크기/페이지 번호를 독립적으로 확인한다. 긴 2단 풀이의 단계 순서를 사람이 검토한다.

## 실행

이 프로젝트에서 PyMuPDF와 Pillow가 있는 Python, Node, 로컬 GSAP/HyperFrames/puppeteer-core/Chrome, libass 포함 FFmpeg를 사용한다. 없는 패키지를 자동 전역 설치하지 않는다. `EC2_PUPPETEER_CORE_PACKAGE`는 package.json 절대 경로, `EC2_CHROME`, `EC2_FFMPEG`는 실행 파일 절대 경로로 지정할 수 있다. 현재 환경의 설치 경로는 매 실행 확인한다. Node CLI가 없으면 렌더를 검증 완료로 보고하지 않는다.

1. `python3 .agents/skills/ec2-solution-video/scripts/video.py prepare 1002 --repo "$PWD" [--problems ID,ID] [--review] [--writing-mode pencil|typing]`. 반환된 batch와 문항별 run을 사용한다. 원자료를 동결하며 비용은 0이다.
2. [PDF와 내용 대응](references/pdf-and-coverage.md)을 읽는다. 실제 문제/답안 PDF, 동결 workbook MD, 후보 SVG와 native PNG를 읽고 `source/map.json`을 작성한다. `extract --run RUN`으로 빈/부분/완성 프레임 게이트를 실행한다. native PDF와 원본 SVG도 직접 대조한다. 픽셀 비교 0만으로 의미 검토를 승인하지 않는다.
3. 원문과 일치하는 `manifest.json`, `coverage.json`, `circuit-review.json`을 작성하고 `check --run RUN`으로 검증한다. 한글 음절/조판 기호를 공개하며 첨자·분수선·근호선·답 상자를 누락하지 않는다. PDF/MD 충돌, 풀이 이미지, 해석할 수 없는 클립/도형은 해당 문항을 중단한다. 새 풀이·계산을 창작하거나 오류를 조용히 수정하지 않는다.
4. [음성과 실측 타이밍](references/narration-and-timing.md)을 읽는다. `tts --run RUN [--config JSON] [--env-file ENV]`를 실행한다. 최초 SVG 게이트와 현재 내용 검토 전에는 유료 요청을 하지 않는다. `--review`이면 전체 대본을 사용자에게 보여 주고 승인 후 한 번 `--approve-review`를 사용한다. 기본 모드에는 사용자 승인 단계를 추가하지 않는다.
5. `assemble --run RUN --runtime /ABS/gsap.min.js`, `render --run RUN --hyperframes-entry /ABS/hyperframes/dist/cli.js`, `captions --run RUN`을 차례로 실행한다. 모든 공개 상태가 임의 seek에도 같아야 하며 끝난 후 연필·커서를 숨긴다. 완성 오류를 마지막 원본 이미지 교체로 감추지 않는다.
6. [최종 검증과 게시](references/verification.md)를 읽는다. 최종 하드 자막 MP4의 재생·음성·가독성을 직접 검토하고 현재 증거 해시를 가진 audio/visual review를 작성한다. `verify --run RUN --hyperframes-entry /ABS/.../cli.js`를 통과한 문항만 `publish-set --batch BATCH`로 게시한다. 일부 실패 시 성공 결과/음성은 보존하고 전체 latest를 바꾸지 않는다.

작성 속도만 바꾸려면 `retime --run RUN [--writing-config JSON]`을 사용한다. 현재 내용 검증과 저장 WAV의 형식·해시를 확인하고 유료 음성 호출 없이 timeline을 다시 만든다. 이후 assemble/render/captions/verify를 재실행한다. `source/writing.json`이 없는 이전 실행은 기존 타이핑 설정으로 읽는다. PNG·metadata·촉 좌표가 누락되거나 손상되면 실패하며 타이핑으로 자동 전환하지 않는다.

모든 단계 명령은 위 `scripts/video.py`에 붙인다. JSON status가 author-required이면 필요한 원문 검토 파일을 작성한다. awaiting-review는 사용자 대본 승인 대기다. failed이면 명시된 단계의 증거를 읽고 원인을 수정한다. `resume-set --batch BATCH`는 캐시 파일을 삭제하지 않는다. 단계를 건너뛰어 오래된 음성/영상과 새 대본을 섞지 않는다.

## 출력

`문제풀이영상/<날짜 또는 범위>/<문항 ID — 자연스러운 한국어 제목>.mp4`에 최종 하드 자막본만 둔다. `_자막` 접미사를 쓰지 않는다. 소스·대본·SVG·HTML·WAV·마스터·자막·검증·사용량은 같은 날짜의 `<범위>_제작자료/실행/<실행ID>/videos/<안전한 키>/`에 둔다. 같은 제목의 이전 결과는 제작자료 안에 보존한다. catalog/README는 실제 최종 파일 SHA256을 기록하고 latest는 전체 성공일 때만 갱신한다.

기존 ec2-review-video·노트·PDF·영상을 수정하지 않는다. 그 스킬의 TTS/cache/budget만 이름이 격리된 adapter로 사용한다. 다크 전용 렌더/자막 검사는 사용하지 않는다. 스캔 완전 자동 처리, 손글씨, 실제 키보드 녹화, 음성만 교체하는 별도 기능은 제공하지 않는다. 전달 시 검증한 범위와 실제 음성 미검증 여부를 구분한다.
