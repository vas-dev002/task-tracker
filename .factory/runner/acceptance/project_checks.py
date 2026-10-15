"""Project-level build/test gates — run every acceptance run, for ANY stack.

Distinct from checks.py (the per-step `expect` vocabulary). A *project check* is a
whole-project command (build / test / lint) that gates the merge. Its commands
come from one of two places:

  1. an explicit `checks:` list in .factory/runtime.yml (human-declared; wins), or
  2. DISCOVERY — scan the repo for known manifests (package.json, go.mod, *.sln,
     Cargo.toml, ...) and run that ecosystem's canonical build/test in each
     manifest's directory.

Discovery exists because a greenfield/scaffold task CREATES the project during the
run: its name and location aren't known when the human writes the contract, but
they ARE present in the tree by the time checks run in CI — so we find them then.
The commands are canonical and name-agnostic (`go build ./...`, `dotnet build`),
so discovery never needs to know what the project was called.

Policy:
  - Toolchain absent (the ecosystem's binary isn't on PATH — e.g. a Go project
    discovered in a Node-only image): SKIP with a warning. A missing toolchain
    must not block a scaffold.
  - Tool present, `build`/`lint`/setup command fails: hard FAIL (gates the merge).
  - A `test` command that fails BECAUSE the runtime has no browser to drive it (a
    browser-based runner like Karma/Cypress/Playwright in a browserless image):
    SKIP with a warning — that is not a real defect. The failure output must name a
    browser-launch problem (see _BROWSER_LAUNCH_FAILURE); a headless runner
    (vitest/jest) that reports genuine failures is NOT excused and hard-FAILS, so a
    real unit-test failure can never hide behind the missing-browser skip.
  - A `test` that fails WITH a browser present: hard FAIL.
"""

from __future__ import annotations

import fnmatch
import os
import shlex

# Directories discovery never descends into (dependencies, build output, VCS).
_SKIP_DIRS = {
    ".git", "node_modules", "vendor", "bin", "obj", "target", "dist",
    ".angular", "__pycache__", ".venv", "venv", ".factory", ".github",
}


class _Ecosystem:
    """How to recognise a stack and the canonical checks to run for it.

    `commands` are `(label, shell_command, kind)`; kind drives the fail/skip policy
    (`setup`/`build`/`lint` hard-fail, `test` may skip when no browser is present).
    """

    def __init__(self, name, manifests, globs, tool, commands):
        self.name = name
        self.manifests = manifests      # exact filenames, e.g. {"go.mod"}
        self.globs = globs              # fnmatch patterns, e.g. ("*.sln",)
        self.tool = tool                # binary probed with `command -v`
        self.commands = commands

    def matches(self, files):
        if any(f in self.manifests for f in files):
            return True
        return any(fnmatch.fnmatch(f, g) for f in files for g in self.globs)


ECOSYSTEMS = [
    _Ecosystem("go", {"go.mod"}, (), "go", [
        ("go build", "go build ./...", "build"),
        ("go test", "go test ./...", "test"),
    ]),
    _Ecosystem("rust", {"Cargo.toml"}, (), "cargo", [
        ("cargo build", "cargo build --locked", "build"),
        ("cargo test", "cargo test --locked", "test"),
    ]),
    _Ecosystem("dotnet-sln", set(), ("*.sln",), "dotnet", [
        ("dotnet build", "dotnet build", "build"),
        ("dotnet test", "dotnet test", "test"),
    ]),
    _Ecosystem("dotnet-proj", set(), ("*.csproj",), "dotnet", [
        ("dotnet build", "dotnet build", "build"),
        ("dotnet test", "dotnet test", "test"),
    ]),
    _Ecosystem("node", {"package.json"}, (), "npm", [
        ("npm ci", "npm ci", "setup"),
        ("npm run lint", "npm run lint --if-present", "lint"),
        ("npm run build", "npm run build --if-present", "build"),
        ("npm test", "npm test --if-present", "test"),
    ]),
]


