"""Bring the app-under-test up in a container and expose how to reach it.

The container is the universal runtime boundary: the app runs in Docker (declared
per repo in runtime.yml), never on the bare CI runner — so this module is
stack-agnostic. Stage 1 supports two runtime forms:

    runtime: { image: <base>, setup: [<cmd>, ...] }   # inline recipe
    runtime: { dockerfile: ./Dockerfile }             # existing image build

`compose` and `devcontainer` are declared in the schema but raise a clear
"not yet" error here — they're the next runtime forms to implement.
"""

from __future__ import annotations

import contextlib
import logging
import os
import shlex
import socket
import subprocess
import time
import urllib.request
from urllib.parse import urlsplit

log = logging.getLogger("acceptance.runtime")


class RuntimeBringupError(RuntimeError):
    pass


def _run(cmd):
    # Decode as UTF-8 with replacement, NOT text=True: on Windows text=True uses
    # the legacy cp1252 code page, and npm/ng/pytest emit UTF-8 glyphs (✔, box
    # chars) that crash the capture reader thread with UnicodeDecodeError. Mirrors
    # factory.py's -X utf8 guard, but scoped to our own subprocess calls.
    log.info("$ %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")


class Runtime:
    """Context manager: __enter__ brings the app up and probes readiness;
    __exit__ captures container logs and tears the container down."""

    def __init__(self, spec, artifacts, workspace="."):
        self.spec = spec
        self.rt = spec.get("runtime", {})
        self.run_spec = spec.get("run", {})
        self.artifacts = artifacts
        self.workspace = os.path.abspath(workspace)
        self.container = f"factory-aut-{os.getpid()}"
        self.mode = None
        self.base_url = None

    # -- lifecycle ------------------------------------------------------------

    def __enter__(self):
        if "compose" in self.rt or "devcontainer" in self.rt:
            raise RuntimeBringupError(
                "runtime.compose / runtime.devcontainer are not supported yet "
                "(Stage 1 handles inline `image`+`setup` and `dockerfile`)."
            )
        if "dockerfile" in self.rt:
            self._up_dockerfile()
        elif "image" in self.rt:
            self._up_inline()
        else:
            raise RuntimeBringupError(
                "runtime must declare one of: image, dockerfile, compose, devcontainer"
            )
        self._start_app()
        self._wait_ready()
        return self

    def __exit__(self, *exc):
        os.makedirs(self.artifacts, exist_ok=True)
        with contextlib.suppress(Exception):
            logs = _run(["docker", "logs", self.container])
            with open(os.path.join(self.artifacts, "app.log"), "w", encoding="utf-8") as fh:
                fh.write((logs.stdout or "") + (logs.stderr or ""))
        with contextlib.suppress(Exception):
            _run(["docker", "rm", "-f", self.container])
        return False       # never swallow exceptions

    # -- bring-up -------------------------------------------------------------

    def _port_args(self):
        args = []
        for p in (self.run_spec.get("ports") or []):
            args += ["-p", f"{p}:{p}"]
        return args

    def _up_inline(self):
        self.mode = "inline"
        # Hold the container open with `sleep infinity`, mount the checked-out
        # repo at /app, then run setup inside it. The app is started separately
        # by _start_app so we control its lifecycle.
        res = _run([
            "docker", "run", "-d", "--name", self.container, *self._port_args(),
            "-v", f"{self.workspace}:/app", "-w", "/app",
            self.rt["image"], "sleep", "infinity",
        ])
        if res.returncode != 0:
            raise RuntimeBringupError(f"container did not start: {res.stderr.strip()}")
        for cmd in (self.rt.get("setup") or []):
            r = self.exec(cmd)
            if r["exit"] != 0:
                raise RuntimeBringupError(f"setup failed: {cmd}\n{r['stdout']}{r['stderr']}")
        self.base_url = self._infer_base_url()

    def _up_dockerfile(self):
        self.mode = "dockerfile"
        dockerfile = os.path.join(self.workspace, self.rt["dockerfile"])
        context = os.path.dirname(dockerfile) or self.workspace
        tag = self.container
        build = _run(["docker", "build", "-t", tag, "-f", dockerfile, context])
        if build.returncode != 0:
            raise RuntimeBringupError(f"docker build failed: {build.stderr.strip()}")
        # If run.start is given we override the image CMD with a holder and start
        # the app ourselves; otherwise the image's own CMD is the app.
        if self.run_spec.get("start"):
            cmd = ["docker", "run", "-d", "--name", self.container, *self._port_args(),
                   tag, "sh", "-lc", "sleep infinity"]
        else:
            cmd = ["docker", "run", "-d", "--name", self.container, *self._port_args(), tag]
        res = _run(cmd)
        if res.returncode != 0:
            raise RuntimeBringupError(f"container did not start: {res.stderr.strip()}")
        self.base_url = self._infer_base_url()

    def _start_app(self):
        start = self.run_spec.get("start")
        if not start:
            return      # cli/library (no server), or dockerfile CMD already runs it
        env = self.run_spec.get("env") or {}
        prefix = "".join(f"export {k}={shlex.quote(str(v))}; " for k, v in env.items())
        workdir = self.run_spec.get("workdir")
        cd = f"cd {shlex.quote(workdir)}; " if workdir else ""
        res = _run(["docker", "exec", "-d", self.container, "sh", "-lc", f"{prefix}{cd}{start}"])
        if res.returncode != 0:
            raise RuntimeBringupError(f"app did not start: {res.stderr.strip()}")

    # -- reachability ---------------------------------------------------------

    def exec(self, cmd):
        """Run a command inside the app container → {exit, stdout, stderr}."""
        if isinstance(cmd, (list, tuple)):
            cmd = " ".join(shlex.quote(str(c)) for c in cmd)
        res = _run(["docker", "exec", self.container, "sh", "-lc", cmd])
        return {"exit": res.returncode, "stdout": res.stdout, "stderr": res.stderr}

    def _infer_base_url(self):
        ready = self.run_spec.get("ready") or {}
        if ready.get("http"):
            u = urlsplit(ready["http"])
            return f"{u.scheme}://{u.netloc}"
        ports = self.run_spec.get("ports") or []
        return f"http://localhost:{ports[0]}" if ports else None

    def _wait_ready(self):
        ready = self.run_spec.get("ready")
        if not ready:
            return      # nothing to probe (cli/library, or caller accepts the risk)
        timeout = int(ready.get("timeout", 60))
        probe = self._probe_fn(ready)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if probe():
                log.info("app ready")
                return
            time.sleep(1)
        raise RuntimeBringupError(f"app not ready within {timeout}s (probe: {list(ready)})")

    def _probe_fn(self, ready):
        if ready.get("http"):
            url = ready["http"]

            def f():
                try:
                    with urllib.request.urlopen(url, timeout=3) as r:
                        return 200 <= r.status < 400
                except Exception:   # noqa: BLE001 - not-up-yet looks like an error
                    return False
            return f
        if ready.get("tcp"):
            host, _, port = ready["tcp"].partition(":")

            def f():
                with contextlib.suppress(Exception):
                    with socket.create_connection((host, int(port)), timeout=3):
                        return True
                return False
            return f
        if ready.get("log"):
            needle = ready["log"]

            def f():
                logs = _run(["docker", "logs", self.container])
                return needle in (logs.stdout + logs.stderr)
            return f
        return lambda: True
