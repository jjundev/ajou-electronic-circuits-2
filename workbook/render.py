"""문제집 JSON → 템플릿 HTML → PDF.

템플릿 계약(workbook/templates/*.html): #workbook-data 안의 자리표시자 __WORKBOOK_DATA__ 를 JSON으로 바꾼다.
템플릿은 다 그리면 html[data-ready]를 'true'(실패면 'error')로, body[data-overflow]를 넘친 쪽 id(쉼표)로 둔다.
PDF는 Playwright Chromium으로 만든다. 템플릿의 CDN 글꼴·KaTeX와 로컬 자원은
공통 브라우저 경로가 오프라인에서 응답한다.
템플릿이 KaTeX·글꼴을 못 불렀거나 TeX가 남으면 data-ready를 'error'로, 사유를 html[data-error]에 둔다.
"""
import json
import re
import tempfile
from pathlib import Path

import vendor_route
from browser_runtime import install_render_routes, launch_chromium, local_url
from paths import TEMPLATES

PLACEHOLDER = "__WORKBOOK_DATA__"
TEMPLATE_FILES = {"problems": "problem.html", "answers": "answer.html"}
INSTALL_HINT = "pip3 install --user --break-system-packages playwright"
VIEWPORT = {"width": 1400, "height": 1000}   # 화면 배율 1 (템플릿 screenZoom 기준 297mm ≈ 1123px)
# A4 overview is fitted to 900px high. The full widescreen PDF maps 1440pt to 1920px.
VIDEO_TEXT_SCALE = (900 / (210 * 72 / 25.4)) / (1920 / 1440)


class RenderError(Exception):
    def __init__(self, message, *, error_code="readiness_failed", browser_version=None):
        super().__init__(message)
        self.error_code = error_code
        self.browser_version = browser_version


def load_template(mode, layout="a4"):
    if layout not in ("a4", "video-16x9"):
        raise RenderError(f"알 수 없는 페이지 규격: {layout}")
    template = (TEMPLATES / TEMPLATE_FILES[mode]).read_text(encoding="utf-8")
    if layout == "video-16x9":
        template = re.sub(r'((?:font-size|--fs-body)\s*:\s*)(\d+(?:\.\d+)?)pt',
            lambda m: m[1] + f'{float(m[2])*VIDEO_TEXT_SCALE:.6f}pt', template)
        css = (TEMPLATES / "video-16x9.css").read_text(encoding="utf-8")
        template = template.replace('</head>', '<style>'+css+'</style>'
            '<script>window.workbookVideoLayout=true;</script></head>')
    return template


def inject(template, data):
    """자리표시자를 JSON으로 바꾼다. '<'를 \\u003c로 적어 </script>, <!-- 가 스크립트를 끊지 못하게 한다."""
    count = template.count(PLACEHOLDER)
    if count != 1:
        raise RenderError(f"템플릿의 자리표시자 {PLACEHOLDER} 가 {count}번 있음 (1번이어야 함)")
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace(PLACEHOLDER, payload)


def _render_html(html_path, pdf_path=None, timeout_ms=120_000, *, preflight=False):
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RenderError(f"playwright가 없음. 설치: {INSTALL_HINT}", error_code="launch_failed") from e

    html = Path(html_path).resolve()
    browser_version = None
    stage = "launch_failed"
    try:
        with sync_playwright() as pw:
            browser = launch_chromium(pw)
            browser_version = browser.version
            try:
                stage = "transport_failed"
                page = browser.new_page(viewport=VIEWPORT, offline=True, service_workers="block")
                blocked = set()
                install_render_routes(page, local_roots=(html.parent,),
                                      vendor_resolver=vendor_route.resolve_asset, blocked=blocked)
                failed_resources = set()
                if preflight:
                    page.on("requestfailed", lambda r: failed_resources.add((r.resource_type, r.url)))
                    page.on("response", lambda r: failed_resources.add((r.request.resource_type, r.url))
                            if r.status >= 400 else None)
                response = page.goto(local_url(html, html.parent), timeout=timeout_ms)
                if response is None or not response.ok:
                    raise RenderError(f"HTML 요청 실패: {html}", error_code=stage,
                                      browser_version=browser_version)

                stage = "readiness_failed"
                page.wait_for_function("document.documentElement.dataset.ready", timeout=timeout_ms)
                ready, overflow, reason = page.evaluate(
                    "[document.documentElement.dataset.ready, document.body.dataset.overflow || '',"
                    " document.documentElement.dataset.error || '']")
                if preflight:
                    _check_preflight_page(page, failed_resources, blocked, ready, browser_version)
                if ready != "true":
                    detail = "; ".join(x for x in [reason, *sorted(blocked)] if x)
                    raise RenderError(f"템플릿이 데이터를 그리지 못함 (data-ready={ready!r}): {html}"
                                      + (f" — {detail}" if detail else ""), browser_version=browser_version)
                typography = page.evaluate("""Object.fromEntries([...document.querySelectorAll('.page--problem')].map(p => {
                    const panel=p.querySelector('.panel'), work=p.querySelector('.work');
                    const scale=n=>{const t=getComputedStyle(n).transform;return t==='none'?1:new DOMMatrix(t).a;};
                    return [p.id, {panel:parseFloat(getComputedStyle(panel).getPropertyValue('--fs'))||1,
                        solution:parseFloat(getComputedStyle(work).getPropertyValue('--sfs'))||1,
                        math:[...p.querySelectorAll('.katex-display > .katex')].map(scale),
                        hints:[...p.querySelectorAll('.hint-strip-formula')].map(scale)}];
                }))""")
                if pdf_path is not None:
                    stage = "pdf_failed"
                    page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
            finally:
                browser.close()
    except PlaywrightError as e:
        raise RenderError(f"Chromium 렌더링 실패: {e}", error_code=stage,
                          browser_version=browser_version) from e
    return {"overflow": [x for x in overflow.split(",") if x], "typography": typography,
            "browser_version": browser_version}


