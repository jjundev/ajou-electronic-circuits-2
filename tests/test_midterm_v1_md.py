from pathlib import Path
import re


def test_midterm_v1_md_files_exist_and_valid():
    md_dir = Path("중간고사대비/v1/.assets/md")
    for i in range(1, 6):
        path = md_dir / f"Q{i}.md"
        assert path.is_file(), f"Q{i}.md missing"
        text = path.read_text(encoding="utf-8")
        assert "## 문제" in text, f"Q{i}.md missing '## 문제'"
        assert "## 풀이" in text, f"Q{i}.md missing '## 풀이'"
        assert ("20점" in text or "배점: 20" in text or "20" in text), f"Q{i}.md missing score 20"
        assert "$$" in text, f"Q{i}.md missing display math formula $$"


def test_midterm_v1_md_subparts_and_scores():
    md_dir = Path("중간고사대비/v1/.assets/md")
    
    # Q1: 3 subparts (a: 7, b: 7, c: 6)
    q1 = (md_dir / "Q1.md").read_text(encoding="utf-8")
    assert "(a)" in q1 and "(b)" in q1 and "(c)" in q1
    assert "7점" in q1 and "6점" in q1
    
    # Q2: 2 subparts (a: 10, b: 10)
    q2 = (md_dir / "Q2.md").read_text(encoding="utf-8")
    assert "(a)" in q2 and "(b)" in q2
    assert "10점" in q2
    assert "fig-Q2a.svg" in q2 and "fig-Q2b.svg" in q2
    
    # Q3: 2 subparts (a: 10, b: 10)
    q3 = (md_dir / "Q3.md").read_text(encoding="utf-8")
    assert "(a)" in q3 and "(b)" in q3
    assert "10점" in q3
    assert "fig-Q3a.svg" in q3 and "fig-Q3b.svg" in q3
    
    # Q4: 2 subparts (a: 10, b: 10)
    q4 = (md_dir / "Q4.md").read_text(encoding="utf-8")
    assert "(a)" in q4 and "(b)" in q4
    assert "10점" in q4
    assert "fig-Q4a.svg" in q4 and "fig-Q4b.svg" in q4
    
    # Q5: 4 subparts (1: 5, 2: 5, 3: 5, 4: 5)
    q5 = (md_dir / "Q5.md").read_text(encoding="utf-8")
    assert "(1)" in q5 and "(2)" in q5 and "(3)" in q5 and "(4)" in q5
    assert "5점" in q5
    assert "fig-Q5.svg" in q5
