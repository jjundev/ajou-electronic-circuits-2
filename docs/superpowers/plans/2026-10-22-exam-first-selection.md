# Exam-first Selection Implementation Plan

**Goal:** Apply the approved exam-first policy, at most 20 whole questions, with no solution prerequisite and strict exclusion of questions used in other packs.

**Architecture:** Extend the existing candidate/selection pipeline. Keep legacy pack inputs readable; new runs declare `selection_policy: exam-first-v2`. Bind the selected workload metadata to explanation inputs and both PDFs through `.assets/selection.json`. Semantic scope and math approval remain independent agent reviews.

**Spec:** User-approved design and strict no-reuse decision in this conversation, 2026-10-22.

**Constraints:** No regeneration of existing packs, no source problem edits, no automatic commits. Same-range regeneration remains allowed, but a question used anywhere else remains forbidden, including dependencies.

- [x] Add failing tests for unsolved candidates, 20/21 limits, strict reuse, audit and workload metadata.
- [x] Separate catalog eligibility from reference solution availability; expose use history and subparts.
- [x] Validate versioned selection/audit records, scope/dependency coverage and metadata; retain legacy reads.
- [x] Bind selection metadata to generated HTML and PDFs, with exact ID/order and source hashes.
- [x] Update shared selection specification, skill entrypoints, authoring/review and catalog documentation.
- [x] Run targeted regression suites and real-repository candidate/CLI smoke checks; inspect rendered metadata.
