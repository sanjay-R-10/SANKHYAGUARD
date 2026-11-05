import csv
import io
import tempfile
import unittest
import wave
from pathlib import Path

from live_workflow import (
    AudioValidationError,
    append_session_event,
    audio_fingerprint,
    evaluate_transcripts,
    validate_correction,
    validate_wav,
)


def make_wav(seconds=0.2):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\0\0" * int(16000 * seconds))
    return buffer.getvalue()


class LiveWorkflowTests(unittest.TestCase):
    def test_validate_wav_accepts_valid_clip_and_rejects_bad_or_long_audio(self):
        clip = make_wav()
        self.assertAlmostEqual(validate_wav(clip), 0.2)
        with self.assertRaises(AudioValidationError):
            validate_wav(b"not wav")
        with self.assertRaisesRegex(AudioValidationError, "no more than"):
            validate_wav(make_wav(1), max_seconds=0.5)

    def test_guard_uses_both_real_transcripts(self):
        result = evaluate_transcripts(
            {"transcript": "one two three"},
            {"transcript": "123"},
            "digits",
            expected_len=3,
        )
        self.assertEqual(result["parsed_v25"], "123")
        self.assertEqual(result["parsed_v30"], "123")
        self.assertEqual(result["guard"]["decision"], "ACCEPT")
        with self.assertRaisesRegex(ValueError, "[Bb]oth real model"):
            evaluate_transcripts({"transcript": "123"}, None, "digits")
        with self.assertRaisesRegex(ValueError, "empty transcript"):
            evaluate_transcripts(
                {"transcript": ""},
                {"transcript": "123"},
                "digits",
            )

    def test_correction_is_parsed_and_digit_length_is_checked(self):
        self.assertEqual(validate_correction("digits", "1 2 3", 3), "123")
        self.assertEqual(validate_correction("amount", "25000"), 25000)
        with self.assertRaisesRegex(ValueError, "2 digits; 3 are expected"):
            validate_correction("digits", "12", 3)
        with self.assertRaises(ValueError):
            validate_correction("amount", "not a number")

    def test_fingerprint_includes_audio_and_processing_options(self):
        first = audio_fingerprint(b"clip-a", "en-IN", "digits", 10)
        self.assertEqual(first, audio_fingerprint(b"clip-a", "en-IN", "digits", 10))
        self.assertNotEqual(first, audio_fingerprint(b"clip-b", "en-IN", "digits", 10))
        self.assertNotEqual(first, audio_fingerprint(b"clip-a", "kn-IN", "digits", 10))
        self.assertNotEqual(first, audio_fingerprint(b"clip-a", "en-IN", "amount", None))

    def test_session_events_are_appended_without_audio(self):
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "results" / "live_sessions.csv"
            session = {
                "session_id": "session-1",
                "transcript_v25": "one two three",
                "api_status": "SUCCESS",
                "api_request_ids": ["req-1", "req-2"],
            }
            append_session_event(session, "TRANSCRIPTION_RESULT", log_path)
            append_session_event(session, "USER_CONFIRMED", log_path)
            with log_path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([row["event"] for row in rows], [
                "TRANSCRIPTION_RESULT",
                "USER_CONFIRMED",
            ])
            self.assertEqual(rows[1]["api_request_ids"], "req-1|req-2")
            self.assertNotIn("audio", rows[1])


if __name__ == "__main__":
    unittest.main()
