# 렌더와 검증

Python 3.11+, Node, FFmpeg/ffprobe, 로컬 HyperFrames CLI Node entry가 필요하다. 자막 굽기는 libass subtitles filter가 있는 FFmpeg를 사용한다. HyperFrames entry는 해당 설치 package.json의 bin이 가리키는 실제 JS 파일이다. CLI에 --hyperframes-entry로 절대 경로를 넘긴다. 렌더 버전은 기록하고 이전 run의 도구/템플릿을 몰래 갱신하지 않는다.

기본 CLI는 문제풀이 영상과 같은 정책을 쓴다: Apple M5/물리 CPU10/RAM>=16GiB workers6, 그 외 workers2. CPU 인코딩, 브라우저 GPU auto, `--experimental-fast-capture=false`, delivery 1080p30. 장면은 순차 처리해 내부 작업자와 장면 병렬의 중복을 방지한다. `render`/`revoice --render-workers 1..6` > source/render-options.json > 장비 기본값. resume은 설정 파일을 새로 만들지 않는다. 설정 변경은 render 이후만 무효화한다. 실제 로그 확인 전 GPU 사용 성공으로 보고하지 않는다.

probe_backends는 기존 CPU/NVENC 진단용으로 유지되며 기본 CLI의 인코더 선택에 사용하지 않는다. 직접 render_parts를 부르는 기존 호출도 저장 정책 또는 장비 기본값으로 캡처한다. 장면 MP4 옆 JSON은 실제 args/elapsed_seconds/render_options/hash/frames를 기록한다. verification/render-receipt.json은 성공한 mux와 함께 render 단계의 검증 대상으로 등록한다. 재음성 영수증의 parts는 재렌더된 장면만 포함한다.

실제 성능시험: `PATH=/opt/homebrew/opt/ffmpeg-full/bin:$PATH HYPERFRAMES_FFMPEG_PATH=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg python3 tests/render_performance_acceptance.py --destination <새 절대경로> --hyperframes-entry <로컬 JS 절대경로>`. 기존 차동쌍 fixture의 60초/2장면을 workers1/2/6으로 실행하며 전체 frame hash·PCM·AAC·소스 hash·자막 굽기·전체 decode를 검사한다. 합성 PCM 시험 신호이며 실제 Aoede 발화 품질 또는 전체 제작 속도 검증은 아니다. 단일 장비·fixture 결과로 일반화하지 않는다. `--motion-duration 24`는 동작을 연장한 stress 시험이다. 정지 프레임이 대부분인 짧은 장면은 CLI의 정지 프레임 재사용 효과 때문에 workers6가 더 느릴 수 있으므로 workers2와 비교해 선택한다.

검증:
1. content: 전체 원문 항목 발견과 발화/문항 판별점 의미 대응 검토.
2. audio: PCM hash/무음/클리핑/길이 검사 + 핵심 수치 직접 청취 또는 예산에 포함한 전사. 표본 검사 범위를 명시.
3. visual: tests/browser_check.mjs로 모든 장면/테마/자막 경계 검사(장면 안 고정 자막은 없으므로 captionCount는 0이어야 한다) 후 스크린샷을 직접 검토. 템플릿 컴포넌트와 크기 변경만 다른지 비교.
4. source: HyperFrames check를 실제 편집 소스에 실행. timeout은 unverified. MP4 wrapper로 대체 금지.
5. media: ffprobe, 전체 decode, 1920×1080/30fps/mono24k/프레임/스트림.
6. sync: PCM 샘플과 문단 경계, 마지막 audio/video 시간 오차.

verification/reviews.json의 content/audio/visual은 {status,evidence:[run 내부 경로],errors:[],input_hash} 형식이다. input_hash는 verify 모드가 출력하는 현재 review_fingerprint 값이다. 마지막 산출물이 정해진 뒤 검토하고 기록한다. 오래된 검토는 통과하지 않는다. content와 audio의 의미 검토를 기계 성공으로 자동 승인하지 않는다.

node tests/browser_check.mjs RUN PUPPETEER_PACKAGE_JSON CHROME_EXE는 로컬 설치한 puppeteer-core와 Chrome 실행 파일을 사용한다. 각 인자는 절대 경로다. 화면 대표 PNG는 verification/frames에 저장한다.

완료 보고는 검증한 항목과 미확인 항목을 구분한다. report.complete일 때만 latest.json을 갱신한다. 실패 시 이전 최신 결과를 유지한다. 사용자가 명시한 예산이 소진되면 성공한 문단을 보존하고 사용자에게 예산/실패 사유를 알린다. --resume은 처음 미완료 단계부터 다시 수행한다.

하드 자막본은 마스터 검증과 `publish-set` 후 만든다. 굽기 결과가 `status: passed`이고 대표 프레임을 확인한 뒤 SKILL.md의 "자막 (고정)" 순서로 자막본만 원래 제목에 남기고 README·catalog의 경로·크기·SHA256을 갱신한다. 제작자료의 마스터 검증 지문·해시는 자막본에 맞춰 바꾸지 않는다. 재검증·목소리 교체·자막 재굽기 전에 마스터가 필요하면 해당 RUN에서 `render`로 재생성한다. 자막 위치·폰트는 SKILL.md의 "자막 (고정)" 설정을 따르고, 자막본의 대표 프레임에서 박스·본문과 겹치지 않는지 직접 확인한다.

**다크모드 고정.** 최종 영상은 항상 다크모드다. 렌더는 반드시 `render_parts`(장면별 `scene-NN.html`, `data-theme="dark"` 진입점)와 `mux`로 한다. 프로젝트 `index.html`을 `hyperframes render .`로 한 번에 렌더하면 서브 컴포지션 CSS 때문에 라이트로 나올 수 있으므로 쓰지 않는다. 코드가 이를 강제한다: `render_parts`는 `data-theme="dark"`가 아닌 진입점·`index.html`을 거부하고, `mux`·`verify_media`(`not-dark`)·`burn_subtitles`는 여러 시점의 좌상단 배경 밝기가 기준(80)을 넘으면 실패한다. 이 검사를 끄거나 우회하지 않는다.

content에는 [회로 검토](circuit-semantics.md)의 현재 검토를 결합한다. passed 보고서도 입력 변경·장면 누락·근거 변경 후에는 게시를 통과하지 않는다. 검토 구조 검사 통과를 식의 물리적 증명으로 보고하지 않는다.

글꼴 초기 그리기 차이를 막기 위해 화면 조립 시 document.fonts.ready 이후 타임라인을 등록한다. 이전 코드로 조립한 RUN은 composition 코드 지문 변경으로 assemble을 한 번 다시 실행해야 한다. 음성은 재생성하지 않는다.

렌더 시도별 pending 파일을 쓰고 시간 초과/중단 시 Node와 Chrome·FFmpeg 자식 프로세스를 종료한 뒤 정리한다. 장면·마스터는 영수증과 함께 교체하며 교체 실패/중단은 이전 쌍으로 복구한다. 복구 실패 시 `.rollback` 사본을 유지하고 경로를 알린다. 이 사본이 남으면 다음 시도가 덮어쓰지 않으며 수동 복구 후 재개해야 한다. 프로세스 트리 종료는 현재 macOS에서 실측했고 Windows의 taskkill 경로는 이 장비에서 실행하지 않았다.
