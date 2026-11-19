import builtins
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from lstm_comparison.cli import main


CONFIG = Path(__file__).resolve().parents[1] / "configs" / "research.json"


class CliTests(unittest.TestCase):
    def invoke(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = main(arguments)
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_help_and_validation_need_no_research_imports_or_network(self):
        original_import = builtins.__import__

        def checked_import(name, *args, **kwargs):
            if name.split(".")[0] in {"tensorflow", "keras", "numpy", "pandas", "yfinance", "sklearn", "matplotlib"}:
                raise AssertionError(f"Unexpected research import: {name}")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=checked_import), patch.object(
            socket, "socket", side_effect=AssertionError("Unexpected network access")
        ):
            for command in ([], ["validate-config"], ["download"], ["load-snapshot"], ["run"], ["report"]):
                with self.subTest(command=command):
                    code, output, _ = self.invoke(command + ["--help"])
                    self.assertEqual(code, 0)
                    self.assertIn("usage:", output)
            code, output, error = self.invoke(["validate-config", "--config", str(CONFIG)])
        self.assertEqual(code, 0)
        self.assertIn("設定檢查通過", output)
        self.assertIn(str(CONFIG.parent.parent / "res" / "research").replace("\\", "\\\\"), output)
        self.assertEqual(error, "")

    def test_invalid_config_returns_error_without_traceback(self):
        code, output, error = self.invoke(["validate-config", "--config", str(CONFIG.parent / "missing.json")])
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("設定錯誤", error)
        self.assertNotIn("Traceback", error)

    def test_unimplemented_commands_are_not_successful(self):
        for command, option in (("run", "--config"), ("report", "--run-dir")):
            with self.subTest(command=command):
                code, output, error = self.invoke([command, option, "does-not-exist"])
                self.assertEqual(code, 1)
                self.assertEqual(output, "")
                self.assertIn("尚未實作", error)

    def test_missing_required_arguments_fail(self):
        for command in ([], ["validate-config"], ["download"], ["load-snapshot"], ["run"], ["report"]):
            with self.subTest(command=command):
                code, _, error = self.invoke(command)
                self.assertEqual(code, 2)
                self.assertIn("required", error)

    def test_download_and_offline_load_validate_configuration(self):
        for command in ("download", "load-snapshot"):
            with self.subTest(command=command):
                code, _, error = self.invoke([command, "--config", str(CONFIG.parent / "missing.json")])
                self.assertEqual(code, 2)
                self.assertIn("設定錯誤", error)

    def test_snapshot_errors_do_not_report_success(self):
        from lstm_comparison.data import SnapshotError

        for command, operation in (("download", "download_snapshot"), ("load-snapshot", "load_snapshot")):
            with self.subTest(command=command), patch(
                f"lstm_comparison.data.{operation}", side_effect=SnapshotError("invalid snapshot")
            ):
                code, output, error = self.invoke([command, "--config", str(CONFIG)])
                self.assertEqual(code, 1)
                self.assertEqual(output, "")
                self.assertIn("快照錯誤", error)


if __name__ == "__main__":
    unittest.main()
