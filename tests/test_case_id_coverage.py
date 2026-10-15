import ast
import re
from pathlib import Path
from unittest import TestCase


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTED_ID = re.compile(r"(?:^\| (M-\d{2}) \||^### (S-\d{2})\.)", re.MULTILINE)
IMPLEMENTED_ID = re.compile(r"def test_([ms])_(\d{2})")


class CaseIdCoverageTests(TestCase):
    def test_all_documented_case_ids_have_tests(self) -> None:
        """Проверяет, что каждому ID из TEST_CASES.md соответствует unittest-тест."""
        documented_text = (ROOT / "TEST_CASES.md").read_text(encoding="utf-8")
        documented = {
            case_id
            for match in DOCUMENTED_ID.finditer(documented_text)
            for case_id in match.groups()
            if case_id is not None
        }

        implemented = set()
        for test_file in (ROOT / "tests").glob("test_*.py"):
            if test_file.name == Path(__file__).name:
                continue
            for prefix, number in IMPLEMENTED_ID.findall(
                test_file.read_text(encoding="utf-8")
            ):
                implemented.add(f"{prefix.upper()}-{number}")

        self.assertEqual(
            implemented,
            documented,
            msg=(
                f"нет тестов для: {sorted(documented - implemented)}; "
                f"лишние ID: {sorted(implemented - documented)}"
            ),
        )

    def test_all_test_methods_have_russian_docstrings(self) -> None:
        """Проверяет наличие русскоязычного описания у каждого тестового метода."""
        missing = []
        for test_file in (ROOT / "tests").glob("test_*.py"):
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith("test_"):
                    continue
                docstring = ast.get_docstring(node) or ""
                if re.search(r"[А-Яа-яЁё]", docstring) is None:
                    missing.append(f"{test_file.name}:{node.name}")

        self.assertEqual(missing, [], msg=f"нет русского описания: {missing}")
