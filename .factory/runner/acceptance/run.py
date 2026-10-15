"""CLI entrypoint: run the declared acceptance scenarios and gate on them.

    python -m acceptance.run --manifest .factory/runtime.yml \
                             --scenarios .factory/scenarios \
                             --artifacts ./.factory-artifacts

Writes <artifacts>/summary.json (+ app.log and screenshots/), prints a short
table, and exits nonzero if any scenario failed — which is what makes the CI
`acceptance` check red and the factory's tester node loop the task back.
"""

from __future__ import annotations

import argparse
import json
import logging
import os

from . import drivers, manifest, project_checks
from .runtime import Runtime

log = logging.getLogger("acceptance.run")


def main(argv=None):
    ap = argparse.ArgumentParser("acceptance.run")
    ap.add_argument("--manifest", default=".factory/runtime.yml")
    ap.add_argument("--scenarios", default=".factory/scenarios")
    ap.add_argument("--artifacts", default="./.factory-artifacts")
    ap.add_argument("--workspace", default=".")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")

    rt_spec = manifest.load_runtime(args.manifest)
    scenarios = manifest.load_scenarios(args.scenarios)
    os.makedirs(args.artifacts, exist_ok=True)

    results = []
    checks = []
    try:
        with Runtime(rt_spec, args.artifacts, workspace=args.workspace) as rt:
            # Project-level build/test gates first (discovered, or the contract's
            # `checks:` override). A hard failure skips the behavioural scenarios —
            # no point exercising behaviour that doesn't build.
            checks = project_checks.run(rt, project_checks.plan(rt_spec, rt.workspace))
            for c in checks:
                log.info("check [%s] %s (%s)", c["status"], c["name"], c["cwd"])
            if any(c["status"] == "fail" for c in checks):
                log.error("project checks failed; skipping behavioural scenarios")
            else:
                for sc in scenarios:
                    log.info("scenario: %s (%s)", sc.get("scenario"), sc.get("_file"))
                    results.append(drivers.run_scenario(sc, rt, args.artifacts))
    except Exception as exc:        # noqa: BLE001 - bring-up failure == acceptance failure
        log.error("runtime error: %s", exc)
        results.append({
            "scenario": "<runtime bring-up>", "file": args.manifest, "ok": False,
            "steps": [{"id": None, "name": "bring up runtime", "ok": False,
                       "failures": [str(exc)], "screenshots": []}],
        })

    checks_ok = all(c["status"] != "fail" for c in checks)
    scenarios_ok = all(r["ok"] for r in results)
    summary = {"ok": checks_ok and scenarios_ok, "checks": checks, "scenarios": results}
    with open(os.path.join(args.artifacts, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    _print(summary)
    return 0 if summary["ok"] else 1


def _print(summary):
    for c in summary.get("checks", []):
        mark = {"pass": "ok ", "fail": "XX ", "skip": ".. "}.get(c["status"], "?? ")
        print(f"[{c['status'].upper()}] check {c['name']}")
        if c["status"] != "pass" and c.get("detail"):
            print(f"   {mark}{c['detail']}")
    for sc in summary["scenarios"]:
        print(f"[{'PASS' if sc['ok'] else 'FAIL'}] {sc['scenario']} ({sc['file']})")
        for st in sc["steps"]:
            print(f"   {'ok ' if st['ok'] else 'XX '}{st['name']}")
            for f in st["failures"]:
                print(f"       - {f}")
    print(f"\n{'ALL PASSED' if summary['ok'] else 'FAILURES'}")


if __name__ == "__main__":
    raise SystemExit(main())
