import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review_selection import load_selection, reviewed_selection_path, apply_selection


class SelectionTest(unittest.TestCase):
    def test_order_and_metadata_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'selection.json'
            value = dict(schema_version=2, policy='exam-first-v2', workload=dict(estimated_minutes=20),
                problems=[dict(id=pid, priority='core', learning_goals=['이득'],
                               estimated_minutes=10, subpart_count=1) for pid in ['A', 'B']])
            path.write_text(json.dumps(value), encoding='utf-8')
            loaded = load_selection(path, ['A', 'B'])
            data = apply_selection(dict(meta={}, problems=[dict(id='A'), dict(id='B')]), loaded)
            self.assertIn('핵심', data['problems'][0]['review_workload_label'])
            with self.assertRaises(ValueError):
                load_selection(path, ['B', 'A'])
            value['problems'][0]['estimated_minutes'] = True
            path.write_text(json.dumps(value), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_selection(path, ['A', 'B'])

    def test_answer_requires_same_approved_selection_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / '.assets/selection.json'
            path.parent.mkdir()
            path.write_text('{}', encoding='utf-8')
            overlay = dict(source_inputs={'.assets/selection.json': hashlib.sha256(path.read_bytes()).hexdigest()})
            self.assertEqual(reviewed_selection_path(overlay, repo), path)
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaises(ValueError):
                reviewed_selection_path(overlay, repo)
            with self.assertRaises(ValueError):
                reviewed_selection_path(dict(source_inputs={}), repo, path)

    def test_unknown_policy_and_duplicate_ids_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'selection.json'
            path.write_text(json.dumps(dict(schema_version=2, policy='future', problems=[])), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_selection(path, [])
