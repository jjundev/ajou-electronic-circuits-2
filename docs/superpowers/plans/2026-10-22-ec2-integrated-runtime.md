# 통합 해설 공통 실행기 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 확정한 일곱 구역 해설을 정상 조립·검사하고 같은 본문에서 간결한 답안 PDF를 추출한다.
**Architecture:** 기존 본문 요소에 답안 추출 표지만 붙인다. 별도 풀이 사본은 만들지 않는다. 구형 발행 자료의 검증용 추출은 유지하고 새 build는 통합 형식만 받는다. 입력·명세·검토·그림 해시 게이트는 유지한다.
**Tech Stack:** Python, 기존 EPE DOM 파서, workbook, Playwright, PDF 렌더러.
**Spec:** docs/learning/solution-style.md 및 두 스킬의 일곱 구역 계약.

## Global Constraints
- understand → recall → start → solve → verify → pitfall → retry; solve 제목 ‘이렇게 풀어요’.
- 독립 계산은 별도 display; 같은 양의 연속 등식 허용.
- 상세 설명은 HTML, 답안 PDF는 본문의 회로·판단·계산·최종 답을 선택하여 재사용.
- 기존 사용자 수정 보존. 커밋·push 없음. 대표 여섯 문항만 재생성.

## Review Focus
- 다중 소문항의 순서·답안 누락·중복·중첩 표지를 거부하는 테스트.
- start의 공통 회로를 잘못된 소문항에 배정하지 않는 명시적 범위 테스트.
- 표지 없는 내용·요약·검산 전부를 PDF로 잘못 옮기지 않는 추출 테스트.
- 과거 발행 자료의 무결성 검증 유지와 새 저작에서 구형 route 거부 테스트.
- 실제 최종 DOM 자원 경로 보존 및 변경된 검토 해시 거부 테스트.

### Task 1: 공통 구조와 추출 계약
- [x] 회귀 테스트를 작성해 실패 확인.
- [x] 통합 본문 검증·선택 추출 구현, 기존 검증 게이트 유지.
- [x] 관련 전체 테스트와 독립 코드 리뷰, 발견 사항 수정.

### Task 2: 대표 재생성과 실제 검토
- [x] 최신 명세·원본 MD에서 새 extract; 여섯 조각의 기존 본문에 추출 표지만 추가.
- [x] 정상 build/check, 실제 내용·독립 검산·원문·브라우저 검토 기록 후 publish.
- [x] 정상 workbook overlay 경로로 답안 PDF 생성, 모든 페이지 렌더링 검토.
- [x] HTML·MD·PDF 및 해시·보존·최종 보고 확인.

사용자가 이 턴에서 구현·재생성·최종 검토를 명시적으로 승인하여 같은 세션에서 이어서 실행한다.
