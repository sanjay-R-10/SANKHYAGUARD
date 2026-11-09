import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


POST_HEADERS = {"X-SankhyaGuard-Request": "1"}


class ServerTests(unittest.TestCase):
    def setUp(self):
        server.app.config.update(TESTING=True)
        server.STATE["calls"] = 0
        self.client = server.app.test_client()

    def tearDown(self):
        server.STATE["calls"] = 0

    def test_check_requires_same_origin_header_and_consent(self):
        missing_header = self.client.post("/api/check")
        self.assertEqual(missing_header.status_code, 403)
        missing_consent = self.client.post("/api/check", headers=POST_HEADERS)
        self.assertEqual(missing_consent.status_code, 403)
        self.assertEqual(server.STATE["calls"], 0)

    def test_correction_is_local_and_validates_expected_length(self):
        valid = self.client.post(
            "/api/correction",
            headers=POST_HEADERS,
            data={"kind": "digits", "expected_len": "6", "value": "123456"},
        )
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(valid.json["value"], "123456")

        invalid = self.client.post(
            "/api/correction",
            headers=POST_HEADERS,
            data={"kind": "digits", "expected_len": "6", "value": "12345"},
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(server.STATE["calls"], 0)

    def test_demo_routes_only_expose_valid_manifest_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "audio").mkdir()
            (root / "audio" / "en_01.wav").write_bytes(b"demo wav")
            with (root / "dataset_script.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(
                    stream, fieldnames=("id", "language", "kind", "expected_len")
                )
                writer.writeheader()
                writer.writerows(
                    (
                        {"id": "en_01", "language": "en", "kind": "digits", "expected_len": "10"},
                        {"id": "../x", "language": "en", "kind": "digits", "expected_len": "10"},
                        {"id": "kn_02", "language": "kn", "kind": "amount", "expected_len": ""},
                    )
                )

            with (
                patch.object(server, "PROJECT_DIR", root),
                patch.object(server, "DATASET", root / "dataset_script.csv"),
            ):
                cases = self.client.get("/api/demo/cases")
                self.assertEqual(cases.status_code, 200)
                self.assertEqual([row["id"] for row in cases.json], ["en_01"])

                clip = self.client.get("/api/demo/clip/en_01")
                self.assertEqual(clip.status_code, 200)
                self.assertEqual(clip.data, b"demo wav")
                clip.close()

                invalid_clip = self.client.get("/api/demo/clip/../x")
                self.assertIn(invalid_clip.status_code, (400, 404))

    def test_live_check_calls_only_mocked_prisma_and_counts_attempts(self):
        responses = [
            {"transcript": "1234567890", "output": {"literal": "one two three four five six seven eight nine zero"}},
            {"transcript": "1234567890"},
        ]
        with (
            patch.object(server, "read_upload", return_value=(b"normalized wav", 1.2)),
            patch.object(server.prisma_client, "transcribe", side_effect=responses) as transcribe,
        ):
            result = self.client.post(
                "/api/check",
                headers=POST_HEADERS,
                data={
                    "audio": (io.BytesIO(b"browser audio"), "recording.webm"),
                    "lang": "en",
                    "kind": "digits",
                    "expected_len": "10",
                    "live_consent": "true",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(result.json["decision"], "ACCEPT")
        self.assertEqual(result.json["calls"], 2)
        self.assertEqual(transcribe.call_count, 2)
        self.assertEqual(server.STATE["calls"], 2)

    def test_request_limit_prevents_transcription(self):
        with (
            patch.object(server, "MAX_CALLS", 1),
            patch.object(server, "read_upload", return_value=(b"normalized wav", 1.2)),
            patch.object(server.prisma_client, "transcribe") as transcribe,
        ):
            result = self.client.post(
                "/api/check",
                headers=POST_HEADERS,
                data={
                    "audio": (io.BytesIO(b"browser audio"), "recording.webm"),
                    "lang": "en",
                    "kind": "digits",
                    "expected_len": "10",
                    "live_consent": "true",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(result.status_code, 429)
        transcribe.assert_not_called()
        self.assertEqual(server.STATE["calls"], 0)

    def test_replay_uses_saved_views_without_prisma(self):
        row = {
            "id": "en_01",
            "condition": "clean",
            "kind": "digits",
            "language": "en",
            "expected_len": "10",
            "view_v2_5": "1234567890",
            "view_v3_0": "1234567890",
            "truth": "1234567890",
        }
        with patch.object(server, "replay_rows", return_value=[row]):
            response = self.client.get("/api/replay/clean/en_01")

        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["decision"], "ACCEPT")
        self.assertEqual(response.json["truth"], "1234567890")
        self.assertEqual(server.STATE["calls"], 0)

    def test_no_timbre_readback_api_is_exposed(self):
        self.assertEqual(self.client.post("/api/readback").status_code, 404)
        self.assertEqual(server.STATE["calls"], 0)


if __name__ == "__main__":
    unittest.main()
