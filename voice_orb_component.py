from pathlib import Path

import streamlit.components.v1 as components


_component = components.declare_component(
    "sankhyaguard_voice_orb",
    path=str(Path(__file__).with_name("voice_orb_component")),
)


def voice_orb(max_seconds=15, key=None):
    return _component(
        max_seconds=max_seconds,
        key=key,
        default=None,
    )
