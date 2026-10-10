# 전자회로2 문제풀이 영상 렌더 성능 설정

## 의도와 범위

검증된 캡처 작업자 6개 설정을 `ec2-solution-video`의 신규 제작과 명시적인 재렌더에 적용한다. 성능 설정 변경은 렌더 이후 단계만 갱신하며 기존 음성·대본·타임라인을 보존한다. 기존 흐름 수정(bounded)이다.

`grill-yourself`의 결정 #1은 문제풀이 영상 먼저 적용으로 confirmed by default다. 사용자가 다음 단계로 writing-plans를 요청했고 범위를 바꾸지 않았다. 개념 복습 영상은 독립된 장면 렌더/동시 실행 구조여서 별도 검증·계획으로 다룬다. 이 문서는 채팅 설계를 구현 계획과 함께 전달하기 위한 저장본이다.

## 현재 근거

- 계획 조사 시 체크아웃: `main`, HEAD `345a88e`. 실행 시 다시 확인한다.
- `scripts/solution_video/media.py:22-48`: 각 파트를 순차 처리하며 HyperFrames 캡처 작업자가 2개로 고정되어 있다. 마스터 mux는 임시 출력 후 교체하지만 파트는 최종 경로에 직접 쓴다.
- `scripts/solution_video/state.py:7-25`: `source/config.json`은 voice 단계 입력이며 media 모듈은 render부터 지문에 포함된다. util/contracts 같은 공통 모듈 변경은 앞 단계까지 영향을 준다.
- 현재 구성과 벤치마크 원래 RUN의 도구 지문은 같다고 가정하지 않는다. 벤치마크 RUN의 승인/단계 영수증을 복사해 유효하게 만들지 않는다.
- 근거 폴더: `문제풀이영상/1007/1007_제작자료/성능시험/20261010-205141/`. 전체 P10.72 7,220프레임에서 2개 평균 176.64초, 6개 평균 85.10초. CPU 인코딩 결과 5개의 파일/전체 프레임이 동일했다.
- GPU 인코딩 옵션은 더 느렸고, 실험적 고속 캡처는 화면 정확도 검사에 실패해 일반 캡처로 복귀했다. 이 결과는 단일 문항·현재 맥의 결과다.

## Global Constraints

- 적용 대상은 ec2-solution-video만이며 ec2-review-video 코드와 출력은 변경하지 않는다.
- 신규 RUN 기본값은 Darwin / Apple M5 / CPU 10코어 / 메모리 16GiB 이상에서 작업자 6개이며, 다른 환경이나 탐지 실패에서는 기존 2개다.
- 렌더 작업자 수는 정수 1–6이며 bool, 실수, 문자열 JSON 값, 범위 밖 값은 거부한다.
- CPU 인코딩과 브라우저 GPU auto를 유지하며 experimental-fast-capture=false를 명시한다.
- 1920×1080, 30fps, 기존 PCM mono 24kHz, 기존 자막 인코딩·폰트·배치 설정을 유지한다.
- 렌더 옵션은 source/render-options.json에 저장하며 source/config.json·대본·음성·타임라인을 변경하지 않는다.
- 파트와 문항은 순차 렌더하며 문항 내부의 캡처 작업자만 늘린다.
- 실패 시 기존 파트·마스터·최종 영상과 검증 영수증을 보존하고, GPU·음성 공급자·작업자 수를 자동 대체하지 않는다.
- 신규 패키지 설치·전역 설정 변경·유료 API 호출·기존 완성 영상 일괄 재생성·자동 게시를 하지 않는다.

## 렌더 옵션 계약

```json
{"schema_version":1,"workers":6,"encoder":"cpu","browser_gpu":"auto","fast_capture":false}
```

키는 이 다섯 개만 허용한다. schema_version은 정수 1, encoder/browser_gpu/fast_capture는 위 값으로 고정한다. 기본 탐지는 Darwin에서 sysctl의 machdep.cpu.brand_string, hw.physicalcpu, hw.memsize를 읽는다. 탐지 실패는 기본 2개로 처리하며 런타임 벤치마크를 하지 않는다.

우선순위는 CLI `--render-workers` → 저장된 유효 옵션 → 현재 호스트 기본값이다. 저장된 옵션은 호스트가 바뀌어도 유지한다. 호스트 기본값은 신규 RUN과 옵션 파일이 없는 RUN에만 적용한다. 손상된 파일은 기본값으로 숨기지 않고 오류를 낸다.

prepare는 별도 옵션 파일을 생성한다. render는 옵션을 검증한 뒤 기존 단계 재개 검사 전에 atomic write로 저장한다. resume-set 자체는 이전 RUN에 옵션을 쓰지 않는다. 옵션/정책 모듈을 render 지문에만 등록하고, 음성·조립까지의 지문 계산을 바꾸지 않는다.

## 실행과 기록

render_master의 기존 다섯 위치 인자는 유지하고 선택적 keyword-only render_options를 추가한다. 전달하지 않은 직접 호출은 옵션 파일/호스트 기본값을 읽는다. CLI render만 수동 조절 옵션을 받는다.

파트는 `<key>.pending.mp4`에 렌더한다. 실행 성공과 1920×1080/30fps/예상 프레임 검사를 통과한 뒤 기존 `<key>.mp4`와 교체한다. 마스터도 pending 출력의 영상 규격·총 프레임·오디오 mono 24kHz를 검사한 후 교체한다. 실패한 임시 파일은 제거하고 실패 로그를 보존한다. 앞서 성공한 파트는 보존한다.

`verification/render-receipt.json`에는 schema_version=1, 선택된 options, 파트별 key/실제 command/elapsed_seconds/output_sha256/frames, 마스터 SHA256을 기록한다. 마스터와 영수증은 모두 pending 상태로 준비한 뒤 이전 파일의 복구용 사본을 확보하고 교체한다. 영수증 쓰기나 두 파일 교체 중 실패하면 이전 마스터·영수증을 복구한다. command는 실제 절대 경로 인자 목록이며 비밀이나 환경변수 전체를 기록하지 않는다. render 단계 출력 영수증에는 master와 render-receipt를 함께 등록한다. 기존 시간·내용 검토 승인 절차는 유지하며 새 입력 지문에 이전 리뷰를 억지로 맞추지 않는다.

## 완료 기준과 제외 범위

옵션 없는 이전 RUN의 읽기, 잘못된 옵션의 사전 차단, 작업자 변경 후 render부터의 재개, 기존 WAV 해시 보존, 실패 시 이전 파일 보존을 검사한다. 구현된 CLI의 연결은 독립 회귀 테스트로 검증하고, 실제 P10.72의 동결 composition/PCM은 생산 render_master를 직접 호출하여 2/6개 출력의 모든 프레임을 비교한다. 현재 체크아웃과 과거 RUN의 상태 지문 차이를 피하기 위한 검증 분리이며 의미 검토/음성 승인을 우회하지 않는다.

복습 영상으로의 일반화, 새 글로벌 스케줄러/잠금, GPU 인코딩 선택 UI, 자막 캐시 재설계, 장면별 캐시 재설계는 이번 범위에 포함하지 않는다. 여러 채팅 간 실행 동시성은 자동 제어하지 않으며 스킬 문서에는 시험과 동일하게 한 번에 한 문항을 렌더하도록 안내한다.
