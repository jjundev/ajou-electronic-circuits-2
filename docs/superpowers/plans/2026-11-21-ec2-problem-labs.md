# EC2 Problem Labs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Publish a verified E12.27 circuit lab in the 1120 explanations and automatically consider up to one lab per future pack.

**Architecture:** The explanation coordinator ranks eligible proposals from reviewed reasoning. The interactive skill builds and verifies the selected lab in the run. The existing explanation assembler and publication gates own the lab and its links.

**Tech Stack:** Python, Node.js, native SVG, MNA, Playwright.

**Spec:** The approved chat design and decision #6, summarized under Global Constraints.

## Global Constraints

- One meaningful circuit decision per lab and at most one lab per new pack.
- Match by workbook ID, subpart, section and current explanation input digest.
- Stage the lab and require the four interactive gates with source and HTML hashes. Keep the existing explanation reviews and answer selection.
- Use a separate HTML and relative links from the explanation HTML and Markdown. A lab failure yields a regular explanation and a diagnostic.
- Stage E12.27 for 1120 first. Students predict the output load, choose an open or short termination and see the resulting current path. Mark demo values clearly.

## Review Focus

- Two eligible proposals select at most one by first-step priority and current problem order.
- An unknown workbook ID or stale reviewed brief must never attach to a different problem.
- A missing or changed lab artifact cannot appear in a published link.
- A linked lab must survive an intact rerender and retain the PDF answer extraction.
- Opening both relative links must work from their respective published directories.

---

### Task 1. Candidate selection, assembly and validation

**Files:** Create `.claude/skills/ec2-problem-explain/scripts/epe_labs.py` and `.claude/skills/ec2-problem-explain/tests/test_labs.py`. Modify `epe_cli.py`, `epe_render.py` and `epe_rerender.py` in the same skill.

**Interfaces:** Candidate proposals live in the bucket as `lab-candidates.json`. `select-lab --run RUN` chooses one and binds its brief to the current explanation input digest in `bucket/lab/brief.json`. A completed candidate also has `lab.js`, `index.html`, and `lab-validation.json` in that directory. `load_lab(bucket, pack, fragments)` yields the verified lab or no attachment and a diagnostic.

- [x] Add regressions for first-step priority, stable ID, rejected hashes, answer overlay equivalence, HTML and MD links, and rerender.
- [x] Run `python3 -m pytest .claude/skills/ec2-problem-explain/tests/test_labs.py -q` and observe missing feature failures.
- [x] Add selection, validation, stage assembly, and verified rerender to the existing CLI. Feed lab files through the existing manifest and publication path.
- [x] Run the lab tests and existing EPE checks.

### Task 2. Verify and publish the 1120 pilot

**Files:** E12.27 under the existing explanation's `.assets/자료_문제설명_1120_Nonideal_IO_Feedback/labs/E12.27/` ownership, plus the explanation HTML, MD and validation metadata.

- [x] Use the existing fragments and reviews under the rerender rules. Build the two-state bench with `R_1=12~kΩ`, `R_2=8~kΩ`, `v_o=1~V` as example settings.
- [x] Check both states independently. Open gives 20 kΩ and 50 µA through both resistors. Short gives 12 kΩ and about 83.33 µA through R1 with zero current through R2.
- [x] Run check.cjs, steps.cjs, the offline browser probe and visible browser interaction. Confirm HTML and MD links, stage review and publication. Compare protected notes and PDFs.

### Task 3. Enable automatic selection for new packs

**Files:** Update the explanation and interactive skill instructions and parent integration instructions.

- [x] Put automatic evaluation after the independent result is adopted and before the final explanation build. Use the same contract for direct and legacy calls and the parallel child coordinator. Keep selection and lab creation optional.
- [x] Test an eligible candidate, an ineligible candidate, two eligible candidates, and an unsuccessful lab in the existing candidate-publication path.
- [x] Inspect the resulting changes and report local validation and Git state.

## Verification

- The pilot passed independent KCL, 32 offline probe checks, and visible Chromium interaction at desktop and mobile sizes in both themes.
- The explanation suite passed 236 tests. The interactive JavaScript suite passed 79 tests. A parallel pack fixture carried the verified lab through publication.
- The published HTML and Markdown links resolve to the same lab. A new rerender retained its approved files. The protected note, PDFs, and answer overlay matched their original hashes.
