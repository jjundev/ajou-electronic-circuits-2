"""Exercise Chromium's offline transport with the production workbook template."""
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Browser, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_preflight_writes_real_pdf_without_file_urls(tmp_path, monkeypatch):
    from render import render_preflight

    requested_urls = []
    new_page = Browser.new_page

    def observe_page(self, **options):
        page = new_page(self, **options)
        page.on('request', lambda request: requested_urls.append(request.url))
        return page

    monkeypatch.setattr(Browser, 'new_page', observe_page)
    result = render_preflight(tmp_path)

    assert result['status'] == 'pass', result
    assert result['page_count'] == 1
    assert result['pdf'].read_bytes().startswith(b'%PDF-')
    assert result['browser_version']
    assert result['error_code'] is None
    assert any(url.endswith('.svg') for url in requested_urls)
    assert any(url.endswith('.woff2') for url in requested_urls)
    assert not any(url.startswith('file:') for url in requested_urls)


def test_local_routes_block_escape_and_unknown_origin(tmp_path):
    from browser_runtime import install_render_routes, launch_chromium, local_url

    root = tmp_path / 'site'
    root.mkdir()
    html = root / 'index.html'
    html.write_text('<title>Local render</title>', encoding='utf-8')
    (root / 'allowed.txt').write_text('allowed', encoding='utf-8')
    outside = tmp_path / 'outside.txt'
    outside.write_text('outside', encoding='utf-8')
    (root / 'shortcut.txt').symlink_to(outside)
    url = local_url(html, root)
    base = url.rsplit('/', 1)[0]
    escaped_path_url = f'{base}/%2e%2e%2foutside.txt'
    symlink_url = f'{base}/shortcut.txt'
    remote_url = 'https://example.invalid/unknown.css'
    blocked = set()

    with sync_playwright() as pw:
        browser = launch_chromium(pw)
        try:
            page = browser.new_page(offline=True)
            install_render_routes(page, local_roots=(root,), blocked=blocked)
            page.goto(url)
            assert urlsplit(page.url).hostname == '127.0.0.1'
            assert page.title() == 'Local render'
            assert page.evaluate("() => fetch('allowed.txt').then(r => r.text())") == 'allowed'
            for denied in (escaped_path_url, symlink_url, remote_url):
                assert page.evaluate('url => fetch(url).then(() => false, () => true)', denied)
        finally:
            browser.close()

    assert {escaped_path_url, symlink_url, remote_url} <= blocked


def test_preflight_rejects_a_fixture_without_rendered_math(tmp_path, monkeypatch):
    import render

    inject = render.inject

    def without_math(template, data):
        data['problems'][0]['html']['conditions'] = '<p>전류와 저항</p>'
        return inject(template, data)

    monkeypatch.setattr(render, 'inject', without_math)
    result = render.render_preflight(tmp_path)

    assert result['status'] == 'fail'
    assert result['error_code'] == 'readiness_failed'
    assert result['pdf'] is None
    assert list(tmp_path.glob('*.pdf')) == []
