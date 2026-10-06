"""Factory acceptance-scenario runner.

Interprets a target repo's `.factory/runtime.yml` + `.factory/scenarios/*.yml`,
brings the app up in a container, drives the declared scenarios, and gates on
them (nonzero exit on failure). Invoked by the reusable `acceptance.yml` CI
workflow; the factory's tester node reads the resulting check conclusion.

Stack-agnostic by construction: this runner is always Python, but the app under
test runs in a container declared by the target repo, so nothing here is tied to
the app's language or framework.
"""
