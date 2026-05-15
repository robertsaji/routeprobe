"""Command-line interface for RouteProbe."""

from __future__ import annotations

import argparse
import sys

from routeprobe.spec_loader import SpecLoadError, load_spec
from routeprobe.runner import run_spec
from routeprobe.reporter import render_report, OutputFormat


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routeprobe",
        description="Validate API routes against a YAML spec.",
    )
    parser.add_argument(
        "spec",
        metavar="SPEC",
        help="Path to the YAML spec file.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        default=False,
        help="Exit immediately after the first failure.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code (0 = all passed, 1 = failures or error)."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        spec = load_spec(args.spec)
    except SpecLoadError as exc:
        print(f"[routeprobe] Error loading spec: {exc}", file=sys.stderr)
        return 1

    report = run_spec(spec, fail_fast=args.fail_fast)
    fmt: OutputFormat = args.fmt
    print(render_report(report, fmt=fmt))

    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
