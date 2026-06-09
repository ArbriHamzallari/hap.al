from app.security.sanitizer import sanitize_input


def test_strips_html_and_limits_length() -> None:
    raw = "<b>hello</b>" + "x" * 3000
    out = sanitize_input(raw)
    assert "<" not in out
    assert len(out) == 2000


def test_removes_null_bytes() -> None:
    assert "\x00" not in sanitize_input("hi\x00there")
