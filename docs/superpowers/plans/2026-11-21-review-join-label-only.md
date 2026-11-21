# Review-Join Label-Only Disagreements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In new parallel RUNs, an `applied` / `not_applicable` mismatch between the two note reviewers is recorded and reported. It no longer becomes an Important finding that sends authors back to rewrite.

**Architecture:** `join_reviews` checks a per-RUN `join_contract`. On contract 2 it merges with style-audit's disposition and marks the mismatched cell `disagreement: true`. It appends the mismatch to `state['applicability_disagreements']` and creates no `review-join` finding. `init_run` writes contract 2 for new parallel RUNs. Existing RUNs, which have no key, keep contract 1 behavior. A summary helper puts the disagreements into `report.json`. A shared reference document gives both reviewers the same label semantics.

**Tech Stack:** Python 3 (stdlib), pytest. Runner code is in `.claude/skills/ec2-review-pack/scripts/`.

**Spec:** `docs/superpowers/specs/2026-11-21-review-join-label-only-design.md`

## Global Constraints

- Work on branch `fix/review-join-label-only` cut from `main`, not on `main`.
- Contract key `join_contract`; constant `LABEL_ONLY_JOIN = 2` in `pack_findings.py`. If the key is absent, the RUN is contract 1 and keeps today's behavior unchanged.
- Only `init_run(..., workflow='parallel')` writes `join_contract = 2`. Seeded and legacy RUNs are not migrated.
- Do not modify `references/solution-style.md` or `workbook/learning_style.py`. The snapshot hash and the audit validator stay as they are.
- On a disagreement, the merged cell keeps the **style-audit** disposition. Its evidence keeps both reviewers' text, in today's two-line format.
- The applicability table in `note-rule-applicability.md` is copied verbatim from the spec. It is a draft: the user must confirm it before the branch is merged.
- Run tests from `.claude/skills/ec2-review-pack/tests`: `python3 -m pytest -q <file>::<test>`. Baseline: `test_pack_findings.py` gives 40 passed.
- Every commit message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. The same candidate is joined twice (a style re-review on identical HTML). The disagreement list must hold one entry per cell, not two. → Task 1 `test_rejoin_same_candidate_keeps_one_disagreement_per_cell`.
2. A contract-1 RUN is resumed under the new code. It must still produce `review-join` findings, with no silent mid-run change. → Task 1 `test_contract_one_run_still_raises_review_join_finding`.
3. One reviewer is `needs-fix` while the other's labels differ. Join must not run, no disagreement is recorded, and only the real finding is routed. → Task 1 `test_needs_fix_review_records_no_disagreement`.
4. A real fix produces a new candidate after a disagreement on the old one. The report's current count must cover only the current candidate. → Task 2 `test_summary_counts_only_current_candidate`.
5. The report is written before any join, with no active audit. It must give zeros and `cells: None`, not crash. → Task 2 `test_summary_before_join_is_empty`.

---

### Task 1: Label-only join under contract 2

**Files:**
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_findings.py` (constants near line 71–79; `join_reviews` at 413–466)
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_flow.py:372-375` (parallel branch of `init_run`)
- Test: `.claude/skills/ec2-review-pack/tests/test_pack_findings.py`

**Interfaces:**
- Consumes: the existing helpers in `test_pack_findings.py`: `note_run` fixture, `submit_review(ctx, tid, findings=(), disposition=None, ...)`, `defect(rule, target)`.
- Produces:
  - `pack_findings.LABEL_ONLY_JOIN: int = 2`
  - `state['join_contract']: int`
  - `state['applicability_disagreements']: list[dict]`. Each item is `dict(candidate_digest: str, target: str, rule: str, style: dict(reviewer: str, disposition: str, evidence: str), content: dict(reviewer: str, disposition: str, evidence: str))`.
  - The merged audit cell gains `disagreement: True` only when the two dispositions differ.

- [ ] **Step 1: Add the legacy pin helper and pin the existing conflict tests**

