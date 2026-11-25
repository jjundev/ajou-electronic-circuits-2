"""macOS와 Windows에서 같은 바이트·같은 경로 표기가 나오는지 소스에서 확인한다.

Windows의 텍스트 쓰기는 줄바꿈을 CRLF로 바꾼다. 발행 승인은 바이트 해시로 하므로
운영 코드가 텍스트를 쓸 때는 newline을 직접 정해야 한다.
"""

import ast
import os
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = (".agents/skills", ".claude/skills", "scripts", "workbook", "from_the_past/md/_tools",
        "교과서/마이크로전자회로/_tools", "tests")
OPENERS = {"open", "fdopen", "NamedTemporaryFile", "TemporaryFile"}


def sources():
    """검사할 (경로, 테스트 여부). 스킬 폴더의 심볼릭 링크는 따라가지 않는다."""
    for base in CODE:
        for folder, dirs, files in os.walk(ROOT / base):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "node_modules", "build")]
            for name in sorted(files):
                if name.endswith(".py"):
                    path = Path(folder) / name
                    yield path, "tests" in path.relative_to(ROOT).parts


def _mode(call, name):
    """리터럴 mode. 모르면 빈 문자열."""
    value = next((k.value for k in call.keywords if k.arg == "mode"), None)
    if value is None:
        path_open = name == "open" and isinstance(call.func, ast.Attribute)
        index = 0 if path_open or name in ("NamedTemporaryFile", "TemporaryFile") else 1
        value = call.args[index] if len(call.args) > index else None
    return value.value if isinstance(value, ast.Constant) and isinstance(value.value, str) else ""


def problems(source, *, is_test):
    """[(줄, 설명)]"""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(a.name == "fitz" for a in node.names):
            found.append((node.lineno, "`import fitz`는 stdout에 경고를 찍는다 → `import pymupdf as fitz`"))
        if isinstance(node, ast.ImportFrom) and node.module == "fitz":
            found.append((node.lineno, "`from fitz`는 stdout에 경고를 찍는다 → `from pymupdf`"))
        if not isinstance(node, ast.Call):
            continue
        if node.args and isinstance(node.args[0], ast.List) and node.args[0].elts:
            first = node.args[0].elts[0]
            if isinstance(first, ast.Constant) and first.value == "python3":
                found.append((node.lineno, "Windows에는 python3가 없다 → sys.executable"))
        name = getattr(node.func, "attr", getattr(node.func, "id", None))
        if is_test or any(k.arg == "newline" for k in node.keywords):
            continue
        writes = name == "write_text" or name in OPENERS and re.fullmatch(r"[wax][+t]*", _mode(node, name))
        if writes:
            found.append((node.lineno, "텍스트 쓰기에 newline이 없다 → newline='\\n'"))
    return found


class HostPortabilityTests(unittest.TestCase):
    def test_sources(self):
        seen, bad = 0, []
        for path, is_test in sources():
            seen += 1
            bad += [f"{path.relative_to(ROOT).as_posix()}:{line}: {text}"
                    for line, text in problems(path.read_bytes(), is_test=is_test)]
        self.assertGreater(seen, 100)
        self.assertEqual(bad, [])

    def test_detects_each_problem(self):
        for code in ("import fitz", "from fitz import open", "run(['python3', 'x.py'])", "p.write_text('x')",
                     "open('x', 'w')", "open('x', mode='a')", "p.open('x', encoding='utf-8')", "os.fdopen(fd, 'w')",
                     "tempfile.NamedTemporaryFile(mode='w')", "tempfile.NamedTemporaryFile('w+t')"):
            with self.subTest(code=code):
                self.assertEqual(len(problems(code, is_test=False)), 1)

    def test_accepts_portable_code(self):
        for code in ("import pymupdf as fitz", "run([sys.executable, 'x.py'])", "p.write_text('x', newline='\\n')",
                     "open('x')", "open('x', 'wb')", "p.open('xb')", "p.open()", "p.write_bytes(b'x')",
                     "tempfile.NamedTemporaryFile()", "tempfile.NamedTemporaryFile('w', newline='')"):
            with self.subTest(code=code):
                self.assertEqual(problems(code, is_test=False), [])
        self.assertEqual(problems("p.write_text('x')", is_test=True), [])

    def test_published_quiz_bytes_survive_checkout(self):
        paths = ["복습노트/9999/확인문제_9999_X.html", "복습노트/9999/.pack/자료_확인문제_9999_X/browser.json",
                 "복습노트/9999/.pack/자료_확인문제_9999_X/shots/a/b.json"]
        result = subprocess.run(["git", "check-attr", "-z", "text", "--", *paths], cwd=ROOT, capture_output=True)
        if result.returncode:
            self.skipTest("git 저장소가 아니다")
        fields = result.stdout.decode("utf-8").split("\0")
        self.assertEqual(fields[2::3], ["unset"] * len(paths))


if __name__ == "__main__":
    unittest.main()
