"""SKILL.md stays parseable, its links resolve and its CLI commands match the parser."""
import re
import unittest

import yaml

from _util import SKILL, REPO
from epe_cli import main  # noqa: F401  (the documented CLI must import)
import epe_cli

SKILL_MD = SKILL / 'SKILL.md'
LINK_RE = re.compile(r'\]\(((?:references|scripts)/[^)#\s]+)\)')
COMMAND_RE = re.compile(r'epe_cli\.py"?\s+([a-z]+)\b')


def text():
    return SKILL_MD.read_text(encoding='utf-8')


def frontmatter():
    match = re.match(r'^---\n(.*?)\n---\n', text(), re.S)
    if not match:
        raise AssertionError('SKILL.md frontmatter 없음')
    return yaml.safe_load(match.group(1))


def parser_commands():
    seen = []
    original = epe_cli.argparse.ArgumentParser.parse_args

    def capture(self, args=None, namespace=None):
        for action in self._actions:
            if isinstance(action, epe_cli.argparse._SubParsersAction):
                seen.extend(action.choices)
        raise SystemExit(0)

    epe_cli.argparse.ArgumentParser.parse_args = capture
    try:
        epe_cli.main([])
    except SystemExit:
        pass
    finally:
        epe_cli.argparse.ArgumentParser.parse_args = original
    return set(seen)


class SkillFilesTest(unittest.TestCase):
    def test_frontmatter_parses_and_names_skill(self):
        meta = frontmatter()
        self.assertEqual(meta['name'], 'ec2-problem-explain')
        self.assertIsInstance(meta['description'], str)
        self.assertTrue(meta['description'].strip())
        # Quoted on purpose: an unquoted colon broke YAML parsing before (986a3b7).
        line = next(l for l in text().splitlines() if l.startswith('description:'))
        self.assertRegex(line, r'^description: ".*"$')

    def test_referenced_files_exist(self):
        links = set(LINK_RE.findall(text()))
        for required in ('references/authoring.md', 'references/verification.md', 'scripts/epe_cli.py'):
            self.assertIn(required, links)
        for link in links:
            self.assertTrue((SKILL / link).is_file(), link)

    def test_cli_commands_in_skill_match_parser(self):
        documented = set(COMMAND_RE.findall(text()))
        self.assertEqual(documented, {'extract', 'build', 'check', 'publish', 'rerender'})
        self.assertEqual(documented, parser_commands())

    def test_agents_symlink_points_to_skill(self):
        link = REPO / '.agents/skills/ec2-problem-explain'
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(), SKILL.resolve())


class LearningStyleBriefTest(unittest.TestCase):
    def test_child_briefs_include_profile_and_integrated_contract(self):
        skill = text()
        for required in ("<REPO>/docs/learning/solution-style.md", "learning_style", "data-answer-step", "learning_style_audit", "answer-overlay.json"):
            self.assertIn(required, skill)
        author = (SKILL / "references/authoring.md").read_text()
        for required in ("data-personalization", "data-solution-core", "data-core-label", "data-answer-step", "<REPO>/docs/learning/solution-style.md"):
            self.assertIn(required, author)
        review = (SKILL / "references/verification.md").read_text()
        for required in ("learning_style_audit", "not_applicable", "핵심", "단위", "근사", "그림"):
            self.assertIn(required, review)


if __name__ == '__main__':
    unittest.main()
