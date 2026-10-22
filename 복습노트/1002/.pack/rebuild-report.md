# 복습팩 1002 완료

- 파일: 정리노트 HTML·MD, 복습문제 PDF 9쪽, 답안 PDF 16쪽, 문제설명 HTML·MD, 그림·검산 자료 폴더.
- 기본 팩: 완료. 정리노트 기계 검사와 MD 변환 최종 OK, 답안 유예 없음.
- 문제설명: published — 9문항/14소문항. 원본 화면·내용·독립 검산·브라우저 검토와 개인화 감사 통과. disputed 없음.
- 범위: Lec4 s22–35(도입의 BJT 바이어스 s19–22 복습 포함), Razavi 10.2.3·10.4·10.5 일부. 부하 불일치·CMRR·차동-단일단 변환·능동 부하의 새 전개는 예고만.
- 선발: 기출 4개/교과서 5개, 핵심 7개/추가 2개, 소문항 14묶음. 핵심 약 100분/전체 약 134분은 추정값이다.
- 사용자 추가 지시: 타회차 중복 허용. 2018-2 중간 Q3·2019-1 중간 Q4의 1007 수록 이력을 보존하고 이번에도 채택했다.
- 기출 전체 검토: 35개 중 선택 4개·제외 12개·보류 19개. 범위 밖 CMRR/부하 불일치/주파수·피드백 등을 함께 묻는 문항은 전체 소문항 단위로 보류했다. 2021-1 중간 Q3은 R_P의 DC 바이어스 가정이 원문에 없어 제외했다.
- 전체 시험 범위: 이번 수업 목표의 기본형·설계 역산·BJT 유한 r_pi·대칭 CM을 핵심 문제로 다뤘다. 기초 2R_SS 유도는 두 CM 기출 풀이에 포함했고 P10.65는 중복으로 생략했다. 이후 수업의 CMRR/비대칭은 보류 목록에서 재검토한다.
- 선발 기록: .assets/selection.json, .pack/selection-review.json.
- 스킬이 정한 사항: slug Differential_Amplifiers, why+s0–s4의 6섹션/15토픽, 위젯 0개. 정적 SVG·작은 사례로 개념을 설명하고 같은 계산의 중복을 줄였다. E10.11의 필수 전제 E10.10을 함께 수록했다.
- 풀이 표기: 일곱 구역 통합 본문, 한 행 하나의 계산, G_m → 부하 포함 R_out → 부호 있는 A_v. 저항 포함 다이오드 접속은 새 기본 블록 (1/g_m+R_P/β)∥r_o를 쓰고 1/g_m을 숨기거나 삭제하지 않았다.
- 최신 명세: 작업 중 갱신을 감지해 새 실행으로 추출·저작·감사를 다시 묶었다. 최종 SHA 15dd74dba003093e0a3e627a7531d1b89dbc4b081ebfb2f04245d065758f62fe.
- 검증: 정리노트 개인화 15×12=180개, 문제설명 14×12=168개 pass. 두 HTML의 네 화면 조합에서 수식/콘솔/가로 넘침 오류 0. 독립 계산 10개 스크립트 실행 0, 원문 소문항 14개 판정 pass.
- PDF 검토: 문제지 9쪽·답안 16쪽 전체 확인. 모두 16:9, 하단 1/6(180/1080)의 자막 여백 유지. 최종 답안의 하단 밴드는 래스터 최소값 255·텍스트 0, 빌드 OVERFLOW 없음. Pretendard SemiBold 실제 PDF 임베드 확인.
- 발행 receipt: .pack/answer-publication-receipt.json. 답안 렌더 검토는 .pack/answer-render-review.md, 해설 검토는 .assets/자료_문제설명_1002_Differential_Amplifiers/validation.json.
- 미해결: 없음.

## 선발 문항

- E10.10 (예제, core) — E10.11의 원문 전제이며 이상적 전류원 부하 BJT 반회로의 G_m과 R_out 기준을 세운다.
- E10.11 (예제, core) — 첫 수업 예제 그대로 이상적 부하를 실제 pnp 전류원으로 바꾸고 두 r_O의 병렬을 확인한다.
- P10.62 (장말문제, core) — 기출의 순방향 계산에 없는 MOS 입력 캐스코드의 이득 목표에서 테일 전류를 역산한다.
- P10.64 (장말문제, core) — 입력과 부하를 모두 캐스코드로 키운 두 출력저항의 병렬 및 NMOS·PMOS 폭 설계를 연습한다.
- 2018-2_중간-Q1 (기출, core) — 세 원본 회로에서 선행 이미터 축퇴, 수업의 R1/R2 pnp 부하, 유한 r_π BJT 캐스코드를 차례로 구별한다.
- 2015-2_중간-Q2 (기출, extra) — 베이스 저항 pnp 부하와 다단 BJT 캐스코드의 출력저항·이득을 기본 반회로 다음에 확장한다.
- 2018-2_중간-Q3 (기출, core) — 캐스코드 테일의 큰 R_SS를 2R_SS 공통 모드 반회로에 넣어 차동 이득과 단일 출력 CM 이득을 비교한다.
- 2019-1_중간-Q4 (기출, core) — 이번에는 부하가 캐스코드이고 테일이 단순한 원본 회로에서 입력·부하 저항의 병렬을 유지해 DM과 단일 출력 CM을 비교한다.
- P10.66 (장말문제, extra) — 기출의 CM 수치 계산에서 한 걸음 더 나아가 유한 테일 저항으로 CM 이득 상한 부등식을 증명한다.

## 실행·백업

- RUN: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855
- EXPLAIN_RUN: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\problem-explain\1002-explicit-gm
- 기존 기본 팩: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\previous-basic-pack
- 기존 문제설명: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\previous-explanations
- 설명 발행 백업: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\problem-explain\1002-explicit-gm\review-1002-Differential_Amplifiers\backups
- 답안 발행 receipt 원본: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\answer-backup-final\receipt.json
- 렌더 근거 원본: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\answer-pages-final
- 최종 답안 검토 JSON: C:\Users\Hyunjun\AppData\Local\Temp\ec2-review-pack-1002-20261022-160855\answer-review.json

커밋은 실행하지 않았다. 제안: `git add 복습노트/1002 && git commit -m "docs(notes): regenerate review pack 1002"`

폴더 배치 검사: `.claude/skills/ec2-review-pack/tests/test_pack_layout.py` — 2 passed. 최종 링크 4개 HTTP 200, `check_html.py`와 `html2md.py --check` 모두 OK.
