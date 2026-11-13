"""브라우저가 cdn.jsdelivr.net에 보내는 KaTeX·Pretendard 요청을 저장소 사본으로 답한다.

템플릿과 발행 HTML은 CDN 주소를 그대로 두고, 빌드·검사 때만 요청을 가로챈다.
사본은 paths.VENDOR(provenance.json이 버전과 해시를 고정)에 있다.
매핑 밖의 주소, 버전이 다른 주소, 사본에 없는 파일은 요청을 막고 install()이 돌려준 목록에 남긴다.
"""
import json
import re

import paths

CDN_PATTERN = "https://cdn.jsdelivr.net/**"
_KATEX_RE = re.compile(r"^https://cdn\.jsdelivr\.net/npm/katex@([^/]+)/dist/(.+)$")
_PRETENDARD_RE = re.compile(
    r"^https://cdn\.jsdelivr\.net/(?:npm/pretendard@|gh/orioncactus/pretendard@v)([^/]+)/dist/web/static/(.+)$")
# 템플릿마다 압축본·일반본 이름이 달라도 사본은 하나다
_ALIASES = {"pretendard.min.css": "pretendard.css"}


def _versions(vendor):
    return json.loads((vendor / "provenance.json").read_text(encoding="utf-8"))["packages"]


def resolve(url, vendor=None):
    """CDN 주소를 사본 파일 경로로 바꾼다. 맞는 사본이 없으면 (None, 사유)."""
    vendor = paths.VENDOR if vendor is None else vendor
    try:
        versions = _versions(vendor)
    except (OSError, ValueError, KeyError) as e:
        return None, f"사본 목록을 읽지 못함 ({vendor / 'provenance.json'}): {e}"
    url = url.split("?", 1)[0].split("#", 1)[0]
    for package, pattern in (("katex", _KATEX_RE), ("pretendard", _PRETENDARD_RE)):
        m = pattern.match(url)
        if not m:
            continue
        version, rel = m[1], m[2]
        if version != versions.get(package):
            return None, f"{package} 버전 {version} ≠ 사본 {versions.get(package)}: {url}"
        rel = _ALIASES.get(rel, rel)
        target = (vendor / package / rel).resolve()
        root = (vendor / package).resolve()
        if root not in target.parents or not target.is_file():
            return None, f"사본에 없음: {url}"
        return target, None
    return None, f"사본 매핑 밖의 주소: {url}"


def install(page, vendor=None):
    """page의 CDN 요청을 사본으로 답하게 하고, 막힌 요청 사유를 모을 목록을 돌려준다."""
    misses = []

    def handle(route):
        target, reason = resolve(route.request.url, vendor)
        if target is None:
            misses.append(reason)
            route.abort()
        else:
            route.fulfill(path=str(target))

    page.route(CDN_PATTERN, handle)
    return misses
