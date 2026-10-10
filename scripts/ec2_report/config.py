"""과목정보(.claude/과목정보.md)와 설계과제 보고서 경로."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

INFO_REL = Path(".claude") / "과목정보.md"
REQUIRED = ("department", "course", "course_code", "professor", "class_section",
            "student_id", "student_name", "date_format", "chrome")
IDENTITY = ("professor", "class_section", "student_id", "student_name")
KIND = "보고서"


def find_root(start: Path | None = None) -> Path:
    here = Path(start or __file__).resolve()
    for d in (here, *here.parents):
        if (d / INFO_REL).is_file():
            return d
    raise FileNotFoundError(f"{INFO_REL} 를 찾지 못했습니다 (시작: {here})")


def _frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("과목정보.md 첫 줄이 --- 가 아닙니다")
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    raise ValueError("과목정보.md frontmatter 가 닫히지 않았습니다")


def load_course_info(root: Path) -> dict:
    text = (Path(root) / INFO_REL).read_text(encoding="utf-8")
    info = yaml.safe_load(_frontmatter(text)) or {}
    for key in REQUIRED:
        if key not in info:
            raise ValueError(f"과목정보.md 에 {key} 가 없습니다")
    info.setdefault("notion_parent_page_id", None)
    return info


def missing_identity(info: dict) -> list[str]:
    return [k for k in IDENTITY if info.get(k) in (None, "")]


def assignment_dir(n: int, root: Path) -> Path:
    d = Path(root) / "설계과제" / f"과제{n}"
    if not d.is_dir():
        raise FileNotFoundError(f"과제 폴더가 없습니다: {d}")
    return d


def document_title(n: int) -> str:
    return f"전자회로2 설계과제{n} 보고서"


@dataclass(frozen=True)
class ReportPaths:
    report_md: Path
    notion_dir: Path
    cover_html: Path
    cover_pdf: Path
    final_pdf: Path

    def baseline(self, v: int) -> Path:
        return self.notion_dir / f"baseline_v{v}.md"

    def pulled(self, v: int) -> Path:
        return self.notion_dir / f"pulled_v{v}.md"


def paths(n: int, root: Path, info: dict) -> ReportPaths:
    a = assignment_dir(n, root)
    report = a / "report"
    return ReportPaths(
        report_md=report / f"설계과제{n}_보고서.md",
        notion_dir=report / "notion",
        cover_html=report / f"설계과제{n} 표지.html",
        cover_pdf=report / f"설계과제{n} 표지.pdf",
        final_pdf=a / f"전자회로2_설계과제{n}_{info['student_id']}_{info['student_name']}.pdf",
    )
