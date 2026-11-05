import json
import tempfile
from pathlib import Path

from build_results import make_result, write_results


ITEM = {
    "id": "en_01",
    "language": "en",
    "kind": "digits",
    "truth": "123",
    "expected_len": "3",
}


def test_missing_response_is_incomplete():
    with tempfile.TemporaryDirectory() as directory:
        raw_dir = Path(directory) / "raw"
        raw_dir.mkdir()
        (raw_dir / "en_01__prisma-v2.5.json").write_text(
            json.dumps(
                {
                    "success": True,
                    "transcript": "one two three",
                    "model": "prisma-v2.5",
                }
            ),
            encoding="utf-8",
        )
        statuses = {
            ("en_01", "prisma-v2.5"): {"status": "SUCCESS"},
            ("en_01", "prisma-v3.0"): {"status": "SUCCESS"},
        }
        result = make_result(ITEM, statuses, raw_dir)

    assert result["v2_5_status"] == "SUCCESS", result
    assert result["v3_0_status"] == "MISSING_RESPONSE", result
    assert result["paired_views_status"] == "INCOMPLETE", result
    assert result["view_v2_5"] == "", result
    assert result["view_v3_0"] == "", result


def test_empty_transcript_is_not_complete():
    with tempfile.TemporaryDirectory() as directory:
        raw_dir = Path(directory) / "raw"
        raw_dir.mkdir()
        for model in ("prisma-v2.5", "prisma-v3.0"):
            (raw_dir / f"en_01__{model}.json").write_text(
                json.dumps(
                    {
                        "success": True,
                        "transcript": "",
                        "model": model,
                    }
                ),
                encoding="utf-8",
            )
        result = make_result(ITEM, {}, raw_dir)

    assert result["v2_5_status"] == "EMPTY_TRANSCRIPT", result
    assert result["v3_0_status"] == "EMPTY_TRANSCRIPT", result
    assert result["paired_views_status"] == "INCOMPLETE", result


def test_csv_writer_refuses_overwrite():
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "results.csv"
        raw_dir = Path(directory) / "raw"
        raw_dir.mkdir()
        rows = write_results([ITEM], {}, output, raw_dir)
        before = output.read_bytes()
        assert len(rows) == 1
        try:
            write_results([ITEM], {}, output, raw_dir)
        except SystemExit as error:
            assert "Refusing to overwrite" in str(error), error
        else:
            raise AssertionError("Existing output was not protected")
        assert output.read_bytes() == before


if __name__ == "__main__":
    test_missing_response_is_incomplete()
    test_empty_transcript_is_not_complete()
    test_csv_writer_refuses_overwrite()
    print("Result-builder tests passed")
