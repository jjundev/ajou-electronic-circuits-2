# 복습팩 1016 완료

- 기본 팩: HTML 1 · MD 1 · PDF 2, 기계/내용/브라우저/MD 검사 통과.
- 문제설명: published — 10문항 / 10 main 소문항. 네 검토 모두 pass, unresolved disputed 없음.
- 범위: Lec5 s12–23 (s11은 지난 수업 연결), Razavi 11.1.5·11.1.6·11.2.1·11.2.2. 시험 상한 Lec5 p23. p24 fT와 이후 회로별 내재 용량 응답은 예고만.
- STT 타임스탬프 없음: 허위 시각 대신 Part 번호 사용.
- 스킬이 정한 사항: slug Miller_High_Frequency_Models; why/밀러/AC 결합/MOS/BJT/요약 6섹션, 14토픽; 위젯0(노드 연결과 근사 조건에 정적 SVG 사용); 예제4·연습4·장말2, 네 절 및 전제의존을 보존하기 위한 예제 수 예외. 기출은 날짜 범위와 미진도 소문항을 함께 요구하여 제외.
- E11.11/X11.11은 외부 Ci/CL와 이미 배운 1/gm·RC만 사용. 이후 내재용량의 소스팔로어 주파수 응답식 제외.
- P11.22 원본 단계의 근사 조건 누락: 원본을 수정하지 않고 설명에 정확 KCL/극점과 RC << (RB||rpi)(1+gmRC) 조건을 공개·검산. 근사 수준 차이 예외 기준으로 최종 pass.
- 문제 구성:
  - E11.10 (예제) — CS 부유 커패시터의 밀러 근사 극점
  - X11.10 (연습문제) — 밀러 입력 커패시턴스 수치 계산
  - P11.16 (장말문제) — 일반 임피던스인 저항에 밀러 정리 적용
  - P11.22 (장말문제) — BJT 입력저항을 포함한 밀러 근사 극점
  - E11.11 (예제) — 외부 C_i·C_L와 기존 1/g_m·RC만으로 통과 대역 설계(내재 용량 응답식 제외)
  - X11.11 (연습문제) — E11.11의 외부 C_i·C_L에 전류·폭 변화 적용(내재 용량 응답식 제외)
  - E11.13 (예제) — MOS 커패시턴스 위치와 소거
  - X11.13 (연습문제) — 다이오드 연결 부하의 고주파 소신호 회로
  - E11.12 (예제) — BJT 캐스코드의 커패시턴스 식별
  - X11.12 (연습문제) — BJT 캐스코드의 고주파 소신호 회로

- RUN: /private/tmp/ec2-review-pack-1016-20261016
- EXPLAIN_RUN: /private/tmp/ec2-review-pack-1016-20261016/problem-explain/final-01
- 백업: 기존 1016팩/설명 없음; 새 발행 백업 경로 /private/tmp/ec2-review-pack-1016-20261016/problem-explain/final-01/review-1016-Miller_High_Frequency_Models/backups
- 미해결: 없음
- 커밋하지 않음. 제안: git add 복습노트/1016 && git commit -m "docs(notes): add review pack 1016"
