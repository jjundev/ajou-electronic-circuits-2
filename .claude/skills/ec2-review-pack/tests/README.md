# ec2-review-pack 테스트 실행

저장소 루트에서 실행합니다.

```powershell
# 전체, 병렬 (권장)
python -m pytest .claude/skills/ec2-review-pack/tests -n 12 --dist worksteal -p no:cacheprovider
# 전체, 직렬
python -m pytest .claude/skills/ec2-review-pack/tests -p no:cacheprovider
# 테스트 하나 (-n 없이)
python -m pytest ".claude/skills/ec2-review-pack/tests/test_pack_graph.py::test_quiz_adoption_keeps_approved_answer_after_sibling_removed"
```

측정값(2026-11-27, 8코어, 724 passed / 5 skipped / 357 subtests): 직렬 약 12분 25초, `-n 12` 4분~4분 40초.
`-n 8`도 통과하지만 두 번 모두 `-n 12`보다 10% 넘게 느렸습니다. 다른 작업이 CPU를 쓰면 시간이 25%쯤 흔들립니다.

**완전 재현 모드:** `EC2_TEST_CLI=subprocess`(pack_cli를 진짜 프로세스로)와 `EC2_TEST_BROWSER=real`(퀴즈 브라우저 검사를 진짜 Chromium으로)을 함께 설정합니다. pack_cli/pack_flow 진입점이나 concept `browser_check`를 바꿨다면 커밋 전에 이 모드로 한 번 돌립니다. `-n 12`에서 약 8분 걸립니다.

```powershell
$env:EC2_TEST_CLI = 'subprocess'; $env:EC2_TEST_BROWSER = 'real'
python -m pytest .claude/skills/ec2-review-pack/tests -n 12 --dist worksteal -p no:cacheprovider
Remove-Item Env:EC2_TEST_CLI, Env:EC2_TEST_BROWSER
```

**`EC2_CACHE_ROOT`는 미리 설정하지 않습니다.** 각 pytest 프로세스(xdist 워커마다)가 `_util.py`에서 따로 임시 폴더를 만들어 RUN과 발행 잠금을 격리합니다. 미리 설정하면 워커들이 같은 폴더를 공유합니다.

**in-process CLI 호출과 monkeypatch:** 기본 모드의 `cli()` 호출은 새 프로세스처럼 pack_cli, pack_flow, pack_probe, note_assemble 외의 scripts/ 모듈을 새로 불러옵니다. 그래서 pack_actions, pack_parallel, pack_receipts 같은 모듈에 건 monkeypatch는 CLI 호출에 닿지 않습니다. 그런 패치는 함수를 직접 부르는 테스트에서만 검증됩니다.

**기본 모드에서도 진짜 브라우저가 도는 곳:** `zero_problem[None]`(진짜 퀴즈 브라우저 + 대체 보고서와 형태 비교), layout_probe 테스트, pack_approvals의 실제 브라우저 테스트, standalone-svg-qa, `real_probe=True` 통합 테스트. 그 밖의 퀴즈 시나리오는 `quiz_browser_stub.py`의 대체 보고서를 씁니다.
