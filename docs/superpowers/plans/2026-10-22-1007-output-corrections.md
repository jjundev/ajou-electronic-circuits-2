# 1007 Output Corrections Implementation Plan

> **For agentic workers:** Use the existing review-pack parallel author/reviewer workflow. No commits unless requested.

**Goal:** Apply the approved high-gain teaching convention, concise numbered titles and true SVG mathematical labels to all 1007 outputs and future generation.

**Architecture:** Keep original workbook questions unchanged. Store pack display titles separately, regenerate the reviewed explanation overlay, and build PDFs from approved content.

**Tech Stack:** Python, SVG text/tspan, HTML/Markdown, Playwright, workbook PDF renderer.

**Spec:** User-approved design in the current conversation, 2026-10-22.

## Global Constraints

- Preserve all ten selected questions, subparts, original conditions and figures.
- Use gmro >> 1 and gmRe >> 1 as the course default; Re is a degeneration resistance, not intrinsic re=1/gm.
- Preserve finite rpi and explicitly required original proof expressions.
- Back up current outputs before changing them; preserve existing uncommitted changes.
- Re-review current profile snapshot, all content and rendered outputs before publishing.

## Tasks

- [x] Update shared profile and generation rules, add regression-tested display title support for HTML/MD/PDF.
- [x] Correct ten explanation fragments and concept-note SVG labels and affected high-gain formulas.
- [x] Independently derive affected formulas, compare all final answers and audit all subparts/topics against the current profile.
- [x] Build staged explanations; verify originals, source hashes, HTML/MD and browser layouts in both themes and viewport sizes.
- [x] Publish approved explanations and regenerate both PDFs with the same title map; inspect every raster page, overflow and subtitle margin.
- [x] Run final manifest, note, explanation and regression checks; save current evidence and report.

## Review Focus

- Preserve P10.67's explicitly requested formula while making leading approximations the default elsewhere.
- Retain the mean-load term where mismatch is not assumed small.
- Confirm SVG subscript positioning, color, spacing and exported SVG/PDF equivalence.
- Preserve source identity separately from concise titles.
- Never relabel stale review evidence as a new approval.
