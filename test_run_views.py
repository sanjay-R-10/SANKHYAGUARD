from run_views import get_work_items


def test_language_filter_preserves_selection():
    all_pilot = get_work_items(True, None)
    kannada_pilot = get_work_items(True, None, {"kn"})
    assert len(all_pilot) == 8, all_pilot
    assert [item["id"] for item, _, _ in kannada_pilot] == [
        "kn_01",
        "kn_11",
        "kn_12",
    ], kannada_pilot
    assert all(language_code == "kn-IN" for _, language_code, _ in kannada_pilot)

    english_clip = get_work_items(True, "en_01", {"en"})
    assert [item["id"] for item, _, _ in english_clip] == ["en_01"], english_clip


if __name__ == "__main__":
    test_language_filter_preserves_selection()
    print("Runner language-filter tests passed")
