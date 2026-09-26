"""스킬 테스트 공통 경로·도우미."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import unicodedata

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parent
SCRIPTS = SKILL / "scripts"
FIXTURES = TESTS / "fixtures"
MINI_RUN = FIXTURES / "mini-run"
REPO = SKILL.parents[2]  # <repo>/.claude/skills/ec2-review-pack

# 템플릿 원본(머신러닝기초 저장소). 없으면 비교 테스트를 건너뛴다.
# 워크트리에서 REPO.parent가 .claude/worktrees이므로, 부모 디렉토리를 순회하여 찾는다.
ML_SKILL = None
for p in [REPO, *REPO.parents]:
    candidate = p.parent / "머신러닝기초" / ".claude" / "skills" / "ml-review-pack"
    if candidate.exists():
        ML_SKILL = candidate
        break
if ML_SKILL is None:
    ML_SKILL = REPO.parent / "머신러닝기초" / ".claude" / "skills" / "ml-review-pack"

sys.path.insert(0, str(SCRIPTS))


def find_nfc(directory: Path, name: str) -> Path | None:
    """macOS NFD 파일명을 NFC 이름으로 찾는다."""
    if not directory.is_dir():
        return None
    for entry in os.listdir(directory):
        if unicodedata.normalize("NFC", entry) == name:
            return directory / entry
    return None
