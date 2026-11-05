import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import readback
from ui_helpers import candidates_html, friendly_reasons, indian


class ReadbackTests(unittest.TestCase):
    def test_indian_number_formatting(self):
        self.assertEqual(indian(250000), "2,50,000")
        self.assertEqual(indian(13000), "13,000")
        self.assertEqual(indian(999), "999")

    def test_spoken_values_and_language_templates(self):
        self.assertEqual(readback.spoken_value("digits", "9831"), "9 8 3 1")
        self.assertEqual(readback.spoken_value("amount", 15000), "₹15,000")
        english = readback.readback_text("amount", ["15000", "50000"], "en")
        self.assertTrue(english.startswith("I heard two"))
        self.assertIn("₹15,000", english)
        self.assertIn("₹50,000", english)
        self.assertIn("ಎರಡು", readback.readback_text("digits", ["12", "13"], "kn"))
        self.assertIn("दो", readback.readback_text("digits", ["12", "13"], "hi"))
        self.assertIn("again", readback.readback_text("digits", [], "en"))
        self.assertIn(
            "Is that correct", readback.readback_text("digits", ["123456"], "en")
        )

    def test_cache_key_is_stable_and_language_specific(self):
        self.assertEqual(
            readback.cache_path("x", "en"), readback.cache_path("x", "en")
        )
        self.assertNotEqual(
            readback.cache_path("x", "en"), readback.cache_path("x", "kn")
        )

    def test_cached_audio_is_reused_without_synthesis(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous_cache = readback.CACHE
            readback.CACHE = temporary
            try:
                text = "hello"
                path = Path(readback.cache_path(text, "en"))
                path.write_bytes(b"RIFF....WAVE")
                with patch.object(readback.requests, "post") as post:
                    self.assertEqual(readback.synthesize(text, "en"), str(path))
                    post.assert_not_called()
            finally:
                readback.CACHE = previous_cache

    def test_paid_tts_is_disabled_without_a_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous_cache = readback.CACHE
            readback.CACHE = temporary
            try:
                with patch.object(readback.requests, "post") as post:
                    with self.assertRaisesRegex(RuntimeError, "disabled"):
                        readback.synthesize("not cached", "en")
                    post.assert_not_called()
            finally:
                readback.CACHE = previous_cache

    def test_candidate_highlighting_and_friendly_reasons(self):
        html = candidates_html("digits", ["1234", "1243"], [3, 4])
        self.assertEqual(html.count("bad"), 4)
        self.assertIn("₹", candidates_html("amount", ["15000"], []))
        self.assertEqual(
            friendly_reasons(["views_disagree"])[0],
            "The different readings of the audio do not agree.",
        )

if __name__ == "__main__":
    unittest.main()
