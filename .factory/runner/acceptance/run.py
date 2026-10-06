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

from . import drivers, manifest
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
    try:
        with Runtime(rt_spec, args.artifacts, workspace=args.workspace) as rt:
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

    summary = {"ok": all(r["ok"] for r in results), "scenarios": results}
    with open(os.path.join(args.artifacts, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    _print(summary)
    return 0 if summary["ok"] else 1


def _print(summary):
    for sc in summary["scenarios"]:
        print(f"[{'PASS' if sc['ok'] else 'FAIL'}] {sc['scenario']} ({sc['file']})")
        for st in sc["steps"]:
            print(f"   {'ok ' if st['ok'] else 'XX '}{st['name']}")
            for f in st["failures"]:
                print(f"       - {f}")
    print(f"\n{'ALL PASSED' if summary['ok'] else 'FAILURES'}")


if __name__ == "__main__":
    raise SystemExit(main())
