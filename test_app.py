import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import prisma_client


class AppTests(unittest.TestCase):
    def run_app(self):
        app_path = Path(__file__).with_name("app.py")
        return AppTest.from_file(str(app_path), default_timeout=20).run()

    def process_button(self, app):
        return next(
            button
            for button in app.button
            if button.label == "Process recording (2 Prisma requests)"
        )

    def test_live_mode_is_off_and_startup_never_calls_prisma(self):
        with patch.object(prisma_client, "transcribe") as transcribe:
            app = self.run_app()

        self.assertEqual(len(app.exception), 0, app.exception)
        self.assertFalse(app.session_state["live_mode"])
        self.assertFalse(app.session_state["live-credit-acknowledgement"])
        for language in ("en", "kn", "hi"):
            self.assertEqual(
                sum(button.label.startswith(f"{language}_") for button in app.button),
                24,
            )
        self.assertTrue(self.process_button(app).disabled)
        transcribe.assert_not_called()
        self.assertTrue(any("Replay saved clean-pilot examples" in item.label for item in app.expander))

    def test_live_mode_and_credit_acknowledgement_do_not_process_without_audio(self):
        with patch.object(prisma_client, "transcribe") as transcribe:
            app = self.run_app()
            app.toggle[0].set_value(True)
            app.run()
            app.checkbox[0].set_value(True)
            app.run()

        self.assertTrue(app.session_state["live_mode"])
        self.assertTrue(app.session_state["live-credit-acknowledgement"])
        self.assertTrue(self.process_button(app).disabled)
        transcribe.assert_not_called()

    def test_selected_amount_demo_uses_manifest_language_and_kind(self):
        app = self.run_app()
        next(button for button in app.button if button.label.startswith("kn_11")).click()
        app.run()
        next(button for button in app.button if button.label == "Load into Try it").click()
        app.run()

        self.assertEqual(app.session_state["live-language"], "kn")
        self.assertEqual(app.session_state["live-kind"], "amount")
        self.assertEqual(app.session_state["loaded_demo_audio_id"], "kn_11")
        self.assertIsNone(app.session_state["live_result"])
        self.assertTrue(self.process_button(app).disabled)

    def test_selected_demo_audio_loads_without_calling_prisma(self):
        with patch.object(prisma_client, "transcribe") as transcribe:
            app = self.run_app()
            next(button for button in app.button if button.label.startswith("en_01")).click()
            app.run()
            next(button for button in app.button if button.label == "Load into Try it").click()
            app.run()

        recording = app.session_state["voice_recording"]
        self.assertEqual(app.session_state["selected_demo_audio"], "en_01")
        self.assertEqual(app.session_state["loaded_demo_audio_id"], "en_01")
        self.assertEqual(app.session_state["live-language"], "en")
        self.assertEqual(app.session_state["live-kind"], "digits")
        self.assertEqual(app.session_state["live-digit-length"], 10)
        self.assertEqual(app.session_state["app-navigation"], "Try it")
        self.assertTrue(recording["bytes"].startswith(b"RIFF"))
        self.assertGreater(recording["duration"], 0)
        self.assertTrue(self.process_button(app).disabled)
        transcribe.assert_not_called()

    def make_result(self):
        return {
            "session_id": "test-session",
            "fingerprint": "",
            "kind": "digits",
            "expected_len": 3,
            "api_status": "SUCCESS",
            "transcript_v25": "one two three",
            "transcript_v30": "123",
            "parsed_v25": "123",
            "parsed_v30": "123",
            "guard": {
                "decision": "ACCEPT",
                "value": "123",
                "candidates": ["123"],
                "reasons": [],
                "disputed_positions": [],
            },
            "guard_decision": "ACCEPT",
            "guard_reasons": [],
            "user_confirmation": "",
            "user_correction": "",
            "final_verified_number": "",
            "save_locally": False,
            "api_request_ids": [],
        }

    def test_confirmation_action_saves_final_user_confirmed_number(self):
        app = self.run_app()
        app.session_state["live_result"] = self.make_result()
        app.run()

        yes_button = next(button for button in app.button if button.label == "YES, CORRECT")
        yes_button.click()
        app.run()

        result = app.session_state["live_result"]
        self.assertEqual(result["user_confirmation"], "YES")
        self.assertEqual(result["final_verified_number"], "123")

    def test_correction_action_preserves_original_transcripts(self):
        app = self.run_app()
        app.session_state["live_result"] = self.make_result()
        app.run()

        no_button = next(button for button in app.button if button.label == "NO, INCORRECT")
        no_button.click()
        app.run()
        app.text_input[0].set_value("124")
        app.form_submit_button[0].click()
        app.run()

        result = app.session_state["live_result"]
        self.assertEqual(result["user_confirmation"], "CORRECTED")
        self.assertEqual(result["final_verified_number"], "124")
        self.assertEqual(result["transcript_v25"], "one two three")
        self.assertEqual(result["guard_decision"], "ACCEPT")


if __name__ == "__main__":
    unittest.main()
