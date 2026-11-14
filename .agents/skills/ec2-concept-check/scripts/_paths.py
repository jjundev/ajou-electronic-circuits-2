"""Shared skill, vendored assets and repository paths."""
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[2]
REVIEW_PACK = REPO / ".claude/skills/ec2-review-pack"
VENDOR_REL = Path("복습노트/.assets/vendor")
