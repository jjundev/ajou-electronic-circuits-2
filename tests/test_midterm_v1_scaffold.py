import json
from pathlib import Path


def test_midterm_v1_scaffold_structure():
    base = Path("중간고사대비/v1")
    assert base.is_dir()
    assert (base / "README.md").is_file()
    assert (base / ".assets/display-titles.json").is_file()
    assert (base / ".assets/selection.json").is_file()

    titles = json.loads((base / ".assets/display-titles.json").read_text(encoding="utf-8"))
    assert len(titles) == 5
    for i in range(1, 6):
        assert f"MIDTERM-V1-Q{i}" in titles

    selection = json.loads((base / ".assets/selection.json").read_text(encoding="utf-8"))
    assert selection["total_score"] == 100
    assert len(selection["problems"]) == 5
