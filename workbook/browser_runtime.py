"""Chromium and the offline HTTP transport used for repository render checks."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urlsplit

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Playwright

LOCAL_ORIGIN = "http://127.0.0.1:8765"
LOCAL_PREFIX = "/__ec2_local__/"


def launch_chromium(playwright: Playwright, *, executable: Path | None = None) -> Browser:
    """Try the supplied browser, the Playwright bundle, and installed Chrome in order."""
    from playwright.sync_api import Error

    candidates = [(str(executable), {"executable_path": str(executable)})] if executable else []
    candidates += [("Playwright Chromium", {}), ("Google Chrome", {"channel": "chrome"})]
    failures = []
    for name, options in candidates:
        try:
            return playwright.chromium.launch(headless=True, **options)
        except Error as exc:
            failures.append(f"{name}: {str(exc).splitlines()[0]}")
    raise Error("\n".join(failures))


def local_url(path: Path, root: Path) -> str:
    """Build an HTTP URL preserving the relative links in the local directory tree."""
    relative = path.absolute().relative_to(root.absolute())
    if ".." in relative.parts:
        raise ValueError(f"Local path leaves its root: {path}")
    return LOCAL_ORIGIN + LOCAL_PREFIX + quote(relative.as_posix(), safe="/")


def install_render_routes(
    page,
    *,
    local_roots: tuple[Path, ...],
    vendor_resolver: Callable[[str], Path | None] | None = None,
    blocked: set[str],
) -> None:
    """Mount the first root and allow symlinks only into other listed roots."""
    roots = tuple(root.resolve() for root in local_roots)

    def handle(route):
        url = route.request.url
        parsed = urlsplit(url)
        is_local = f"{parsed.scheme}://{parsed.netloc}" == LOCAL_ORIGIN
        try:
            if is_local and roots and parsed.path.startswith(LOCAL_PREFIX):
                decoded = unquote(parsed.path[len(LOCAL_PREFIX):], errors="strict")
                relative = Path(decoded)
                if not relative.is_absolute() and ".." not in relative.parts and "\\" not in decoded:
                    target = (roots[0] / relative).resolve()
                    if any(target.is_relative_to(root) for root in roots):
                        if target.is_file():
                            return route.fulfill(path=str(target))
                        return route.fulfill(status=404, body="Local resource not found")
            elif not is_local and vendor_resolver is not None:
                target = vendor_resolver(url)
                if target is not None and target.is_file():
                    return route.fulfill(path=str(target))
        except (OSError, RuntimeError, ValueError):
            # Malformed paths, unreadable files and circular symlinks are denied.
            pass
        blocked.add(url)
        return route.abort()

    page.route("**/*", handle)
