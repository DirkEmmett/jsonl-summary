import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonl_summary import summarize


SCRIPT = Path(__file__).with_name("jsonl_summary.py")


class SummaryTests(unittest.TestCase):
    def test_all_types_and_boolean_number_distinction(self):
        result = summarize(io.StringIO('null\ntrue\nfalse\n0\n-3.5\n2e7\n"x"\n[]\n{}'))
        self.assertEqual(result, {
            "records": 9,
            "types": {"null": 1, "boolean": 2, "number": 3,
                      "string": 1, "array": 1, "object": 1},
            "fields": {},
        })

    def test_empty_and_blank_input(self):
        for text in ("", "\n \t\n\r\n"):
            with self.subTest(text=text):
                result = summarize(io.StringIO(text))
                self.assertEqual(result["records"], 0)
                self.assertEqual(result["fields"], {})
                self.assertEqual(result["types"], dict.fromkeys(
                    ("null", "boolean", "number", "string", "array", "object"), 0
                ))

    def test_field_presence_is_per_top_level_object(self):
        text = (
            '{"a":null,"nested":{"hidden":1},"a":2}\n'
            '{"a":false,"z":[]}\n'
            '[{"array_only":1}]\n'
            '{"":0,"é":true}\n'
        )
        self.assertEqual(summarize(io.StringIO(text))["fields"], {
            "a": 2, "nested": 1, "z": 1, "": 1, "é": 1,
        })

    def test_blank_lines_preserve_physical_error_position(self):
        with self.assertRaisesRegex(ValueError, r"^line 4:"):
            summarize(io.StringIO('\n{}\n \t\n{"broken":}\n'))

    def test_constants_are_rejected_at_any_depth(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            for text in (constant, f'{{"a":[{constant}]}}'):
                with self.subTest(text=text):
                    with self.assertRaisesRegex(ValueError, "invalid JSON constant"):
                        summarize(io.StringIO(text))

    def test_large_numbers_need_no_numeric_conversion(self):
        text = "9" * 10000 + "\n1e" + "9" * 10000 + "\n"
        result = summarize(io.StringIO(text))
        self.assertEqual(result["records"], 2)
        self.assertEqual(result["types"]["number"], 2)

    def test_accepts_one_pass_line_iterator(self):
        lines = (line for line in ('null\n', '\n', '{"a":1}\n'))
        self.assertEqual(summarize(lines)["records"], 2)
        self.assertEqual(list(lines), [])

    def test_rejects_multiple_values_on_one_line(self):
        with self.assertRaisesRegex(ValueError, r"^line 1:"):
            summarize(io.StringIO("true false\n"))


class CliTests(unittest.TestCase):
    def run_cli(self, *args, data=b""):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )

    def assert_input_error(self, process):
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, b"")
        self.assertIn(b"jsonl-summary:", process.stderr)
        self.assertNotIn(b"Traceback", process.stderr)

    def test_default_and_explicit_stdin(self):
        for args in ((), ("-",)):
            with self.subTest(args=args):
                process = self.run_cli(*args, data=b'\ntrue\n{"x":null}\n')
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertEqual(process.stderr, b"")
                result = json.loads(process.stdout)
                self.assertEqual(result["records"], 2)
                self.assertEqual(result["fields"], {"x": 1})
                self.assertEqual(process.stdout, (json.dumps(result, sort_keys=True) + "\n").encode())

    def test_utf8_file_and_sorted_field_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text('{"z":1,"é":2,"a":3}\nnull', encoding="utf-8")
            process = self.run_cli(path)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, b"")
        result = json.loads(process.stdout)
        self.assertEqual(result["fields"], {"a": 1, "z": 1, "é": 1})
        self.assertEqual(list(result["fields"]), ["a", "z", "é"])
        self.assertEqual(result["records"], 2)

    def test_late_error_has_no_partial_stdout(self):
        process = self.run_cli(data=b'{}\n\nfalse\n{bad}\n')
        self.assert_input_error(process)
        self.assertIn(b"line 4:", process.stderr)

    def test_invalid_constants_have_clean_cli_errors(self):
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(constant=constant):
                process = self.run_cli(data=b"null\n\n" + constant)
                self.assert_input_error(process)
                self.assertIn(b"line 3:", process.stderr)
                self.assertIn(constant, process.stderr)

    def test_missing_file_error_names_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.jsonl"
            process = self.run_cli(path)
        self.assert_input_error(process)
        self.assertIn(str(path).encode(), process.stderr)

    def test_directory_is_not_an_input_file(self):
        with tempfile.TemporaryDirectory() as directory:
            process = self.run_cli(directory)
        self.assert_input_error(process)

    def test_invalid_utf8_file_and_stdin(self):
        data = b'{}\n"\xff"\n'
        self.assert_input_error(self.run_cli(data=data))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            path.write_bytes(data)
            process = self.run_cli(path)
        self.assert_input_error(process)
        self.assertIn(b"utf-8", process.stderr)

    def test_utf8_bom_is_not_json_whitespace(self):
        process = self.run_cli(data=b"\xef\xbb\xbf{}\n")
        self.assert_input_error(process)
        self.assertIn(b"line 1:", process.stderr)


if __name__ == "__main__":
    unittest.main()
