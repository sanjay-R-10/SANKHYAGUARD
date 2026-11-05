import csv
import tempfile
from pathlib import Path

from evaluate import evaluate


FIELDS = (
    "id",
    "language",
    "kind",
    "truth",
    "expected_len",
    "view_v2_5",
    "view_v3_0",
)


def write_fixture(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_row_accounting():
    rows = [
        {
            "id": "complete",
            "language": "en",
            "kind": "amount",
            "truth": "13000",
            "expected_len": "",
            "view_v2_5": "13,000",
            "view_v3_0": "13000 rupees",
        },
        {
            "id": "empty_transcript",
            "language": "hi",
            "kind": "amount",
            "truth": "13000",
            "expected_len": "",
            "view_v2_5": "",
            "view_v3_0": "",
        },
        {
            "id": "missing_truth",
            "language": "en",
            "kind": "amount",
            "truth": "",
            "expected_len": "",
            "view_v2_5": "13,000",
            "view_v3_0": "13000",
        },
    ]

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "fixture.csv"
        write_fixture(path, rows)
        report = evaluate(path)
        missing_views_path = Path(directory) / "missing_views.csv"
        with missing_views_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=("id", "language", "kind", "truth", "expected_len"),
            )
            writer.writeheader()
            writer.writerow(
                {
                    "id": "missing_views",
                    "language": "kn",
                    "kind": "amount",
                    "truth": "13000",
                    "expected_len": "",
                }
            )
        missing_views_report = evaluate(missing_views_path)

    assert report["input_rows"] == 3, report
    assert report["evaluated_rows"] == 1, report
    assert report["skipped_rows"] == 2, report
    assert report["skip_reasons"] == {
        "empty_transcript": 1,
        "missing_expected_value": 1,
    }, report
    assert report["stats"]["ALL"]["n"] == 1, report
    assert missing_views_report["skip_reasons"] == {"missing_views": 1}, missing_views_report


if __name__ == "__main__":
    test_row_accounting()
    print("Evaluator tests passed")
