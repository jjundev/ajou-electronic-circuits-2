from pathlib import Path
import xml.etree.ElementTree as ET
import re
import pytest

EXPECTED_FIGURES = [
    "fig-Q2a.svg",
    "fig-Q2b.svg",
    "fig-Q3a.svg",
    "fig-Q3b.svg",
    "fig-Q4a.svg",
    "fig-Q4b.svg",
    "fig-Q5.svg",
]

def test_midterm_v1_figures_exist():
    fig_dir = Path("중간고사대비/v1/.assets/figures")
    assert fig_dir.exists(), f"Figure directory {fig_dir} does not exist"
    for fig_name in EXPECTED_FIGURES:
        fig_path = fig_dir / fig_name
        assert fig_path.exists(), f"Figure {fig_name} is missing in {fig_dir}"

def test_midterm_v1_svg_standards():
    fig_dir = Path("중간고사대비/v1/.assets/figures")
    svgs = list(fig_dir.glob("*.svg"))
    assert len(svgs) >= 7, f"Expected at least 7 SVGs, found {len(svgs)}"
    for svg in svgs:
        tree = ET.parse(svg)
        root = tree.getroot()
        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        assert tag == "svg", f"{svg.name} root tag is {tag}, expected svg"
        assert "viewBox" in root.attrib or ("width" in root.attrib and "height" in root.attrib)
        
        text = svg.read_text(encoding="utf-8")
        assert "font-family" in text or "Pretendard" in text
        assert "Pretendard" in text, f"{svg.name} should specify Pretendard font"
        assert "<tspan" in text, f"{svg.name} should use <tspan> for subscripts"

def test_midterm_v1_baseline_restoration():
    fig_dir = Path("중간고사대비/v1/.assets/figures")
    for fig_name in EXPECTED_FIGURES:
        svg_path = fig_dir / fig_name
        text = svg_path.read_text(encoding="utf-8")
        text_nodes = re.findall(r'<text[^>]*>(.*?)</text>', text, re.DOTALL)
        for tn in text_nodes:
            parts = re.split(r'(<tspan[^>]*>.*?</tspan>)', tn)
            current_dy = 0
            for part in parts:
                if not part:
                    continue
                m_dy = re.search(r'dy="([+-]?\d+)"', part)
                if m_dy:
                    current_dy += int(m_dy.group(1))
                elif part.strip():
                    assert current_dy == 0, (
                        f"In {fig_name}, plain text '{part}' is rendered at shifted baseline "
                        f"(drift = {current_dy}): full node='{tn}'"
                    )

def test_figure_labels_and_circuit_components():
    fig_dir = Path("중간고사대비/v1/.assets/figures")
    
    # Q2a: 소스 축퇴 저항 RS NMOS 전류 거울 (M1, M2, I_REF, RS, Vout)
    q2a_text = (fig_dir / "fig-Q2a.svg").read_text(encoding="utf-8")
    assert "M" in q2a_text and "1" in q2a_text
    assert "M" in q2a_text and "2" in q2a_text
    assert "REF" in q2a_text
    assert "out" in q2a_text
    
    # Q2b: NPN/PNP 복합 바이어스 CE 증폭기 (Q1, Q2, Vin, Vout)
    q2b_text = (fig_dir / "fig-Q2b.svg").read_text(encoding="utf-8")
    assert "Q" in q2b_text
    assert "in" in q2b_text
    assert "out" in q2b_text
    
    # Q3a: 기생 저항 RP MOS 캐스코드 증폭기 (M1, M2, RP, Vin, Vout)
    q3a_text = (fig_dir / "fig-Q3a.svg").read_text(encoding="utf-8")
    assert "M" in q3a_text and "1" in q3a_text
    assert "M" in q3a_text and "2" in q3a_text
    assert "P" in q3a_text
    assert "in" in q3a_text
    assert "out" in q3a_text

    # Q3b: Folded Cascode 증폭기 (Vin, Vout)
    q3b_text = (fig_dir / "fig-Q3b.svg").read_text(encoding="utf-8")
    assert "in" in q3b_text
    assert "out" in q3b_text

    # Q4a: 소스 축퇴 차동 증폭기 및 반회로
    q4a_text = (fig_dir / "fig-Q4a.svg").read_text(encoding="utf-8")
    assert "SS" in q4a_text or "deg" in q4a_text
    assert "in" in q4a_text
    assert "out" in q4a_text

    # Q4b: 능동 전류 거울 부하 차동 증폭기 (M1, M2, M3, M4, ISS, Vin1, Vin2, Vout)
    q4b_text = (fig_dir / "fig-Q4b.svg").read_text(encoding="utf-8")
    assert "M" in q4b_text
    assert "in" in q4b_text
    assert "out" in q4b_text

    # Q5: 부하 불일치 ΔRD 차동 증폭기
    q5_text = (fig_dir / "fig-Q5.svg").read_text(encoding="utf-8")
    assert "D" in q5_text
    assert "SS" in q5_text
    assert "in" in q5_text
    assert "out" in q5_text
