import json
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble import (BuildError, Selection, all_selections, build_data, chapter_selection,  # noqa: E402
                      exam_selection, ids_selection, resolve_target)
from paths import TEMPLATES  # noqa: E402

SAMPLE_IDS = ["P9.05", "X9.13", "P11.39", "X11.01", "E9.01", "E11.18",
              "X9.16", "P9.07", "E11.01", "P10.32", "P9.09", "E9.07"]
MECHANICAL = ["id", "kind", "number", "title", "section", "book_page", "difficulty", "sol",
              "depends_on", "figures"]
CONDITIONS_UNEDITED = {"E9.01", "E11.18", "P9.07", "P10.32", "P9.09", "E9.07"}   # 샘플이 손대지 않은 조건
ASK_EDITED = {"P9.05", "P10.32"}                                                 # 샘플이 손댄 구할 것


def sample(name):
    data = json.loads((TEMPLATES / name).read_text(encoding="utf-8"))
    return data["meta"], {p["id"]: p for p in data["problems"]}


class TestGolden(unittest.TestCase):
    """템플릿 샘플(12문제)을 md에서 다시 만들어 기계적인 필드를 비교한다."""

    @classmethod
    def setUpClass(cls):
        sel = ids_selection(SAMPLE_IDS, "샘플")
        cls.data = build_data(sel, "problems")
        cls.built = {p["id"]: p for p in cls.data["problems"]}
        cls.meta, cls.sample = sample("sample-problem.json")
        cls.answers = build_data(sel, "answers")

    def test_meta_matches_sample(self):
        self.assertEqual(self.data["meta"], self.meta)
        self.assertEqual(self.answers["meta"], sample("sample-answer.json")[0])

    def test_order_follows_ids(self):
        self.assertEqual([p["id"] for p in self.data["problems"]], SAMPLE_IDS)

    def test_mechanical_fields_match_sample(self):
        for pid in SAMPLE_IDS:
            for key in MECHANICAL:
                with self.subTest(pid=pid, key=key):
                    self.assertEqual(self.built[pid][key], self.sample[pid][key])

    def test_conditions_match_where_sample_is_unedited(self):
        for pid in CONDITIONS_UNEDITED:
            with self.subTest(pid=pid):
                self.assertEqual(self.built[pid]["html"]["conditions"], self.sample[pid]["html"]["conditions"])

    def test_ask_matches_where_sample_is_unedited(self):
        for pid in set(SAMPLE_IDS) - ASK_EDITED:
            with self.subTest(pid=pid):
                self.assertEqual(self.built[pid]["html"]["ask"], self.sample[pid]["html"]["ask"])


class TestSelections(unittest.TestCase):
    def test_chapter_book_order(self):
        sel = chapter_selection(9)
        ids = [p.stem for p in sel.paths]
        self.assertEqual((sel.name, sel.title, sel.chapter), ("ch09", "9장 캐스코드 단과 전류 거울", 9))
        self.assertEqual(ids[:4], ["E9.01", "X9.01", "E9.02", "X9.02"])
        self.assertEqual(len(ids), 110)
        first_p = next(i for i, x in enumerate(ids) if x.startswith("P"))
        self.assertTrue(all(x.startswith("P") for x in ids[first_p:]))

    def test_exam_selection(self):
        sel = exam_selection("2021-1_기말")
        self.assertEqual([p.stem for p in sel.paths], [f"Q{n}" for n in range(1, 8)])
        self.assertEqual((sel.name, sel.title, sel.chapter), ("2021-1_기말", "2021-1 기말고사", 0))

    def test_nfd_exam_name(self):
        nfd = unicodedata.normalize("NFD", "2023-1_기말")
        self.assertEqual(exam_selection(nfd).name, "2023-1_기말")
        self.assertEqual(resolve_target(nfd).title, "2023-1 기말고사")

    def test_resolve_target_chapter(self):
        self.assertEqual(resolve_target("ch10").chapter, 10)

    def test_unknown_target(self):
        for target in ("ch99", "2099-1_기말", "foo"):
            with self.subTest(target=target), self.assertRaises(KeyError):
                resolve_target(target)

    def test_ids_selection_errors(self):
        with self.assertRaises(BuildError) as cm:
            ids_selection(["Z1", "P9.99"], "t")
        self.assertEqual(len(cm.exception.errors), 2)

    def test_all_selections(self):
        self.assertEqual([s.name for s in all_selections()],
                         ["ch09", "ch10", "ch11", "2021-1_기말", "2021-1_중간", "2023-1_기말", "2023-1_중간"])


class TestEntries(unittest.TestCase):
    def test_in_file(self):
        alone = build_data(ids_selection(["P9.05"], "t"), "problems")["problems"][0]
        self.assertEqual(alone["depends_on"], [{"id": "E9.01", "in_file": False}])
        both = build_data(ids_selection(["E9.01", "P9.05"], "t"), "problems")["problems"][1]
        self.assertEqual(both["depends_on"], [{"id": "E9.01", "in_file": True}])

    def test_answers_mode(self):
        data = build_data(ids_selection(["E9.01", "P9.05"], "t"), "answers")
        self.assertEqual(data["meta"]["title"], "t 답안")
        e901, p905 = data["problems"]
        self.assertEqual(e901["solution"], {
            "steps": [], "answer": r"$R_{out} \approx 328.9\ \text{k}\Omega$ ($V_T \approx 26\ \text{mV}$, 식 9.10)"})
        self.assertNotIn("solution", p905)
        self.assertTrue(all("original" not in p["html"] for p in data["problems"]))

    def test_example_answer_has_no_image_markdown(self):
        e = build_data(ids_selection(["E11.03"], "t"), "answers")["problems"][0]
        self.assertTrue(e["solution"]["answer"])
        self.assertNotIn("![", e["solution"]["answer"])

    def test_exam_entry(self):
        e = build_data(ids_selection(["2023-1_기말-Q1"], "t"), "problems")["problems"][0]
        self.assertEqual((e["kind"], e["number"], e["section"], e["book_page"], e["difficulty"], e["original_lang"]),
                         ("기출", "1", "2023-1 기말고사 · 20점", None, None, "ko"))
        self.assertEqual(len(e["figures"]), 1)

    def test_build_errors_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = []
            for name in ("a.md", "b.md"):
                path = Path(tmp) / name
                path.write_text('---\nid: E9.01\nkind: 예제\nnumber: "9.1"\n---\n본문만\n', encoding="utf-8")
                bad.append(path)
            with self.assertRaises(BuildError) as cm:
                build_data(Selection("bad", "bad", 0, bad), "problems")
        self.assertEqual(len(cm.exception.errors), 2)
        self.assertIn("a.md", cm.exception.errors[0])


if __name__ == "__main__":
    unittest.main()
