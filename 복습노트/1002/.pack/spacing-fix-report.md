# 1002 상하 여백 수정 · 2026-10-22

- 원인: `.sum p/ul`의 margin 초기화가 범용 형제 선택자보다 강해서 요약 제목 위와 식 목록 뒤가 0px. 제목 뒤 문단에는 p+p 규칙이 우선해 8px이 적용됨.
- 수정: 초기화의 우선순위를 낮추고 그룹 여백을 명시. 문장 간 규칙에서 제목·lead 다음을 제외. 두 공통 HTML 템플릿과 1002 정리노트·문제설명에 반영.
- 공통 계산 뒤 소문항은 데스크톱 32px, 모바일 24px. 풀이 제목 직후 첫 소문항은 24px 유지.
- 재발 방지: 두 템플릿·4개 화면 폭(1280/1024/1023/375)의 실제 간격 회귀 테스트. 문제설명 브라우저 검사에서 요약 패널을 열고 모든 문항의 제목 위/아래·식 목록 뒤·소문항 간격을 측정하며 누락/미달은 실패.
- 검증: 회귀 테스트 2개와 24개 하위 사례 통과. 공개 문장/조립/팩 배치 관련 테스트 21개 통과·1개 환경 조건 생략. 브라우저 판정 테스트 3개·12개 하위 사례 통과. 1002 문제설명 9문항 × 4개 조합에서 여백·수식·overflow·console 오류 0. 정리노트도 4개 조합에서 여백·수식·overflow 오류 0. 문제설명 전용 판정의 요약 개수/외부 리소스 항목은 정리노트 계약과 달라 해당 결과는 별도 보존.
- 실제 수정 화면 after-p4/p5/p8.png를 열어 첨부 위치와 대조. 발행 후 HTML은 승인 stage와 바이트 동일. HTML·MD 기계 검사 OK.
- 내용/수식/문제/답안 PDF는 동일. 기존 노트 백업의 승인 hash와 현재 노트를 대조하여 style/script 밖 바이트 동일성을 증명. 현재 입력/그림/조각 해시도 동일하여 content·independent 승인은 기존 carry_reviews 정책으로 보존하고 source_visual·browser는 실제 재검토.
- 상세 근거: spacing-browser-explanation.json, spacing-browser-note.json, spacing-reference-equivalence.json. 임시 백업·화면은 아래 RUN에 보존.

RUN: C:\Users\Hyunjun\AppData\Local\Temp\ec2-spacing-1002-20261022
