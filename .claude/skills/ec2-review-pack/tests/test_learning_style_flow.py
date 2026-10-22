"""Real temporary note assembly with synthetic style approvals, not semantic QA."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from _util import REPO, SCRIPTS, MINI_RUN
import assemble
import check_html
import manifest


@pytest.fixture
def note_fixture(tmp_path):
    repo = tmp_path / "repo"
    profile = repo / ".claude/skills/ec2-review-pack/references/solution-style.md"
    profile.parent.mkdir(parents=True)
    shutil.copyfile(REPO / ".claude/skills/ec2-review-pack/references/solution-style.md", profile)
    run = tmp_path / "run"
    shutil.copytree(MINI_RUN, run)
    m = json.loads((run / "manifest.json").read_text())
    for problem in m["problems"]:
        md = manifest.problem_md_path(repo, problem["id"])
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text("synthetic workbook fixture")
    out = tmp_path / "out"
    note = assemble.assemble(run, out, repo=repo)
    (out / manifest.problem_pdf_name(m)).write_bytes(b"%PDF synthetic problem")
    audit_path = run / "learning-style-audit.json"
    class NoteFixture:
        requires_pdf = property(lambda self: bool(m["problems"]))
        def check(self, defer_answer_pdf=False):
            return check_html.check_pack(m, note, repo=repo,
                style_audit=json.loads(audit_path.read_text()), defer_answer_pdf=defer_answer_pdf)
        def check_final_style(self):
            return [p for p in self.check(True) if p.code == "learning-style"]
        def remove_audit_topic(self, topic):
            audit = json.loads(audit_path.read_text()); audit["items"].pop(topic)
            audit_path.write_text(json.dumps(audit))
        def break_unrelated_link(self):
            note.write_text(note.read_text().replace("</body>", '<a href="elsewhere/答안.pdf">unrelated</a></body>'))
        def set_zero_problems(self):
            for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
                note.write_text(note.read_text().replace(f'href="{name}"', 'href="#why-circuit"'))
            m["problems"], m["links"] = [], []
        def change_profile(self):
            profile.write_bytes(profile.read_bytes() + b"\n")
    f = NoteFixture()
    f.repo, f.run, f.out, f.note, f.m, f.audit_path, f.profile = repo, run, out, note, m, audit_path, profile
    return f


def test_manifest_missing_snapshot_fails(note_fixture):
    m = dict(note_fixture.m); m.pop("learning_style")
    assert any("learning_style" in e for e in manifest.validate(m))


@pytest.mark.parametrize("snapshot", [{}, {"path": "elsewhere", "sha256": "0"*64, "rule_ids": ["UNIT-01"]},
    {"path": ".claude/skills/ec2-review-pack/references/solution-style.md", "sha256": "bad", "rule_ids": ["UNIT-01"]},
    {"path": ".claude/skills/ec2-review-pack/references/solution-style.md", "sha256": "0"*64, "rule_ids": ["UNIT-01", "UNIT-01"]}])
def test_manifest_rejects_malformed_snapshot(note_fixture, snapshot):
    m = dict(note_fixture.m, learning_style=snapshot)
    assert manifest.validate(m)


def test_preliminary_defers_only_expected_answer(note_fixture):
    assert note_fixture.check(True) == []
    assert note_fixture.check(False)
    note_fixture.break_unrelated_link()
    assert note_fixture.check(True)


def test_preliminary_preserves_answer_fragment_and_directory_checks(note_fixture):
    f = note_fixture
    expected = manifest.answer_pdf_name(f.m)
    f.note.write_text(f.note.read_text().replace(f'href="{expected}"', f'href="other/{expected}"'))
    assert f.check(True)
    f.note.write_text(f.note.read_text().replace(f'href="other/{expected}"', f'href="{expected}#wrong"'))
    assert f.check(True)


def test_preliminary_preserves_manifest_required_answer_link(note_fixture):
    f = note_fixture
    f.note.write_text(f.note.read_text().replace(f'href="{manifest.answer_pdf_name(f.m)}"', 'href="#why-circuit"'))
    assert any(p.code == "missing-link" for p in f.check(True))


def test_note_style_audit_covers_all_topics(note_fixture):
    note_fixture.remove_audit_topic("why-circuit")
    assert note_fixture.check_final_style()


def test_zero_problem_pack_skips_pdf_without_skipping_style(note_fixture):
    note_fixture.set_zero_problems()
    assert note_fixture.requires_pdf is False
    assert note_fixture.check(False) == []
    note_fixture.change_profile()
    assert note_fixture.check(False)


def test_assembly_rejects_stale_profile_before_writes(note_fixture):
    f = note_fixture
    before = {p: p.read_bytes() for p in f.out.rglob("*") if p.is_file()}
    f.change_profile()
    with pytest.raises(manifest.ManifestError):
        assemble.assemble(f.run, f.out, repo=f.repo)
    assert {p: p.read_bytes() for p in before} == before
    untouched = f.out / "uncreated"
    with pytest.raises(manifest.ManifestError):
        assemble.assemble(f.run, untouched, repo=f.repo)
    assert not untouched.exists()


def test_final_links_pass_only_with_real_answer(note_fixture):
    f = note_fixture
    assert f.check(False)
    (f.out / manifest.answer_pdf_name(f.m)).write_bytes(b"%PDF synthetic answer")
    assert f.check(False) == []


def test_cli_requires_audit_and_labels_preliminary(note_fixture):
    f = note_fixture
    args = ["--manifest", str(f.run / "manifest.json"), "--note", str(f.note), "--repo", str(f.repo)]
    with contextlib.redirect_stdout(io.StringIO()) as output:
        assert check_html.main(args + ["--defer-answer-pdf"]) == 0
    assert "PRELIMINARY: answer PDF pending" in output.getvalue()
    assert "OK" not in output.getvalue()
    with contextlib.redirect_stdout(io.StringIO()):
        assert check_html.main(args) == 1
        f.audit_path.unlink()
        assert check_html.main(args + ["--defer-answer-pdf"]) == 1


def test_cli_default_repo_does_not_skip_style_check(note_fixture):
    f = note_fixture
    f.m["learning_style"]["sha256"] = "0" * 64
    (f.run / "manifest.json").write_text(json.dumps(f.m))
    for tool, args in [("assemble.py", ["--run", str(f.run), "--out", str(f.out / "never")]),
                        ("check_html.py", ["--manifest", str(f.run / "manifest.json"), "--note", str(f.note)])]:
        result = subprocess.run([sys.executable, str(SCRIPTS / tool), *args], capture_output=True, text=True)
        assert result.returncode == 1, result.stdout + result.stderr
        assert "명세" in result.stdout + result.stderr
    assert not (f.out / "never").exists()


def run_rollback(tmp_path, *, old_pack=True, tamper=False):
    """Execute the published recovery recipe with a small coherent synthetic pack."""
    import hashlib
    import re
    from _util import SKILL
    repo, run = tmp_path / "repo", tmp_path / "run"
    pack = repo / "복습노트/0923"
    (pack / ".assets").mkdir(parents=True)
    run.mkdir()
    old_basic = {"정리노트_0923_Old.html": b"old note", ".assets/정리노트_0923_Old.md": b"old md",
                 "복습문제_0923_Old-문제.pdf": b"old problems", "복습문제_0923_Old-답안.pdf": b"old answers",
                 ".assets/problems.txt": b"E9.01 | old"}
    old_explanations = {"문제설명_0923_Old.html": b"old corresponding explanation"}
    expected = {}
    for record_name, old in [("basic-pack-backup", old_basic), ("explanations-backup", old_explanations)]:
        backup = run / record_name
        record = {"range": "0923", "backup": None, "roots": [], "files": {}, "dirs": []}
        if old_pack:
            record["backup"] = str(backup)
            for rel, data in old.items():
                path = backup / rel
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
                record["roots"].append(rel)
                record["files"][rel] = hashlib.sha256(data).hexdigest()
            expected.update(old)
        (run / f"{record_name}.json").write_text(json.dumps(record))
    current = {"정리노트_0923_New.html": b"failed new note", ".assets/problems.txt": b"E9.02 | new",
               "복습문제_0923_New-답안.pdf": b"failed new answer", "문제설명_0923_New.html": b"new explanation"}
    for rel, data in current.items(): (pack / rel).write_bytes(data)
    other = repo / "복습노트/0918/정리노트_0918_A.html"
    other.parent.mkdir(); other.write_bytes(b"other date")
    (pack / "interactive.html").write_bytes(b"unrelated")
    if tamper:
        (run / "basic-pack-backup/복습문제_0923_Old-답안.pdf").write_bytes(b"tampered")
    text = (SKILL / "references/problem-explain-integration.md").read_text()
    snippet = re.search(r'''python3 - "\$REPO" "\$RUN" "\$RANGE" <<'EOF'\n(.*?)\nEOF''', text, re.S)
    assert snippet, "Executable coherent rollback recipe required"
    result = subprocess.run([sys.executable, "-", str(repo), str(run), "0923"], input=snippet.group(1), text=True, capture_output=True)
    assert other.read_bytes() == b"other date"
    assert (pack / "interactive.html").read_bytes() == b"unrelated"
    return result, pack, run, current, expected


@pytest.mark.parametrize("old_pack", [True, False])
def test_recovery_recipe_restores_old_coherent_pack_or_withholds_new(tmp_path, old_pack):
    result, pack, run, current, expected = run_rollback(tmp_path, old_pack=old_pack)
    assert result.returncode == 0, result.stdout + result.stderr
    remaining = {p.relative_to(pack).as_posix(): p.read_bytes() for p in pack.rglob("*") if p.is_file()}
    assert remaining == {**expected, "interactive.html": b"unrelated"}
    withheld = next(run.glob("withheld-*"))
    assert {p.relative_to(withheld).as_posix(): p.read_bytes() for p in withheld.rglob("*") if p.is_file()} == current


def test_recovery_recipe_hash_failure_preserves_current_pack(tmp_path):
    result, pack, run, current, expected = run_rollback(tmp_path, tamper=True)
    assert result.returncode == 1
    assert not list(run.glob("withheld-*"))
    assert all((pack / rel).read_bytes() == data for rel, data in current.items())


def test_answer_directory_is_not_a_missing_file_deferral(note_fixture):
    f = note_fixture
    (f.out / manifest.answer_pdf_name(f.m)).mkdir()
    assert f.check(False)
    assert f.check(True)
