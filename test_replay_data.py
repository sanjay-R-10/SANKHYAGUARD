import csv
import tempfile
import unittest
from pathlib import Path

from replay_data import audio_path_for, load_replay_rows


FIELDS = [
    "id",
    "language",
    "condition",
    "kind",
    "truth",
    "expected_len",
    "v2_5_status",
    "v2_5_transcript",
    "v2_5_literal",
    "v3_0_status",
    "v3_0_transcript",
    "view_v2_5",
    "view_v3_0",
    "paired_views_status",
]


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def make_row(clip_id="en_01", status="READY"):
    return {
        "id": clip_id,
        "language": "en",
        "condition": "clean",
        "kind": "digits",
        "truth": "123",
        "expected_len": "3",
        "v2_5_status": "SUCCESS",
        "v2_5_transcript": "123",
        "v2_5_literal": "one two three",
        "v3_0_status": "SUCCESS",
        "v3_0_transcript": "123",
        "view_v2_5": "123",
        "view_v3_0": "123",
        "paired_views_status": status,
    }


class ReplayDataTests(unittest.TestCase):
    def test_loads_complete_pilot_rows_and_validates_demo_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "pilot.csv"
            demo_ids = root / "demo_ids.txt"
            dataset = root / "dataset.csv"
            write_rows(results, [make_row("en_01"), make_row("kn_02")])
            demo_ids.write_text("en_01\n", encoding="utf-8")
            dataset.write_text("id\n en_01\nkn_02\n".replace(" ", ""), encoding="utf-8")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual([row["id"] for row in rows], ["en_01"])
            self.assertEqual(warnings, [])

    def test_none_demo_id_path_returns_all_complete_pilot_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "pilot.csv"
            dataset = root / "dataset.csv"
            write_rows(results, [make_row("en_01"), make_row("kn_02")])
            dataset.write_text("id\nen_01\nkn_02\n", encoding="utf-8")
            rows, warnings = load_replay_rows(
                results_path=results, demo_ids_path=None, dataset_path=dataset
            )
            self.assertEqual([row["id"] for row in rows], ["en_01", "kn_02"])
            self.assertEqual(warnings, [])

    def test_excludes_incomplete_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "pilot.csv"
            demo_ids = root / "demo_ids.txt"
            dataset = root / "dataset.csv"
            write_rows(results, [make_row("en_01"), make_row("hi_11", "INCOMPLETE")])
            demo_ids.write_text("en_01\nhi_11\n", encoding="utf-8")
            dataset.write_text("id\nen_01\nhi_11\n", encoding="utf-8")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual([row["id"] for row in rows], ["en_01"])
            self.assertTrue(any("Excluded 1 incomplete" in warning for warning in warnings))
            self.assertTrue(any("hi_11" in warning for warning in warnings))

    def test_missing_results_file_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows, warnings = load_replay_rows(
                root / "missing.csv", root / "ids.txt", root / "dataset.csv"
            )
            self.assertEqual(rows, [])
            self.assertTrue(any("not found" in warning for warning in warnings))

    def test_empty_and_invalid_demo_ids_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "pilot.csv"
            demo_ids = root / "demo_ids.txt"
            dataset = root / "dataset.csv"
            write_rows(results, [make_row()])
            dataset.write_text("id\nen_01\n", encoding="utf-8")

            demo_ids.write_text("", encoding="utf-8")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual([row["id"] for row in rows], ["en_01"])
            self.assertTrue(any("is empty" in warning for warning in warnings))

            demo_ids.write_text("bad-id\n", encoding="utf-8")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual(rows, [])
            self.assertTrue(any("invalid demo ID" in warning for warning in warnings))

    def test_missing_fields_and_invalid_dataset_ids_are_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "pilot.csv"
            demo_ids = root / "demo_ids.txt"
            dataset = root / "dataset.csv"
            write_rows(results, [make_row("en_01"), make_row("../evil")])
            demo_ids.write_text("en_01\n../evil\n", encoding="utf-8")
            dataset.write_text("id\nen_01\n../evil\n", encoding="utf-8")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual([row["id"] for row in rows], ["en_01"])
            self.assertTrue(any("invalid demo ID" in warning for warning in warnings))

            with results.open("w", newline="", encoding="utf-8") as stream:
                stream.write("id,truth\n")
            rows, warnings = load_replay_rows(results, demo_ids, dataset)
            self.assertEqual(rows, [])
            self.assertTrue(any("missing required columns" in warning for warning in warnings))

    def test_missing_audio_is_a_reportable_path(self):
        row = make_row()
        path = audio_path_for(row, Path("temporary_project"))
        self.assertEqual(path, Path("temporary_project") / "audio" / "en_01.wav")
        self.assertIsNone(audio_path_for({**row, "condition": "unknown"}))
        self.assertIsNone(audio_path_for({**row, "id": ".."}))


if __name__ == "__main__":
    unittest.main()
