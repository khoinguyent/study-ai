from app.services.chunking.sectionizer import sectionize_document


def test_sectionizer_headings_and_noise_filter():
    text = """
Table of Contents
1. Intro
Some intro text.

Page 1

## Methods
We used various methods.

Page 2
""".strip()
    secs = sectionize_document(text, {})
    assert len(secs) >= 1
    for s in secs:
        assert "Table of Contents" not in s.text
        assert "Page 1" not in s.text
        assert "Page 2" not in s.text


