# 개발 수용 기록

2026-10-07 로컬 검증. 생성된 예시 영상은 개발 scratch에만 있으며 과목 학습 영상으로 전달·커밋하지 않았다.

- Python 3.14, Node, HyperFrames 0.8.72, FFmpeg/ffprobe 9.0.2 (`ffmpeg-full`, libass 지원), 기존 로컬 Chrome을 사용했다. 설치를 전역 변경하지 않았다.
- 전체 unittest 81개 통과. 독립 CLI·source closure·단일 템플릿·발음 payload·회로 검토 gate·0/N 출력·부분 실패·이전 결과/링크·재음성 원본 보존을 검사했다.
- 원자료 discover 읽기: 0902의 노트 정상; 1002 54파일 중 problem-md 10개, 문제/답안 PDF 각 1개, problem-list 1개, 참조 연결 15개, missing_problem_ids=[] . 원자료 수정 없음.
- 로컬 PCM smoke: MOS 전류 분배 검증용 fixture, note/review 2장면, 156프레임(5.2초), 124800 PCM 샘플. 미디어·PCM·최종 음성 동기·실제 편집 소스 검사가 모두 passed.
- 브라우저 28시점에서 역방향 seek·OS light/dark·Pretendard·KaTeX·수식 넘침·장면 경계·captionCount=0 확인. 대표 PNG와 최종 MP4 프레임을 직접 대조했고 좌우 전류 표시가 60:40 비율이며 수식·가정이 읽힌다.
- 스킬 frontmatter quick_validate 통과. 초기 smoke에서 드러난 통합 소스의 dark token/KaTeX 초기화 문제를 수정하고 새 scratch RUN에서 다시 통과했다.
- HyperFrames 0.8.72에는 usage 명령이 없어 usage는 unknown이다. 최신 버전 조회/업그레이드는 이번 고정 런타임 검증 범위에서 수행하지 않았다.
- 유료 TTS/API 호출 0. 실제 Aoede 발음·내레이션 내용·청취 검증은 **미실행**이다. 합성 PCM은 기술 검사이며 실음성 검증을 대신하지 않는다.

재현 (아래 대문자는 로컬에서 확인한 절대 경로로 펼친다):

```text
PATH=FFMPEG_FULL_BIN:$PATH python3 -m unittest discover -s SKILL/tests -v
python3 SKILL/tests/integration_smoke.py --run SCRATCH_RUN --assets SKILL/assets/runtime --hyperframes-entry HF_ENTRY
node SKILL/tests/browser_check.mjs SCRATCH_RUN PUPPETEER_PACKAGE_JSON CHROME_EXE
python3 QUICK_VALIDATE_SCRIPT SKILL
```

실제 영상 요청은 원자료 전체 선정 → 장면·회로 검토 → 인증 가용성 확인 → TTS → 조립·렌더 → 내용/청취/프레임·편집 소스·미디어 검증 → publish-set으로 완료한다. 프로그램의 구조 검사만으로 학습 내용 정확성을 확정하지 않는다.

독립 리뷰의 Important 2건(참조 그림 변경 지문, 묶음 영상에서 독립 재음성 실행 분리)은 실패 재현 후 수정했고 전체 81개 회귀가 통과했다. 선택 자료 조회 함수의 읽기 전용 명령 예시 추가는 Minor로 보류했다. 현재는 discover()를 Python에서 호출할 수 있다.
