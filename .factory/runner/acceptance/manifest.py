"""Load and lightly validate the runtime manifest and scenario files.

Validation is intentionally shallow — enough to give a clear error at load time
instead of a confusing crash mid-run, not a full schema. Deeper checks live where
the data is used (Runtime for the runtime block, drivers for step shapes).
"""

from __future__ import annotations

import pathlib

import yaml

APP_TYPES = {"http", "cli", "browser", "library", "custom"}


class ManifestError(ValueError):
    pass


def load_runtime(path):
    """Parse `.factory/runtime.yml` → dict. Raises ManifestError on hard problems."""
    p = pathlib.Path(path)
    if not p.is_file():
        raise ManifestError(f"runtime manifest not found: {path}")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    app = data.get("app") or {}
    atype = app.get("type")
    if atype not in APP_TYPES:
        raise ManifestError(
            f"app.type must be one of {sorted(APP_TYPES)}, got {atype!r} ({path})"
        )
    data.setdefault("runtime", {})
    data.setdefault("run", {})
    return data


def load_scenarios(directory):
    """Parse every `.factory/scenarios/*.yml` → [dict], sorted by filename."""
    d = pathlib.Path(directory)
    if not d.is_dir():
        raise ManifestError(f"scenarios directory not found: {directory}")

    files = sorted([*d.glob("*.yml"), *d.glob("*.yaml")])
    scenarios = []
    for f in files:
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        steps = doc.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ManifestError(f"{f.name}: missing or empty 'steps'")
        doc.setdefault("scenario", f.stem)
        doc["_file"] = f.name
        scenarios.append(doc)

    if not scenarios:
        raise ManifestError(f"no scenario files (*.yml) in {directory}")
    return scenarios
