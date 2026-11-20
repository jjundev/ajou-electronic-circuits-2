"""Immutable inputs and staged explanation outputs."""
from dataclasses import dataclass
from pathlib import Path

from epe_shared import StyleSnapshot
from pack_paths import PackPaths

# Pack folders keep only .pack/, HTML and PDF at the top; everything else lives here.
BUNDLE = '.assets'

class ExplainError(ValueError):
    pass

@dataclass(frozen=True)
class Problem:
    id: str
    number: int
    title: str
    source: str
    original_html: str
    conditions_html: str
    ask_html: str
    figures_html: tuple[str, ...]
    reference_steps: tuple[str, ...]
    reference_answer: str
    subparts: tuple[str, ...]
    workbook_id: str
    workload_label: str = ''

@dataclass(frozen=True)
class SourcePack:
    profile: str
    range: str
    slug: str
    path: Path
    sha256: str
    problems: tuple[Problem, ...]
    inputs: tuple[str, ...]
    learning_style: StyleSnapshot
    pack_paths: PackPaths | None = None

    @property
    def folder(self) -> Path:
        """The review pack folder (path is <folder>/.assets/problems.txt)."""
        return self.path.parent.parent

@dataclass(frozen=True)
class Artifacts:
    html: Path
    md: Path
    manifest: Path
    files: tuple[Path, ...]
