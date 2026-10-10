# 복습 영상 렌더링 설정 적용

사용자가 승인한 문제풀이 영상 정책을 복습 영상 render와 revoice 재렌더 장면에 적용한다. Apple M5 / physical 10 cores / RAM >=16 GiB는 workers 6, 그 외는 2. CPU 인코딩, browser GPU auto, fast capture false, delivery 1080p30. 장면은 순차 실행한다.

source/render-options.json은 음성 config와 독립. CLI --render-workers 1..6 > 저장값 > host 기본값. 손상된 저장값은 override로 숨기지 않는다. 옵션/정책 코드 변경은 render 이후만 무효화. 기존 TTS/PCM/조립 결과 보존. 기존 backend probe 함수는 호환을 위해 유지하지만 CLI는 CPU 정책을 직접 사용한다.

장면 영수증에 실제 args/elapsed/options/hash/frames, cache hit는 재렌더 없이 보존. 실패/timeout은 이전 장면 MP4/영수증과 master 보존, stale pending 제거, 로그 보존. 1080p30/프레임 검사. 통합 영수증은 성공한 mux 이후 저장한다.

실제 성능시험은 기존 MOS 차동쌍 fixture를 실제 템플릿·GSAP·KaTeX·Pretendard로 조립한 60초, 2장면 1080p30 영상이다. 음성은 합성 PCM 시험 신호(유료 TTS 없음). workers 1/2/6 순차 실행, 프레임 전체 hash와 PCM/AAC 동일성 검사, representative PNG 직접 확인. 원본 0.6초 motion과 24초로 연장한 stress motion을 별도 시험하고 속도 개선/저하를 모두 보존한다. 실패하면 커밋/병합하지 않는다. 단일 fixture·장비의 측정임을 보고한다.

이번 skill 코드/테스트/설명/계획만 커밋. 시험 미디어는 제작자료 폴더, git에 넣지 않음. 기존 다른 변경 유지, main 로컬 병합, push 없음. HF 0.8.137, FFmpeg 9.0.2 유지해 기존 측정과 비교한다.

동적 실험의 초기 수식 프레임 차이를 보정: document.fonts.ready 이후 타임라인 구성/등록. 이전 RUN은 composition 코드 지문으로 한 번 reassemble 요구(음성 유지). 설정 변경 자체는 render 이후만 무효화한다.

최종 리뷰 반영: 장면·마스터 MP4/영수증을 쌍으로 준비 후 교체, 실패/KeyboardInterrupt 시 복구, 복구 실패 시 rollback 사본 유지·재시도 차단. 시간 초과 시 직계 및 분리 세션 자식 프로세스도 종료하고 직접 프로세스를 reap한 후 정리. 시도별 UUID pending으로 이전 시도와 경로 분리.
