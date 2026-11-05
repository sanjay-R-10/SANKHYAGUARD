import tempfile
import unittest
from pathlib import Path

from make_report import (
    REQUIRED_FULL_COLUMNS,
    adapt_full_rows,
    evaluate_condition,
    load_inputs,
    render_report,
)


class MakeReportTests(unittest.TestCase):
    def test_pilot_metrics_use_existing_evaluator_definitions(self):
        rows = [
            {
                "id": "wrong_and_confirmed",
                "language": "kn",
                "kind": "digits",
                "truth": "123456",
                "expected_len": "6",
                "view_v2_5": "123",
                "view_v3_0": "123",
            },
            {
                "id": "silent_error",
                "language": "kn",
                "kind": "amount",
                "truth": "30000",
                "expected_len": "",
                "view_v2_5": "13000",
                "view_v3_0": "13000",
            },
            {
                "id": "accepted_correct",
                "language": "en",
                "kind": "amount",
                "truth": "13000",
                "expected_len": "",
                "view_v2_5": "13000",
                "view_v3_0": "13000",
            },
        ]
        result = evaluate_condition(rows, "clean pilot")
        stats = result["evaluation"]["stats"]["ALL"]
        self.assertEqual(result["evaluation"]["input_rows"], 3)
        self.assertEqual(result["evaluation"]["evaluated_rows"], 3)
        self.assertEqual(stats["A_errors"], 2)
        self.assertEqual(stats["G_silent_errors"], 1)
        self.assertEqual(stats["G_confirms"], 1)
        self.assertEqual(stats["G_caught"], 1)
        self.assertEqual(stats["G_unneeded"], 0)

    def test_full_schema_adapter_preserves_all_three_views(self):
        source = {
            "id": "en_01",
            "language": "en",
            "kind": "digits",
            "truth": "123",
            "expected_len": "3",
            "view_v25_itn": "one two three",
            "view_v25_literal": "123",
            "view_v30": "123",
        }
        adapted = adapt_full_rows([source], "clean")[0]
        result = evaluate_condition([adapted], "clean")
        detail = result["details"][0]
        self.assertEqual(detail["first_value"], "123")
        self.assertEqual(detail["decision"], "ACCEPT")
        self.assertEqual(result["evaluation"]["evaluated_rows"], 1)

    def test_full_schema_validation_requires_claude_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory) / "results_clean_all.csv"
            phone = Path(directory) / "results_phone_all.csv"
            pilot = Path(directory) / "pilot.csv"
            columns = list(REQUIRED_FULL_COLUMNS)
            for path in (clean, phone):
                path.write_text(",".join(columns) + "\n", encoding="utf-8")
            phone.write_text("truth,kind\n", encoding="utf-8")
            pilot.write_text(
                "id,language,kind,truth,view_v2_5,view_v3_0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "view_v25_itn"):
                load_inputs(clean, phone, pilot)

    def test_missing_full_inputs_select_pilot_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pilot = root / "pilot.csv"
            pilot.write_text(
                "id,language,condition,kind,truth,expected_len,view_v2_5,view_v3_0\n"
                "en_01,en,clean,digits,123,3,123,123\n",
                encoding="utf-8",
            )
            mode, results, missing = load_inputs(
                root / "results_clean_all.csv",
                root / "results_phone_all.csv",
                pilot,
            )
            self.assertEqual(mode, "pilot")
            self.assertEqual(missing, ["results_clean_all.csv", "results_phone_all.csv"])
            self.assertEqual(results[0]["evaluation"]["evaluated_rows"], 1)

    def test_report_lists_skipped_incomplete_rows(self):
        rows = [
            {
                "id": "incomplete",
                "language": "hi",
                "kind": "amount",
                "truth": "13000",
                "expected_len": "",
                "v2_5_status": "HTTP_ERROR",
                "v3_0_status": "SUCCESS",
                "view_v2_5": "",
                "view_v3_0": "",
            }
        ]
        result = evaluate_condition(rows, "clean pilot")
        report = render_report("pilot", [result], ["results_clean_all.csv"])
        self.assertIn("`incomplete` | unavailable_model_response", report)

    def test_existing_outputs_are_not_overwritten_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = [root / "report.md", root / "chart.png", root / "demo_ids.txt"]
            for path in outputs:
                path.write_text("keep me", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                from make_report import generate

                generate(
                    outputs[0],
                    outputs[1],
                    outputs[2],
                    root / "missing_clean.csv",
                    root / "missing_phone.csv",
                    root / "missing_pilot.csv",
                )
            self.assertEqual(
                [path.read_text(encoding="utf-8") for path in outputs],
                ["keep me"] * 3,
            )


if __name__ == "__main__":
    unittest.main()
