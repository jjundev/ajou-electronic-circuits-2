# Exam-first selection implementation

User decision: at most 20 whole questions, past exams first, reference solutions optional, and questions used in any other pack always excluded (including prerequisites). Same-range regeneration remains allowed.

## Implemented

- Versioned `exam-first-v2` selection policy; legacy manifests remain readable.
- Catalog/candidate schema v2 separates source eligibility from reference solution availability and exposes previous-use ranges and question-part groups.
- Selection audit requires dispositions for selected questions and all unused exam candidates, coverage matching learning goals, and reasons for deferred concepts or uncovered core goals.
- New-policy CLI requires the previous-use directory and the exact current range exemption. Other-pack reuse, partial adoption, missing/reversed prerequisites, and more than 20 questions fail.
- Shared selection metadata carries core/extra priority, goals, source part-group counts and estimated minutes. The renderer labels counts as groups and times as estimates.
- Explanation inputs hash `.assets/selection.json`; answer overlays bind the same metadata. Both PDF modes and explanation HTML/MD display it. The assembly/rollback procedures preserve the selection and audit records.
- Generation rules require exam-first semantic review, whole-question scope checks, deferred-question reconsideration, cross-pack gap review, and independent solving without using reference-solution availability as a preference.

## Verification

- Workbook full unittest suite: 130 passed, including rendering and PDF layout checks.
- Selector/manifest/assembly and explanation source/render regression suites run separately; added tests cover unsolved candidate inclusion, an unsolved exam through the selection CLI, 20/21 limits, strict history/prerequisite rejection, coverage, metadata hashing and backup/rollback.
- Real repository chapter-10 candidate smoke check: 186 candidates, 35 exams, 32 previously used candidates marked; all 35 current exam candidates happen to have reference solutions. Unsolved behavior is exercised with synthetic source fixtures instead.
- Chrome screenshot and PDF smoke review: core/extra labels and part-group/time estimates visible in both modes, no page errors or overflow. Evidence: `C:/Users/Hyunjun/.codex/scratch/review-pack/exam-first-policy-20261022/`.
- Existing 1007 outputs and workbook source Markdown were not modified.
- `git diff --check` passes. `.agents/skills` and `.claude/skills` resolve to the same skill directories.

## Existing failures kept separate

The full explanation unittest suite has 7 failures/errors related to missing/mismatched personal-style reference hashes in publication test fixtures. All 7 reproduce using the HEAD versions of the affected explanation modules/tests in a scratch baseline. The review-pack skill-file suite has one Windows/NFD backup path/hash failure; its HEAD backup snippet reproduces the same failure. The answer-publication hash gate was not weakened. These suites are not reported as fully passing.

No existing pack regeneration, source-solution edits, commit or push was performed.