def discover(workspace):
    """Return `[(ecosystem, reldir)]` for every manifest found under `workspace`.

    Walks the tree (skipping deps/build/VCS dirs). `reldir` is the manifest's
    directory relative to the repo root (""/`.` for root). .csproj groups are
    dropped when any .sln exists — the solution build already covers them."""
    hits = []
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
        rel = os.path.relpath(root, workspace)
        rel = "" if rel == "." else rel.replace("\\", "/")
        for eco in ECOSYSTEMS:
            if eco.matches(files):
                hits.append((eco, rel))
    if any(eco.name == "dotnet-sln" for eco, _ in hits):
        hits = [(eco, rel) for eco, rel in hits if eco.name != "dotnet-proj"]
    return hits


def _discovered_checks(workspace):
    checks = []
    for eco, reldir in discover(workspace):
        for label, cmd, kind in eco.commands:
            checks.append({
                "name": f"{reldir or '.'}: {label}",
                "run": cmd, "cwd": reldir, "tool": eco.tool, "kind": kind,
            })
    return checks


def _override_checks(declared):
    checks = []
    for d in declared:
        checks.append({
            "name": d.get("name") or d["run"],
            "run": d["run"], "cwd": d.get("cwd") or "",
            "tool": d.get("tool"),            # usually None -> never skipped on absence
            "kind": d.get("kind"),
        })
    return checks


def plan(rt_spec, workspace):
    """The checks to run: the contract's `checks:` override if present, else
    discovery over the workspace."""
    declared = rt_spec.get("checks")
    if declared:
        return _override_checks(declared)
    return _discovered_checks(workspace)


def _has_browser(rt):
    probe = ("command -v chromium || command -v chromium-browser || "
             "command -v google-chrome || command -v chrome")
    return rt.exec(probe)["exit"] == 0


# A failing `test` is only excused when the failure is the runtime having no
# browser to drive (Karma/Cypress/Playwright in a browserless image) — NOT when a
# headless runner (vitest/jest) reports real failures. These substrings mark the
# former; anything else hard-fails, so a genuine unit-test failure can't hide.
_BROWSER_LAUNCH_FAILURE = (
    "no binary for",             # karma-chrome-launcher: "No binary for Chrome…"
    "[launcher]",                # karma launcher errors
    "chromeheadless",
    "cannot find chrome",
    "could not find browser",
    "no usable sandbox",
    "failed to launch",
    "executable doesn't exist",  # playwright
    "playwright install",
    "cypress failed to start",
)


def _is_browser_launch_failure(res) -> bool:
    """True when a failed command's output reads as 'no browser to drive', not a
    real test failure. Scans full stdout+stderr (not the truncated detail)."""
    output = f"{res.get('stdout', '')}\n{res.get('stderr', '')}".lower()
    return any(signature in output for signature in _BROWSER_LAUNCH_FAILURE)


def _result(check, status, exit_code, detail):
    return {"name": check["name"], "cwd": check.get("cwd") or ".",
            "status": status, "exit": exit_code, "detail": detail}


def run(rt, checks):
    """Run each check in the container via `rt.exec`; return result dicts.

    status is "pass" | "fail" | "skip". See the module docstring for the policy."""
    results = []
    tool_present = {}
    browser = None
    for check in checks:
        tool = check.get("tool")
        if tool:
            if tool not in tool_present:
                tool_present[tool] = rt.exec(f"command -v {shlex.quote(tool)}")["exit"] == 0
            if not tool_present[tool]:
                results.append(_result(
                    check, "skip", None,
                    f"toolchain {tool!r} is not available in the runtime image",
                ))
                continue
        cwd = check.get("cwd")
        command = f"cd {shlex.quote(cwd)} && {check['run']}" if cwd else check["run"]
        res = rt.exec(command)
        if res["exit"] == 0:
            results.append(_result(check, "pass", 0, ""))
            continue
        if check.get("kind") == "test":
            if browser is None:
                browser = _has_browser(rt)
            if not browser and _is_browser_launch_failure(res):
                results.append(_result(
                    check, "skip", res["exit"],
                    "test command failed because the runtime has no browser to drive "
                    "it — a browser-based runner (e.g. Karma) in a browserless image; "
                    "declare a capable image or a `checks:` override to gate it",
                ))
                continue
        detail = (res.get("stderr") or res.get("stdout") or "").strip()[-600:]
        results.append(_result(check, "fail", res["exit"], detail))
    return results