def _check_preflight_page(page, failed_resources, blocked, ready, browser_version):
    checks = page.evaluate("""async () => {
        await document.fonts.ready;
        const loaded = [...document.fonts].filter(f => f.status === 'loaded')
            .map(f => f.family.replace(/["']/g, ''));
        const figure = document.querySelector('.fig-band img');
        return {
            font: document.fonts.status === 'loaded' && loaded.includes('Pretendard')
                && loaded.some(family => family.startsWith('KaTeX_')),
            figure: figure?.complete && figure.naturalWidth > 0,
            math: !!document.querySelector('.katex-display .katex-html')
                && !document.querySelector('.katex-error'),
        };
    }""")
    failures = {url for _, url in failed_resources} | blocked
    non_fonts = failures - {url for kind, url in failed_resources if kind == "font"}
    if non_fonts:
        code, reason = "transport_failed", ", ".join(sorted(non_fonts))
    elif failures or (checks["math"] and not checks["font"]):
        code, reason = "font_failed", "Pretendard 또는 KaTeX 글꼴을 불러오지 못함"
        if failures:
            reason += f": {', '.join(sorted(failures))}"
    elif ready != "true":
        return  # The renderer reports the template's own readiness error.
    elif not checks["figure"]:
        code, reason = "transport_failed", "로컬 SVG를 불러오지 못함"
    elif not checks["math"]:
        code, reason = "readiness_failed", "사전 검사 수식을 렌더링하지 못함"
    else:
        return
    raise RenderError(reason, error_code=code, browser_version=browser_version)


def measure_typography(html_path):
    """Freeze A4 fitting scales before adapting point sizes to the video page ratio."""
    return _render_html(html_path)["typography"]


def render_pdf(html_path, pdf_path, timeout_ms=120_000):
    """HTML을 Chromium으로 열어 다 그려지면 PDF로 저장하고, 넘친 쪽 id 목록을 돌려준다."""
    return _render_html(html_path, pdf_path, timeout_ms)["overflow"]


def render_preflight(output_dir: Path) -> dict:
    """Render a real one-page workbook fixture and verify the resulting 16:9 PDF."""
    result = dict(status="fail", browser_version=None, pdf=None, page_count=0, error_code=None)
    output_dir = Path(output_dir)
    pdf = output_dir / "render-preflight.pdf"
    stage = "transport_failed"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".render-preflight-", dir=output_dir) as tmp:
            folder = Path(tmp)
            html = folder / "render-preflight.html"
            svg = folder / "render-preflight.svg"
            svg.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 80">'
                '<path d="M10 40h140 M80 10v60" stroke="black" stroke-width="4"/></svg>',
                encoding="utf-8",
            )
            data = {
                "meta": {"title": "복습팩 렌더 사전 검사", "total": 1},
                "problems": [{
                    "id": "render-preflight", "kind": "예제", "number": "1", "title": "회로도와 수식",
                    "html": {"conditions": r"<p>전류와 저항</p>$$V=I\cdot R$$",
                             "ask": "<p>전압을 계산합니다.</p>"},
                    "figures": [{"src": svg.name, "w_mm": 40, "h_mm": 20}],
                }],
            }
            html.write_text(inject(load_template("problems", "video-16x9"), data), encoding="utf-8")
            candidate = folder / pdf.name
            evidence = _render_html(html, candidate, preflight=True)
            result["browser_version"] = evidence["browser_version"]
            if evidence["overflow"]:
                raise RenderError("사전 검사 템플릿에 페이지 넘침이 있음")
            stage = "pdf_failed"
            import fitz
            with fitz.open(candidate) as document:
                result["page_count"] = document.page_count
                if not document.is_pdf or document.page_count != 1:
                    raise ValueError("사전 검사 PDF는 한 쪽이어야 함")
                width, height = document[0].rect.br
                if abs(width - 1440) > 1 or abs(height - 810) > 1:
                    raise ValueError(f"사전 검사 PDF의 16:9 페이지 크기가 다름: {width}×{height} pt")
            candidate.replace(pdf)
    except RenderError as exc:
        result.update(error_code=exc.error_code, reason=str(exc))
        if exc.browser_version is not None:
            result["browser_version"] = exc.browser_version
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        result.update(error_code=stage, reason=str(exc))
    else:
        result.update(status="pass", pdf=pdf)
    return result
