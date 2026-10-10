---
name: ec2-merge-report
description: 전자회로2 설계과제 보고서 본문 PDF(노션 내보내기)에 IEEE 윤리강령 표지를 붙여 BB 제출본을 만든다. "과제1 표지랑 합쳐줘", "제출본 만들어줘", "설계과제 표지만 만들어줘"처럼 요청하거나 /ec2-merge-report <n> [--date YYYY.MM.DD] [--keep-body]로 부를 때 사용한다.
---

# 전자회로2 설계과제 제출본 병합

노션에서 내보낸 본문 PDF 앞에 표지 1쪽을 무손실로 붙여 `설계과제/과제<n>/전자회로2_설계과제<n>_<학번>_<성명>.pdf` 를 만든다. 코드는 저장소 루트 패키지 `scripts/ec2_report/` 에 있고, 이 스킬은 그 CLI 를 부르는 절차서다.

## 절대 규칙

1. 학번·성명·교수명·분반·날짜 형식은 `.claude/과목정보.md` 에서만 읽는다. 코드나 명령에 직접 쓰지 않는다.
2. 본문 PDF 를 재인코딩하지 않는다 (`pypdf` 로 원본 스트림 그대로 병합).
3. 표지·최종본·PDF 메타데이터에 AI 관련 언급을 넣지 않는다. 메타데이터는 제목과 작성자만 남는다.
4. 본문 원본은 병합 검증(쪽수·1쪽 A4)이 통과한 뒤에만 지운다. 사용자가 보존을 원하면 `--keep-body`.

## 절차

1. **과제 번호 확정.** 사용자 말이나 인자에서 `<n>` 을 정한다. 모호하면 `설계과제/` 아래 폴더를 보고 가장 최근 과제를 고른 뒤 그 번호를 보고에 밝힌다.
2. **신원 게이트.** 아래가 빈 목록이 아니면 멈추고 `.claude/과목정보.md` 의 해당 항목을 채워 달라고 한다.
   ```bash
   python3 -c "from scripts.ec2_report import config as c; print(c.missing_identity(c.load_course_info(c.find_root())))"
   ```
3. **표지만 요청한 경우.** 아래를 실행하고 출력된 경로를 마크다운 링크로 알려 준 뒤 끝낸다.
   ```bash
   python3 -c "from scripts.ec2_report.cover import make_cover; print(make_cover(<n>))"
   ```
4. **병합.** 저장소 루트에서 실행한다. 본문은 `과제<n>/report/` 와 `~/Downloads` 에서 이름에 `설계과제<n> 보고서` 가 든 PDF 또는 PDF 1개짜리 zip 중 가장 높은 `vN` 을 고른다 (같은 판본이 여러 개면 가장 최근 것). 사용자가 파일을 지정하면 `--body` 로 넘긴다.
   ```bash
   python3 -m scripts.ec2_report.merge --n <n>
   ```
   - `FileNotFoundError` → 노션에서 `⋯ → Export → PDF (A4)` 로 내려받았는지, 파일명에 `설계과제<n> 보고서` 가 들어 있는지 확인해 달라고 한다.
   - zip 안 PDF 가 1개가 아니면 → 어느 파일인지 물어 `--body` 로 다시 실행한다.
5. **보고.** 출력의 최종본 경로를 마크다운 링크로, 쪽수(표지 1 + 본문 N)와 본문 원본 삭제 여부를 함께 알린다. BB 제출은 사용자가 직접 한다.

## 비-목표

- 노션 API 로 PDF 를 받아 오기 (노션 내보내기는 사용자가 한다)
- 본문 PDF 압축·재조판
