# 노드·출력 끝점·근사 출력저항 최종 검토

현재 최종본은 `.superpowers/ec2-node-approx/explain/review-1021-Representative/stage/b30c28596fa24537966f1cd5dad3346f`이다. 이전 중간 stage와 오른쪽 전류 화살표 승인은 현재 승인이 아니며 대체되었다.

## 확정 규칙과 반영

- 이름 있는 입력·출력·시험 전압 노드에는 보이는 점을 둔다.
- Vt는 출력 배선의 실제 맨 오른쪽 끝점이다. 점 오른쪽으로 배선을 연장하지 않는다.
- 왼쪽으로 흐르는 it 화살표 전체와 라벨은 Vt 왼쪽에 둔다. 화살표 꼬리와 점 사이에 간격을 둔다.
- 병렬 전류원 왼쪽 / ro 오른쪽 / 출력 맨 오른쪽 배치와 실제 전기적 연결을 유지한다.
- Rout은 핵심·상세 HTML·요약·MD·답안 PDF 모두 처음부터 조건에 맞는 근사식을 쓴다. 정확 Rout 유도·수치 비교는 내부 검산만 사용한다. 원문 정확식 요구 또는 근사 불성립에 한해 예외 이유를 밝힌다.
- P9.23 유한 beta를 유지하고 ro1||rpi2를 ro1로 줄이는 추가 조건 ro1<<rpi2를 명세에 보완했다. 정확 Gm/Av는 Rout 표시 제한과 구분한다.
- SVG 일반문자 vout 네 군데는 이탤릭 v와 실제 out 아래첨자로 바꿨다.

개인 명세와 두 스킬의 SKILL/저작/검토 지침 총 7파일을 수정했고 기존 12규칙 ID를 유지했다. 대표 6문항·7소문항, 11 SVG를 반영했다. 전체 기존 수업 팩을 일괄 재생성한 작업은 아니다.

## 검증

- 작성자와 다른 리뷰어의 지침/해설 교차 검토, 독립 기호·수치 검산, 7소문항×12규칙=84감사 통과.
- 원문 시각 검토는 이전 실제 원문 증거와 동일한 원문·6그림 해시를 확인한 뒤 출처를 명시해 보존했다. 새로 원본 PDF 전체를 다시 읽었다고 주장하지 않는다.
- 최종 HTML 구조 검사와 1280/1024/375px×라이트/다크 6조합 화면 검사 오류 없음. 최종 실제 회로 확대 화면에서 점·끝점·it 위치·vout 아래첨자 확인.
- 진짜 workbook overlay 경로로 답안 PDF 빌드 성공. 실제 PDF 7쪽과 확대 그림을 작성자 외 리뷰어와 메인 모두 열어 확인. 1440×810pt, 하단 135pt 여백 유지, 겹침/잘림 없음.
- 승인된 현재 HTML/MD/프로필/PDF와 발행 파일의 바이트 동일성 및 원본 자료 17파일 보존 확인. PDF 교체 전 백업과 발행 영수증 보존.
- 실행 코드 수정 없음. 과거 전체 테스트 수를 이번 실행 결과로 재사용하지 않았다. 이번에는 구조·수학·화면·실제 PDF·발행 해시 검사를 수행했다.
- 브랜치 codex/ec2-learning-style 유지. 커밋·푸시·병합·정리 없음.

## 최종 SHA-256

- `docs/learning/solution-style.md`: `40b8b4ed3f38176442f59abfcf57f1a33409af6dd095a4b2631297a05f90132c`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/문제설명_1021_Representative.html`: `55d72f68dac931b91049def61db473270514f3159e72d2d1feab23d4ac19006c`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/.assets/문제설명_1021_Representative.md`: `e9183403497a38d4370766a611d2031751974bfc88d40b341436e69f409eecba`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/복습문제_1021_Representative-답안.pdf`: `bc7ecb55b12aac718f4777d2b0ea69d86587cb77d3562170d2ac5cdf34211ba9`

세부 증거: `.superpowers/ec2-node-approx/`의 content-review.json, math-review.json, browser.json, pdf-review.json, final-verification.json, answer-publication/receipt.json.