Add `pin_join_contract(run, version)` to `test_pack_findings.py`. It calls `flow.update_state(run, flow.load_state(run)['revision'], lambda s: dict(s, join_contract=version))`. Call `pin_join_contract(run, 1)` as the first line after `run, _ = note_run` in these five tests:
- `test_same_reviewer_and_conflicting_source_judgments_cannot_join`
- `test_superseded_style_judgment_retires_exact_conflict_pair`
- `test_fresh_agreement_on_identical_html_can_reconcile_superseded_conflict`
- `test_repeated_conflict_on_identical_html_requires_new_pair_token`
- `test_prior_parallel_conflict_matches_only_its_two_adopted_reports`

Then add this test:

```python
def test_contract_one_run_still_raises_review_join_finding(note_run):
    run, _ = note_run
    pin_join_contract(run, 1)
    submit_review(note_run, 'content-review', disposition='applied')
    state = submit_review(note_run, 'style-audit')
    row, = state['findings'].values()
    assert (row['review_id'], row['severity'], row['target']) == ('review-join', 'Important', 's1-mean')
    assert not state.get('active_audit')
    assert not state.get('applicability_disagreements')
```

- [ ] **Step 2: Write the contract-2 tests**

```python
def test_label_only_disagreement_publishes_audit_without_findings(note_run):
    run, _ = note_run
    submit_review(note_run, 'content-review', disposition='applied')
    state = submit_review(note_run, 'style-audit')
    assert state['join_contract'] == 2
    assert not [r for r in state['findings'].values() if r['review_id'] == 'review-join']
    audit = json.loads(Path(state['active_audit']).read_text())
    rule = next(iter(audit['items']['s1-mean']['rules']))
    cell = audit['items']['s1-mean']['rules'][rule]
    assert cell['disposition'] == 'not_applicable' and cell['disagreement'] is True
    assert 'reviewer-style-audit (not_applicable)' in cell['evidence']
    assert 'reviewer-content-review (applied)' in cell['evidence']
    other = [c for t, i in audit['items'].items() for r, c in i['rules'].items() if (t, r) != ('s1-mean', rule)]
    assert not any('disagreement' in c for c in other)
    item, = state['applicability_disagreements']
    assert (item['target'], item['rule']) == ('s1-mean', rule)
    assert (item['style']['disposition'], item['content']['disposition']) == ('not_applicable', 'applied')
    assert item['candidate_digest'] == state['joined_review']['candidate_digest']
    import manifest  # noqa: F401  (puts workbook/ on sys.path)
    from learning_style import validate_style_audit
    assert validate_style_audit(audit, audit['learning_style'], list(audit['items'])) == []

def test_rejoin_same_candidate_keeps_one_disagreement_per_cell(note_run):
    submit_review(note_run, 'content-review', disposition='applied')
    state = submit_review(note_run, 'style-audit')
    Path(state['tasks']['style-audit']['receipt']['report']).write_text('superseded')
    state = submit_review(note_run, 'style-audit')
    assert len(state['applicability_disagreements']) == 1

def test_needs_fix_review_records_no_disagreement(note_run):
    submit_review(note_run, 'style-audit', [defect('shape')])
    state = submit_review(note_run, 'content-review', disposition='applied')
    assert not state.get('applicability_disagreements')
    assert {r['review_id'] for r in state['findings'].values()} == {'style-audit'}

def test_label_only_join_rejects_leftover_review_join_finding(note_run):
    import copy
    import pack_findings as ledger
    submit_review(note_run, 'content-review', disposition='applied')
    state = copy.deepcopy(submit_review(note_run, 'style-audit'))
    state['findings']['leftover'] = dict(id='leftover', review_id='review-join', status='open')
    with pytest.raises(flow.FlowError, match='label-only join cannot carry review-join findings'):
        ledger.join_reviews(state)
```

- [ ] **Step 3: Run the new tests and confirm they fail**

Run: `python3 -m pytest -q test_pack_findings.py -k "label_only or rejoin_same or needs_fix_review or contract_one"`
Expected: `test_contract_one_run_still_raises_review_join_finding` and `test_needs_fix_review_records_no_disagreement` PASS, because they pin today's behavior. The other three FAIL: two with a `KeyError` on the missing state key, and the leftover test because the matching FlowError is not raised.

- [ ] **Step 4: Implement**

