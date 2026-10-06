"""Named-step interpolation and the (deliberately small) expectation vocabulary.

Interpolation: a string value `${steps.<id>.response.json.<path>}` is resolved
against the results of earlier steps (keyed by their `id`). A value that is a
single token keeps the referenced type (e.g. a number stays a number); tokens
embedded in a larger string are stringified.

Expectations: each `expect` key maps to a check `(want, ctx) -> (ok, message)`.
`ctx` carries whatever the driver produced — status/headers/json/text for http,
exit/stdout/stderr for cli/custom/library, page/url for browser, plus `_rt` so a
check can shell into the container (file_exists).
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"\$\{([^}]+)\}")


# --- interpolation -----------------------------------------------------------

def interpolate(value, steps):
    if isinstance(value, str):
        whole = _TOKEN.fullmatch(value)
        if whole:                               # single token → preserve type
            return _resolve(whole.group(1), steps)
        return _TOKEN.sub(lambda m: str(_resolve(m.group(1), steps)), value)
    if isinstance(value, dict):
        return {k: interpolate(v, steps) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate(v, steps) for v in value]
    return value


def _resolve(path, steps):
    parts = path.strip().split(".")
    if parts[0] != "steps":
        raise KeyError(f"reference ${{{path}}} must start with 'steps.'")
    cur = steps
    for part in parts[1:]:
        if isinstance(cur, dict):
            if part not in cur:
                raise KeyError(f"reference ${{{path}}}: no key {part!r}")
            cur = cur[part]
        elif isinstance(cur, list):
            cur = cur[int(part)]
        else:
            raise KeyError(f"reference ${{{path}}}: cannot index {type(cur).__name__}")
    return cur


# --- expectations ------------------------------------------------------------

def check_expect(expect, ctx):
    """Return a list of failure messages ([] == all expectations met)."""
    failures = []
    for key, want in (expect or {}).items():
        fn = _CHECKS.get(key)
        if fn is None:
            failures.append(f"unknown expect {key!r}")
            continue
        ok, msg = fn(want, ctx)
        if not ok:
            failures.append(msg)
    return failures


def _status(want, ctx):
    got = ctx.get("status")
    return got == want, f"status {got} != {want}"


def _body_contains(want, ctx):
    text = ctx.get("text") or ""
    return want in text, f"body does not contain {want!r}"


def _headers(want, ctx):
    got = {k.lower(): v for k, v in (ctx.get("headers") or {}).items()}
    for k, v in want.items():
        if got.get(k.lower()) != v:
            return False, f"header {k}={got.get(k.lower())!r} != {v!r}"
    return True, ""


def _json(want, ctx):
    body = ctx.get("json")
    if body is None:
        return False, "response body is not JSON"
    for key in want.get("has", []):
        if not (isinstance(body, dict) and key in body):
            return False, f"json missing key {key!r}"
    if "equals" in want:
        return _subset(want["equals"], body)
    return True, ""


def _subset(want, got):
    """Deep subset match: every key/value in `want` must appear in `got`."""
    if isinstance(want, dict):
        if not isinstance(got, dict):
            return False, f"expected object, got {type(got).__name__}"
        for k, v in want.items():
            if k not in got:
                return False, f"missing key {k!r}"
            ok, msg = _subset(v, got[k])
            if not ok:
                return False, msg
        return True, ""
    if isinstance(want, list):
        if not isinstance(got, list) or len(got) < len(want):
            return False, "list length/type mismatch"
        for i, v in enumerate(want):
            ok, msg = _subset(v, got[i])
            if not ok:
                return False, msg
        return True, ""
    return (want == got), f"{got!r} != {want!r}"


def _exit(want, ctx):
    got = ctx.get("exit")
    return got == want, f"exit {got} != {want}"


def _stdout_contains(want, ctx):
    out = ctx.get("stdout") or ""
    return want in out, f"stdout does not contain {want!r}"


def _file_exists(want, ctx):
    rt = ctx.get("_rt")
    if rt is None:
        return False, "file_exists needs a runtime to check in"
    return rt.exec(["test", "-f", want])["exit"] == 0, f"file not found: {want}"


def _url_contains(want, ctx):
    url = ctx.get("url") or ""
    return want in url, f"url {url!r} does not contain {want!r}"


# Browser checks auto-wait (the Playwright pattern) rather than taking an
# instantaneous reading — SPAs paint after load, so a one-shot is_visible() is
# flaky. Wait up to this long for the element to appear.
_VIS_TIMEOUT_MS = 5000


def _text_visible(want, ctx):
    page = ctx.get("page")
    if page is None:
        return False, "text_visible needs a browser page"
    try:
        page.get_by_text(want).first.wait_for(state="visible", timeout=_VIS_TIMEOUT_MS)
        return True, ""
    except Exception:                            # noqa: BLE001 - timeout == not visible
        return False, f"text not visible: {want!r}"


def _visible(want, ctx):
    page = ctx.get("page")
    if page is None:
        return False, "visible needs a browser page"
    try:
        page.locator(want).first.wait_for(state="visible", timeout=_VIS_TIMEOUT_MS)
        return True, ""
    except Exception:                            # noqa: BLE001
        return False, f"not visible: {want}"


_CHECKS = {
    "status": _status,
    "body_contains": _body_contains,
    "headers": _headers,
    "json": _json,
    "exit": _exit,
    "stdout_contains": _stdout_contains,
    "file_exists": _file_exists,
    "url_contains": _url_contains,
    "text_visible": _text_visible,
    "visible": _visible,
}
