import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class VoiceOrbComponentTests(unittest.TestCase):
    def test_orb_component_owns_real_recording_and_voice_reactive_motion(self):
        source = (ROOT / "voice_orb_component" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn('id="orb-button"', source)
        self.assertIn("getUserMedia", source)
        self.assertIn("getByteTimeDomainData", source)
        self.assertIn("--voice-scale", source)
        self.assertIn("encodeWav", source)
        self.assertIn("streamlit:setComponentValue", source)
        self.assertIn("streamlit:componentReady", source)

    def test_old_independent_microphone_control_is_not_used(self):
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("voice_orb(", app_source)
        self.assertNotIn("st.audio_input(", app_source)

    def test_orb_uses_requested_palette_and_reduced_size(self):
        source = (ROOT / "voice_orb_component" / "index.html").read_text(
            encoding="utf-8"
        )
        theme = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
        self.assertIn("--midnight: #05070d", source)
        self.assertIn("--cobalt: #3568ff", source)
        self.assertIn("--lime: #c7f000", source)
        self.assertIn("width: clamp(150px, 29vw, 205px)", source)
        self.assertIn('backgroundColor = "#05070D"', theme)
        self.assertIn('primaryColor = "#3568FF"', theme)

    def test_project_background_art_is_decorative_and_accessible(self):
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn(".stApp::before", app_source)
        self.assertIn(".stApp::after", app_source)
        self.assertIn("height:100vh;min-height:100vh", app_source)
        self.assertIn("[data-testid=\"stMain\"] {position:relative;z-index:1;}", app_source)
        self.assertIn("clip-path:polygon(", app_source)
        self.assertIn("prefers-reduced-motion: reduce", app_source)
        self.assertIn("pointer-events:none", app_source)


if __name__ == "__main__":
    unittest.main()