- In `pack_findings.py`, add `LABEL_ONLY_JOIN = 2` beside `CONFLICT`.
- In `init_run`'s `if workflow == 'parallel':` branch in `pack_flow.py`, set `state['join_contract'] = 2` next to `approval_contract` and `concept_contract`. Import the constant or use the literal with a comment naming it.
- In `join_reviews`, compute `label_only = state.get('join_contract', 1) >= LABEL_ONLY_JOIN` after the existing early-return and independence checks.
  - When `label_only` is true and any finding with `review_id == CONFLICT` and `status != 'resolved'` exists, raise the FlowError above.
  - In the cell loop, when the dispositions differ and `label_only` is true:
    - set `decision['disagreement'] = True`;
    - append the dict from the Interfaces block, taking each side's `evidence` as written before the merge;
    - do not append to `conflicts`.
  - When `label_only` is true:
    - skip the `rechecks`, `compared` and `adjudicate(...)` block;
    - replace this candidate's disagreements with `state['applicability_disagreements'] = [d for d in existing if d['candidate_digest'] != digest] + new`.

  The rest, from publishing the joined audit onward, is unchanged.

- [ ] **Step 5: Run the findings suite**

Run: `python3 -m pytest -q test_pack_findings.py`
Expected: `45 passed` (40 existing plus 5 new).

- [ ] **Step 6: Run the wider runner suites that touch the join**

Run: `python3 -m pytest -q test_pack_flow.py test_pack_graph.py test_parallel_pack_integration.py test_learning_style_flow.py`
Expected: all pass. If a test there relied on a `review-join` finding, pin it with `pin_join_contract(run, 1)` in the same way and record its name in the commit body.

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/ec2-review-pack/scripts/pack_findings.py .claude/skills/ec2-review-pack/scripts/pack_flow.py .claude/skills/ec2-review-pack/tests/test_pack_findings.py
git commit -m "fix(review): record note-review label disagreements instead of routing them to authors"
```

---

### Task 2: Disagreement summary in report.json

**Files:**
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_findings.py` (new function after `join_reviews`)
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_actions.py:540-556` (`write_report`, parallel-only dict)
- Test: `.claude/skills/ec2-review-pack/tests/test_pack_findings.py`

**Interfaces:**
- Consumes: `state['applicability_disagreements']` and `state['joined_review']['candidate_digest']` from Task 1, and `state['active_audit']`, the path of the merged audit JSON.
- Produces: `pack_findings.applicability_summary(state: dict) -> dict`. It returns `dict(current: int, history: int, by_rule: dict[str, int], cells: int | None, items: list[dict])`.
  - `current`, `by_rule` and `items` count only the entries whose `candidate_digest` equals the joined candidate digest.
  - `history` is `len` of the whole list.
  - `cells` is the sum of `len(item['rules'])` over the active audit's items, or `None` when there is no active audit.
  - `report.json` gets key `applicability` with this dict for parallel RUNs.

- [ ] **Step 1: Write the failing tests**

```python
def test_summary_before_join_is_empty(note_run):
    from pack_findings import applicability_summary
    assert applicability_summary(flow.load_state(note_run[0])) == dict(current=0, history=0, by_rule={}, cells=None, items=[])

def test_summary_counts_current_disagreements_and_reaches_report(note_run):
    from pack_findings import applicability_summary
    run, _ = note_run
    submit_review(note_run, 'content-review', disposition='applied')
    state = submit_review(note_run, 'style-audit')
    audit = json.loads(Path(state['active_audit']).read_text())
    rule = next(iter(audit['items']['s1-mean']['rules']))
    summary = applicability_summary(state)
    assert (summary['current'], summary['history'], summary['by_rule']) == (1, 1, {rule: 1})
    assert summary['cells'] == sum(len(i['rules']) for i in audit['items'].values())
    assert flow._read(run/'report.json')['applicability'] == summary

def test_summary_counts_only_current_candidate(note_run):
    from pack_findings import applicability_summary
    submit_review(note_run, 'content-review', disposition='applied')
    state = submit_review(note_run, 'style-audit')
    old = dict(state['applicability_disagreements'][0], candidate_digest='older-candidate')
    state['applicability_disagreements'].append(old)
    summary = applicability_summary(state)
    assert (summary['current'], summary['history']) == (1, 2)
