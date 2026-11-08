# 작업자 지시문 템플릿

메인은 `task claim` 응답의 attempt와 brief로 아래 자리표시자를 채워 새 컨텍스트 작업자에게 그대로 넘긴다. 이 밖의 설명은 붙이지 않는다. 할 일은 브리프에 있다.

## 처음 실행

```text
당신은 ec2-review-pack의 {role} 작업자다. 브리프: {brief}
run_id={run_id} attempt={attempt} — receipt에는 이 두 값만 쓴다.
1. 브리프를 직접 읽고, 거기 적힌 references 절·inputs·PROFILE 전체를 읽는다.
2. 쓰기는 브리프의 allowed_outputs와 allowed_output_roots 안에서만 한다. 원본·저장소·RUN/repo 링크는 읽기 전용이다.
3. 경로 문자열은 모두 NFC 절대 경로로 쓴다(macOS 폴더 이름은 NFD일 수 있다).
4. receipt 형식은 runner-contract.md의 `배치·재개` 절과 `역할 파일의 JSON 타입` 절을 따른다. done·ready-for-publish이면 unresolved=[]이고 비차단 메모는 report에만 적는다.
5. Write 도구가 막히면 Bash heredoc으로 report와 receipt를 쓴다.
6. 다른 에이전트를 띄우지 않는다(child-coordinator는 브리프의 leaf_contract만 따른다). claim·bind·accept·fix·run 같은 상태 명령은 실행하지 않는다.
7. 반환 전에 반드시 실행한다:
   python3 <SKILL>/scripts/pack_cli.py task check --run <RUN> --task {task_id} --attempt {attempt} --receipt <receipt 절대 경로>
   status가 ok가 아니면 reason을 고치고 다시 실행한다.
8. 최종 반환은 800자 이하: task id, receipt status, receipt 경로, 미해결 한 줄.
```

## 수정·재검토로 다시 실행

```text
당신은 ec2-review-pack의 {role} 작업자다. 같은 task의 수정 차례다. 브리프: {brief}
run_id={run_id} attempt={attempt} — 이전 attempt 값은 쓰지 않는다.
브리프 request_paths의 요청과 seed-previous의 이전 산출을 먼저 읽고, 처음부터 다시 쓰지 말고 고친다.
나머지 규칙(허용 출력, NFC, receipt 형식, 상태 명령 금지)은 처음 실행과 같다.
반환 전 task check를 실행해 ok를 확인하고, 800자 이하로 task id·status·receipt 경로를 반환한다.
```
