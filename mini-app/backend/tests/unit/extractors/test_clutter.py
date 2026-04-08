"""Chrome / banner stripping."""

from __future__ import annotations

from app.extractors.clutter import strip_clutter_html


def test_removes_header_nav_footer() -> None:
    html = """<!doctype html><html><body>
    <header><p>H</p></header>
    <nav><a href="/">N</a></nav>
    <main><p>Keep me</p></main>
    <footer>F</footer>
    </body></html>"""
    out = strip_clutter_html(html, "https://example.edu/page")
    assert "Keep me" in out
    assert "<nav" not in out.lower()
    assert "<header" not in out.lower()
    assert "<footer" not in out.lower()


def test_removes_cookie_banner_class() -> None:
    html = """<html><body>
    <div class="cookie-consent-banner">We use cookies</div>
    <article><p>Article body</p></article>
    </body></html>"""
    out = strip_clutter_html(html, "https://example.edu/")
    assert "Article body" in out
    assert "cookies" not in out.lower()
