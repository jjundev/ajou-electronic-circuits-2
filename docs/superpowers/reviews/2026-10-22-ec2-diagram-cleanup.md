# 회로도 제목·점·라벨 여백 최종 검토

최종 stage: `.superpowers/ec2-clean-diagrams/explain/review-1021-Representative/stage/8c896a662c2e4834b87ee25f8a7b8447`. 중간62305f49 stage와 수정 전 PDF는 현재 승인본이 아니다.

## 반영한 사용자 확정 사항

- 접지 입력 위의 불필요한 독립 Rout 제목 삭제.
- Gm 분석 제목·측정 조건·유도 설명은 SVG 아래 caption/수식으로 이동. 소자 자체의 gm vpi 제어원 라벨은 유지.
- 이름·분기가 없는 직선 중간 장식 점303,35 삭제. 입력·출력 단자, 이름 있는 내부 전압 노드, 실제 분기 접속점은 유지.
- 출력/시험전압 라벨을 올리고 viewBox 여백을 늘려 아래첨자까지 도선과 떨어지게 배치. 전압 라벨의 실제 glyph bbox로10곳 측정: 최소16.7498SVG단위,13px글꼴에서0.6em=7.8단위 이상. 소자 라벨과 전류원 외곽선 사이 모든 거리를 수치 보증한 검사가 아니며, 그 표기는 실제 화면에서 가독성과 겹침을 확인했다.
- 기존 전류원 왼쪽/병렬ro오른쪽/출력맨오른쪽, Vt끝점 및 그 왼쪽 it, Rout근사식 우선 규칙 유지.

개인 명세와 두 스킬의 SKILL/저작/검토 지침 총7파일에 반영했고12규칙 ID를 유지했다. 대표6문항의11SVG를 점검했다. 기존 수업팩 전체 재생성이나 실행 코드 변경은 하지 않았다.

## 실제 검증

- 작성자와 다른 리뷰어가7소문항/84규칙 적용을 검토해 통과. 모든 비그림 해설 HTML 바이트와11SVG 전기적 paths/polygons가 직전 승인본과 같아 수학/회로 변경 없음. 이동한 제어 관계는 아래 설명에서 보존.
- 기존 독립 검산의 증거 바이트 및 원문/6그림 해시를 다시 확인해 출처를 명시해 보존했다. 새 blind solve나 원본 전체 재열람을 주장하지 않는다.
- HTML 구조 검사와1280/1024/375px×라이트/다크6조합에서 오류/넘침 없음. 실제 출력전압/시험전압 glyph 여백 검사와 회로 확대 화면 확인.
- genuine workbook 승인 overlay로PDF 빌드 성공. 최종7쪽 모두 메인과 독립 리뷰어가 실제 열고 확대 그림도 확인.16:9(1440×810pt),하단135pt 여백,잘림/겹침 없음.
- PDF에서 발견한 별도 줄의 마침표는 최종 caption의 마침표 하나를 제거해 수정. 새 HTML/MD가 그 문자 외에는 중간 검토본과 동일함을 확인하고 새 PDF를 다시 검토했다. 수학 텍스트 추출에서 단독 마침표로 묶인 것은 실제 시각 줄바꿈과 구분했다.
- 원본 문제/그림/손풀이17파일 해시 불변. 발행 HTML/MD/PDF/프로필과 현재 검토 해시 동일, PDF 백업/영수증 검증.
- 실행 코드 변경이 없어 전체 런타임 테스트를 다시 돌리지 않았다. 과거 테스트 통과 수를 현재 검증으로 사용하지 않았다. git diff --check 통과.
- codex/ec2-learning-style 브랜치 유지. 커밋/푸시/병합/스크래치 삭제 없음.

## 최종 SHA-256

- `docs/learning/solution-style.md`: `f359ee61d337831e176c3dad5b525ed424a73aa4ddc23364bc823848113d9206`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/문제설명_1021_Representative.html`: `24da487264696eb3f714ba7589c7935dc9b0436b612ba080a25a7d11e84410d0`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/.assets/문제설명_1021_Representative.md`: `a629ba24ffcc2d86607963ea8bffac96d9997266d61aa6687f7d3a0757fdeff8`
- `.superpowers/ec2-learning-style-validation/corpus/복습노트/1021/복습문제_1021_Representative-답안.pdf`: `85f904c3235fb63b31570119c25a34e63abcbb54e232f2a132491369a9fc44c3`

세부 증거: `.superpowers/ec2-clean-diagrams/`의 content-review.json,math-review.json,browser.json,label-spacing.json,pdf-review.json,final-verification.json,answer-publication/receipt.json.
