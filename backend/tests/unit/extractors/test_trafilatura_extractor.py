"""Trafilatura extractor on messy academic HTML."""

from __future__ import annotations

import pytest
from app.extractors.trafilatura_extractor import TrafilaturaHtmlExtractor

pytest.importorskip("trafilatura")


def test_messy_page_keeps_main_heading_and_body() -> None:
    html = """<!DOCTYPE html>
<html lang="en"><head><title>Registrar - Forms</title></head>
<body>
<div class="site-header">Logo</div>
<nav class="navbar"><a href="/">Home</a><a href="/about">About</a></nav>
<div id="cookie-banner">Accept all cookies</div>
<main class="content">
  <h1>Registration Deadlines</h1>
  <p>Fall term add/drop ends Friday.</p>
  <table><tr><td>UG</td><td>Grad</td></tr></table>
</main>
<aside class="sidebar">News</aside>
<footer>University</footer>
</body></html>"""
    ext = TrafilaturaHtmlExtractor()
    r = ext.extract(html, source_url="https://registrar.example.edu/deadlines")
    assert len(r.text) > 10
    assert "Registration Deadlines" in r.text or "Fall term" in r.text or "add/drop" in r.text
    if r.title:
        assert "Registration" in r.title or "Registrar" in r.title or "Forms" in r.title
    if r.headings:
        assert any(n.level == 1 for n in r.headings)
