import hashlib
import json
from pathlib import Path
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
CLI = SKILL / "scripts/concept.py"


def invoke(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], text=True, capture_output=True)


def test_template_matches_pinned_digest():
    template = SKILL / "assets/review-template.html"
    assert hashlib.sha256(template.read_bytes()).hexdigest() == (
        "b8df4750f44ce1e6e4487133049e480cf1be2236d92bd6d8af8a56df2d400927"
    )


def test_existing_pack_stages_without_ds_manifest(tmp_path):
    pack = tmp_path / "복습노트/1113"
    assets = pack / ".assets"
    assets.mkdir(parents=True)
    note = pack / "정리노트_1113_Feedback.html"
    note.write_text('<article class="topic" id="s1-return"><span class="tag date">1113 수업</span>'
                    '<span class="tag slide">L06 s24</span></article>', encoding="utf-8")
    (assets / "정리노트_1113_Feedback.md").write_text("# 전류 반송", encoding="utf-8")
    (tmp_path / "STT").mkdir()
    (tmp_path / "STT/1113 전회2.md").write_text("## Part 01\n전류 반송", encoding="utf-8")
    run = tmp_path / "scratch"
    result = invoke("prepare", "1113", "--repo", tmp_path, "--run", run)
    assert result.returncode == 0, result.stderr
    source = json.loads((run / "source.json").read_text(encoding="utf-8"))
    assert source["slug"] == "Feedback"
    assert list(source["topics"]) == ["s1-return"]
    assert not list(pack.glob("확인문제*"))
    result = invoke("publish", "--run", run)
    assert result.returncode == 1
    assert not list(pack.glob("확인문제*"))
