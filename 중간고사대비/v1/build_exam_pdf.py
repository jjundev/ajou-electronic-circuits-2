#!/usr/bin/env python3
"""전자회로2 중간고사 실전 대비 모의고사 (v1) 16:9 와이드스크린 문제지/답안지 PDF 렌더러.

저장소 공식 워크북 템플릿(workbook/templates/problem.html, answer.html)과
video-16x9.css 레이아웃 규격을 100% 사용하여 복습팩(ec2-problem-explain)과 동일한
공식 양식의 16:9 문제지 및 답안지 PDF를 빌드합니다.
"""

import base64
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Add repo root and workbook to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "workbook"))

import yaml
from mdsub import answer_html, inline, to_html
from render import inject, load_template, render_pdf

BASE = ROOT / "중간고사대비" / "v1"
ASSETS = BASE / ".assets"
MD_DIR = ASSETS / "md"
FIG_DIR = ASSETS / "figures"
BUILD_DIR = BASE / "build"

FIG_MAP = {
    1: [],
    2: ["fig-Q2a.svg", "fig-Q2b.svg"],
    3: ["fig-Q3a.svg", "fig-Q3b.svg"],
    4: ["fig-Q4a.svg", "fig-Q4b.svg"],
    5: ["fig-Q5.svg"],
}


def parse_sections(text: str) -> dict[str, str]:
    """Split markdown by ## heading."""
    sections = {}
    current_title = ""
    current_lines = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines).strip()
    return sections


def split_subsections(text: str) -> list[tuple[str, str]]:
    """Split text by ### or #### heading into fine-grained (label, body) steps."""
    subs = []
    current_label = ""
    current_lines = []

    for line in text.splitlines():
        if line.startswith("### ") or line.startswith("#### "):
            heading_text = line.lstrip("#").strip()
            if current_label and (current_lines or not heading_text.startswith("답")):
                body_content = "\n".join(current_lines).strip()
                if body_content or current_label.startswith("답"):
                    subs.append((current_label, body_content))
            current_label = heading_text
            current_lines = []
        elif current_label:
            current_lines.append(line)

    if current_label:
        subs.append((current_label, "\n".join(current_lines).strip()))
    return subs


def load_svg_figure(fig_name: str, total_figs: int = 1) -> dict:
    svg_path = FIG_DIR / fig_name
    raw = svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(raw)
    vb = root.attrib.get("viewBox", "0 0 800 500").split()
    w = float(vb[2])
    h = float(vb[3])

    b64 = base64.b64encode(svg_path.read_bytes()).decode("ascii")
    src = f"data:image/svg+xml;base64,{b64}"

    # Target width in mm for 16:9 layout
    base_w_mm = 90.0 if total_figs > 1 else 115.0
    h_mm = round(base_w_mm * (h / w), 1)

    return {
        "src": src,
        "w_mm": base_w_mm,
        "h_mm": h_mm,
    }


def build_exam_data(mode: str) -> dict:
    display_titles = json.loads((ASSETS / "display-titles.json").read_text(encoding="utf-8"))

    title_suffix = " 답안" if mode == "answers" else ""
    meta = {
        "mode": mode,
        "title": f"2026-2 전자회로2 중간고사 실전 모의고사 (v1){title_suffix}",
        "chapter": 0,
        "total": 5,
        "layout": "video-16x9",
    }

    problems = []
    for i in range(1, 6):
        md_file = MD_DIR / f"Q{i}.md"
        raw_text = md_file.read_text(encoding="utf-8")
        parts = raw_text.split("---")
        fm = yaml.safe_load(parts[1])
        body = "---".join(parts[2:])

        sections = parse_sections(body)
        orig_text = sections.get("원문", "")
        cond_text = sections.get("조건", "")
        ask_text = sections.get("구할 것", "")

        q_id = fm["id"]
        title = display_titles.get(q_id, fm.get("title", f"Q{i}"))

        # Figures
        fig_names = FIG_MAP.get(i, [])
        figs = [load_svg_figure(fn, len(fig_names)) for fn in fig_names]

        prob_entry = {
            "id": q_id,
            "kind": "기출",
            "number": str(i),
            "title": title,
            "section": "전자회로2 중간고사 모의고사 (v1) · 20점",
            "book_page": None,
            "difficulty": 0,
            "sol": False,
            "original_lang": "ko",
            "html": {
                "original": to_html(orig_text),
                "conditions": to_html(cond_text),
                "ask": to_html(ask_text),
            },
            "figures": figs,
        }

        if mode == "answers":
            sol_text = sections.get("풀이", "")
            subs = split_subsections(sol_text)
            if subs:
                # Last subsection is answer if titled '답'
                if subs[-1][0].strip().startswith("답"):
                    steps = [{"label": inline(lbl), "html": to_html(bdy)} for lbl, bdy in subs[:-1]]
                    ans = answer_html(subs[-1][1])
                else:
                    steps = [{"label": inline(lbl), "html": to_html(bdy)} for lbl, bdy in subs]
                    ans = ""
            else:
                steps = []
                ans = to_html(sol_text)

            prob_entry["solution"] = {
                "steps": steps,
                "answer": ans,
                "paginate": True,
            }

        problems.append(prob_entry)

    return {"meta": meta, "problems": problems}


def render_exam_pdf(mode: str) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "답안" if mode == "answers" else "문제"
    data = build_exam_data(mode)

    json_path = BUILD_DIR / f"중간고사대비_v1-{suffix}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    template = load_template(mode, layout="video-16x9")
    html_content = inject(template, data)

    html_path = BUILD_DIR / f"중간고사대비_v1-{suffix}.html"
    html_path.write_text(html_content, encoding="utf-8")

    pdf_path = BASE / f"중간고사대비_v1-{suffix}.pdf"
    print(f"Rendering {pdf_path.name} from {html_path.name}...")
    overflow = render_pdf(html_path, pdf_path)
    if overflow:
        print(f"Warning: Overflow on pages: {overflow}")
    else:
        print(f"Success: {pdf_path.name} rendered with zero overflow.")
    return pdf_path


def main():
    prob_pdf = render_exam_pdf("problems")
    ans_pdf = render_exam_pdf("answers")
    print(f"\nAll PDFs generated successfully in official review-pack format:")
    print(f"- Problem PDF: {prob_pdf}")
    print(f"- Answer PDF:  {ans_pdf}")


if __name__ == "__main__":
    main()
