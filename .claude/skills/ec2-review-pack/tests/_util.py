"""스킬 테스트 공통 경로·도우미."""

from __future__ import annotations

import os
import json
import shutil
import tempfile
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


# RUN folders and publication locks made by tests stay out of the user's ~/.cache.
# A spawned process re-imports this module and must keep its parent's locks.
if "EC2_CACHE_ROOT" not in os.environ:
    _cache_temp = tempfile.TemporaryDirectory(prefix="ec2-test-cache-", ignore_cleanup_errors=True)
    os.environ["EC2_CACHE_ROOT"] = _cache_temp.name


def aliases_nfd(folder: Path) -> bool:
    """Whether this filesystem opens an NFC name through its NFD spelling (APFS does, NTFS does not)."""
    name = unicodedata.normalize("NFC", "전자회로 별칭")
    probe = Path(folder) / name
    probe.mkdir()
    try:
        return (Path(folder) / unicodedata.normalize("NFD", name)).is_dir()
    finally:
        probe.rmdir()


def find_nfc(directory: Path, name: str) -> Path | None:
    """macOS NFD 파일명을 NFC 이름으로 찾는다."""
    if not directory.is_dir():
        return None
    for entry in os.listdir(directory):
        if unicodedata.normalize("NFC", entry) == name:
            return directory / entry
    return None


# The tracked mini-run is a portable template; no environment-specific profile
# hash or claimed real review is committed. These approvals are synthetic tests.
sys.path.append(str(REPO / "workbook"))
from learning_style import read_style


def prepare_mini_run(destination: Path, repo: Path = REPO) -> Path:
    shutil.copytree(FIXTURES / "mini-run", destination)
    m = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    m["learning_style"] = read_style(repo)
    (destination / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    audit = {"learning_style": m["learning_style"], "items": {
        topic["id"]: {"status": "pass", "reviewer": "synthetic test reviewer", "rules": {
            rid: {"disposition": "not_applicable", "evidence": "synthetic fixture; no semantic approval"}
            for rid in m["learning_style"]["rule_ids"]}}
        for section in m["sections"] for topic in section["topics"]}}
    (destination / "learning-style-audit.json").write_text(json.dumps(audit), encoding="utf-8")
    return destination


_mini_temp = tempfile.TemporaryDirectory(prefix="ec2-mini-run-")
MINI_RUN = prepare_mini_run(Path(_mini_temp.name) / "run")
