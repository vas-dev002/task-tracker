"""Scenario drivers: execute one step against the running app, record its result.

A step names exactly one driver (http/cli/browser/custom/library) plus an
optional `expect`. The result of a step with an `id` is stored so later steps can
interpolate it (see checks.interpolate). A scenario stops at the first failed step.
"""

from __future__ import annotations

import logging
import os
import shlex

import httpx

from . import checks

log = logging.getLogger("acceptance.drivers")

_DRIVER_KEYS = ("http", "cli", "browser", "custom", "library")


def run_scenario(scenario, rt, artifacts):
    steps_ctx = {}          # id -> recorded result, for interpolation
    results = []
    ok_all = True
    for i, step in enumerate(scenario["steps"]):
        name = step.get("name") or step.get("id") or f"step{i + 1}"
        try:
            record, failures = _run_step(step, rt, steps_ctx, artifacts)
        except Exception as exc:    # noqa: BLE001 - a step error is a failure, not a crash
            record, failures = {}, [f"error: {exc}"]
        if step.get("id"):
            steps_ctx[step["id"]] = record
        ok = not failures
        ok_all &= ok
        results.append({
            "id": step.get("id"), "name": name, "ok": ok,
            "failures": failures, "screenshots": record.get("screenshots", []),
        })
        if not ok:
            break               # fail fast within a scenario
    return {
        "scenario": scenario.get("scenario"), "file": scenario.get("_file"),
        "ok": ok_all, "steps": results,
    }


def _run_step(step, rt, steps_ctx, artifacts):
    for key in _DRIVER_KEYS:
        if key in step:
            spec = checks.interpolate(step[key], steps_ctx)
            expect = checks.interpolate(step.get("expect", {}), steps_ctx)
            return _DRIVERS[key](spec, expect, rt, artifacts)
    raise ValueError("step declares no driver (one of http/cli/browser/custom/library)")


# --- http --------------------------------------------------------------------

def _http(spec, expect, rt, artifacts):
    base = (rt.base_url or "").rstrip("/")
    url = base + "/" + str(spec.get("path", "")).lstrip("/")
    resp = httpx.request(
        str(spec.get("method", "GET")).upper(), url,
        headers=spec.get("headers"), json=spec.get("json"),
        params=spec.get("params"), timeout=spec.get("timeout", 30),
    )
    try:
        body = resp.json()
    except Exception:           # noqa: BLE001 - non-JSON body is fine
        body = None
    record = {"response": {
        "status": resp.status_code, "headers": dict(resp.headers),
        "json": body, "text": resp.text,
    }}
    ctx = {"status": resp.status_code, "headers": dict(resp.headers),
           "json": body, "text": resp.text, "_rt": rt}
    return record, checks.check_expect(expect, ctx)


# --- cli / custom / library (run a command in the container) -----------------

def _exec(spec, expect, rt, artifacts):
    cmd = spec.get("run")
    if not cmd and spec.get("args") is not None:
        cmd = " ".join(shlex.quote(str(a)) for a in spec["args"])
    if not cmd:
        raise ValueError("step needs 'run' (string) or 'args' (list)")
    res = rt.exec(cmd)
    ctx = {"exit": res["exit"], "stdout": res["stdout"], "stderr": res["stderr"], "_rt": rt}
    return {"result": ctx}, checks.check_expect(expect, ctx)


# --- browser (Playwright) ----------------------------------------------------

def _browser(spec, expect, rt, artifacts):
    # ponytail: Playwright runs in-process in the factory's acceptance run, so the
    # factory host needs chromium (`playwright install chromium`) for browser
    # scenarios. Stage-2 hermetic option: run in mcr.microsoft.com/playwright via
    # launch-server + connect() on a shared Docker network. Deferred.
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {}, ["playwright not installed; run `playwright install chromium`"]

    base = (rt.base_url or "").rstrip("/")
    shots = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            if spec.get("goto") is not None:
                # networkidle, not the default 'load': an SPA (Angular/React/…)
                # paints after its JS bundle executes, so 'load' fires on a blank
                # page. Waiting for the network to settle gives it time to render
                # before we screenshot/assert.
                page.goto(base + "/" + str(spec["goto"]).lstrip("/"),
                          wait_until="networkidle")
            for item in (spec.get("fill") or []):
                page.fill(item["selector"], str(item["value"]))
            if spec.get("click"):
                page.click(spec["click"])
            if spec.get("wait_for"):
                page.wait_for_selector(spec["wait_for"])
            if "screenshot" in spec:
                shots.append(_screenshot(page, spec["screenshot"], artifacts))
            ctx = {"page": page, "url": page.url, "_rt": rt}
            failures = checks.check_expect(expect, ctx)
        finally:
            browser.close()
    return {"screenshots": shots}, failures


def _screenshot(page, spec, artifacts):
    outdir = os.path.join(artifacts, "screenshots")
    os.makedirs(outdir, exist_ok=True)
    if isinstance(spec, str):
        name, full, selector = spec, False, None
    else:
        name = spec.get("name", "screenshot.png")
        full = bool(spec.get("full_page"))
        selector = spec.get("selector")
    path = os.path.join(outdir, name)
    if selector:
        page.locator(selector).first.screenshot(path=path)
    else:
        page.screenshot(path=path, full_page=full)
    return os.path.relpath(path, artifacts)


_DRIVERS = {
    "http": _http,
    "cli": _exec,
    "custom": _exec,
    "library": _exec,
    "browser": _browser,
}