```

If `report.json` is not rewritten when the review is accepted, call `pack_actions.write_report(run)` before reading it in the second test, and note this in the commit body.

- [ ] **Step 2: Run to confirm failure**

Run: `python3 -m pytest -q test_pack_findings.py -k summary`
Expected: FAIL with `ImportError: cannot import name 'applicability_summary'`.

- [ ] **Step 3: Implement `applicability_summary(state)` and add `'applicability': applicability_summary(state)` to the parallel-only dict in `write_report`**

Use `collections.Counter` for `by_rule` and convert it to a plain dict. Read the active audit with `f._read`.

- [ ] **Step 4: Run the findings and actions suites**

Run: `python3 -m pytest -q test_pack_findings.py test_pack_actions.py`
Expected: all pass. The findings suite now has 48 passed.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ec2-review-pack/scripts/pack_findings.py .claude/skills/ec2-review-pack/scripts/pack_actions.py .claude/skills/ec2-review-pack/tests/test_pack_findings.py
git commit -m "feat(review): report note-review applicability disagreements per rule"
```

---

### Task 3: Shared label semantics for both note reviewers

**Files:**
- Create: `.claude/skills/ec2-review-pack/references/note-rule-applicability.md`
- Modify: `.claude/skills/ec2-review-pack/references/review-prompt.md:9` (last sentence of the parallel-RUN paragraph)
- Modify: `.claude/skills/ec2-review-pack/scripts/pack_flow.py:737-738` (`_REFERENCES` entries for `style-audit` and `content-review`)
- Test: `.claude/skills/ec2-review-pack/tests/test_pack_findings.py`

**Interfaces:**
- Consumes: the `note_run` fixture; `flow.claim_task` and `flow.release_task`.
- Produces: both note-review briefs list `references/note-rule-applicability.md`.

- [ ] **Step 1: Write the failing test**

```python
def test_note_reviewers_read_shared_applicability_reference(note_run):
    run, _ = note_run
    for tid in ('style-audit', 'content-review'):
        claim = flow.claim_task(run, tid)
        refs = flow._read(claim['brief'])['references']
        paths = [r['path'] if isinstance(r, dict) else r for r in refs]
        assert any(str(p).endswith('references/note-rule-applicability.md') for p in paths)
        flow.release_task(run, tid, claim['attempt'], 'reference check only')
```

- [ ] **Step 2: Run to confirm failure**

Run: `python3 -m pytest -q test_pack_findings.py::test_note_reviewers_read_shared_applicability_reference`
Expected: FAIL on the `any(...)` assertion.

- [ ] **Step 3: Write the reference document and wire it in**

- Create `note-rule-applicability.md` with the title `# 노트 토픽의 규칙 적용 표시`, then these two sections copied verbatim from spec §5:
  - `## 표시의 뜻` (three bullets)
  - `## 노트 토픽에서의 대상` (the 8-row table and the sentence about the remaining rules)

  Add a first line under the title: `초안 — 사용자 확인 전 (2026-11-21).`
- In `review-prompt.md` line 9, replace the sentence `같은 토픽·규칙의 적용 여부가 엇갈리면 두 보고의 원문 근거를 다시 대조한다.` with the blockquoted paragraph from spec §4, without the `>`.
- Append `('note-rule-applicability.md', '전체')` to both the `'style-audit'` and `'content-review'` lists in `_REFERENCES`.

- [ ] **Step 4: Run the test and the brief-related suites**

Run: `python3 -m pytest -q test_pack_findings.py test_pack_flow.py test_pack_receipts.py`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/ec2-review-pack/references/note-rule-applicability.md .claude/skills/ec2-review-pack/references/review-prompt.md .claude/skills/ec2-review-pack/scripts/pack_flow.py .claude/skills/ec2-review-pack/tests/test_pack_findings.py
git commit -m "docs(review): give both note reviewers one applicability reading"
```

---

### Task 4: Full-suite check

- [ ] **Step 1: Run the whole skill suite**

Run: `python3 -m pytest -q` (from `.claude/skills/ec2-review-pack/tests`)
Expected: no failures. Any test pinned to contract 1 is listed in a Task 1 commit body.

- [ ] **Step 2: Stop for the user**

Report the branch, the commits and the pinned tests. Ask the user to confirm the applicability table in `note-rule-applicability.md` before merging. Do not merge or push.
