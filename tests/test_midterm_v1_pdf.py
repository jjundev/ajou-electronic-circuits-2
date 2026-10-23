from pathlib import Path
from pypdf import PdfReader


def test_midterm_v1_pdfs():
    base = Path("중간고사대비/v1")
    prob_pdf = base / "중간고사대비_v1-문제.pdf"
    ans_pdf = base / "중간고사대비_v1-답안.pdf"
    assert prob_pdf.is_file(), f"{prob_pdf} does not exist"
    assert ans_pdf.is_file(), f"{ans_pdf} does not exist"

    reader_p = PdfReader(prob_pdf)
    assert len(reader_p.pages) >= 5, f"Expected at least 5 pages in problem pdf, got {len(reader_p.pages)}"
    # 16:9 와이드스크린 비율 검증 (1920x1080 approx ratio 1.77)
    box = reader_p.pages[0].mediabox
    ratio = float(box.width) / float(box.height)
    assert 1.7 <= ratio <= 1.85, f"Expected 16:9 ratio (1.7~1.85), got {ratio:.4f}"

    reader_a = PdfReader(ans_pdf)
    assert len(reader_a.pages) >= 5, f"Expected at least 5 pages in answer pdf, got {len(reader_a.pages)}"
    box_a = reader_a.pages[0].mediabox
    ratio_a = float(box_a.width) / float(box_a.height)
    assert 1.7 <= ratio_a <= 1.85, f"Expected 16:9 ratio (1.7~1.85), got {ratio_a:.4f}"
