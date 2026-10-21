# 리뷰어 지시문 (lite에서는 부모가 개인화 감사를 수행)

---
전자회로2 복습팩 초안을 검토한다. 학습 산출물은 읽기 전용이며 아래 개인화 감사 기록만 쓴다.

- 개인 명세(필수 읽기): `<REPO>/docs/learning/solution-style.md` 절대 경로와 `<RUN>/manifest.json`의 `learning_style` snapshot. 현재 바이트와 snapshot이 일치하는지 확인한다.
- 개인화 감사 산출: `<RUN>/learning-style-audit.json`. 대상은 manifest의 **모든 topic ID**(why·요약·예고·링크 포함), 규칙은 snapshot의 모든 rule_ids다. 각 토픽의 첫 설명에서 회로 역할과 핵심 관계가 먼저 보이고 formal에 상세 유도가 이어지는지 실제로 읽는다. `lite`는 메인 에이전트가 같은 감사를 수행한다.
- 대상: `<RUN>/repo/복습노트/<range>/<정리노트 html>`, `<RUN>/manifest.json`의 `problems`
- 근거: `<RUN>/summaries/stt-*.md`, `<RUN>/slides.txt`, `<RUN>/candidates.tsv`, Razavi `<RUN>/repo/교과서/마이크로전자회로/<N>장.pdf`, 문제 md(`<RUN>/repo/교과서/마이크로전자회로/chNN/…`, `<RUN>/repo/from_the_past/md/…`)
- 규칙: `<SKILL>/references/content-rules.md`, `problem-selection.md`

확인할 것:
1. **사실 오류**: 식, 정의, 부호, 근사 조건(예: "$g_m r_O \gg 1$일 때"), 소신호 등가회로가 요약·슬라이드·교과서와 맞는가. 출력저항·이득 식은 한 번 직접 유도해 본다.
2. **누락**: 요약의 핵심 내용·강조 발언·미룬 유도 중 노트에 없는 것.
3. **범위**: "예고만/안 다룸" 내용이 본문에 설명되어 있는가.
4. **ELI5 품질**: 쉽게 말하면(eli5) 레이어가 필요한 용어를 짧게 풀어 쓴 1~3문장인가. 첫 설명과 작은 예시만으로 다음 결과를 예측할 수 있는가. content-rules.md의 "이해되는 설명의 순서"대로 핵심 동작·작은 예시가 유도보다 먼저 나오며, 그림과 요약이 같은 규칙을 보여 주는지 확인한다. 작성자의 적용 질문을 직접 풀어 답·이유·조건을 대조한다. pole 예시라면 −40 다음 −60 dB/dec를 추론하고, 이득의 순간 하락과 기울기 변화를 구별할 수 있어야 한다. 정의·구조 토픽은 작은 사례에서 정의를 식별할 수 있는지 확인한다. 비유나 쉬운 단어가 있다는 이유만으로 통과시키지 않는다. 핵심 동작이 유도 뒤에 묻혀 있거나 예시로 규칙을 적용할 수 없으면 Important로 지적한다.
5. **문제 선별**: 각 `problems[]`에 대해 md 원문과 풀이를 읽고 — 수업에서 다룬 절만으로 풀리는가, `why`가 실제 문제 내용과 맞는가, `anchor` 토픽이 맞는가, 구성(예제·연습/장말·기출 비율, 절마다 최소 1개)이 규칙과 맞는가. 빠진 "다룸" 절이 있으면 `candidates.tsv`에서 대체 후보 id를 제안한다.
6. **표현**: 표 첫 열이 한 글자씩 줄바꿈되거나 빈 칸이 있는 표, 잘린 문장.
7. **첫 페이지(`why-circuit`)**: `content-rules.md` "왜 쓰는가 페이지"의 4단계(문제 / 단순 해법과 한계 / 핵심 아이디어 / 대가와 쓰이는 곳)를 모두 갖췄는가. 뒤 토픽의 유도를 되풀이하지 않는가. `<a href="#…">` 링크가 실제로 그 내용을 다루는 토픽을 가리키는가. 범위의 회로가 모두 나오는가.

개인화 감사는 다음 형태로 실제 검토 후 기록한다. `not_run`을 시작 상태로 쓰고, 적용 위치/내용 또는 `not_applicable` 이유와 reviewer를 채운 뒤에만 해당 토픽을 `pass`로 둔다. 기계 검사는 형식·집합·해시만 확인한다.
```json
{"learning_style": {"path": "docs/learning/solution-style.md", "sha256": "<현재 snapshot>", "rule_ids": ["<전체 규칙 ID>"]},
 "items": {"<topic ID>": {"status": "not_run", "reviewer": "", "rules": {
   "<규칙 ID>": {"disposition": "applied", "evidence": ""}}}}}
```
문제 없는 토픽도 감사하며 회로/계산 규칙이 비적용이면 구체적 이유를 쓴다. `learning-style-audit.json` 외 리뷰 보고 형식:
```
## Critical
- [s2-rout] 문제 → 고칠 내용
## Important
- [P9.12] …
## Minor
- …
```
각 항목은 토픽 id 또는 문제 id로 시작한다. 없으면 "없음".
---
