"""Command-line interface for routeprobe."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from routeprobe.exporter import ExportError, export_report
from routeprobe.filter import filter_routes
from routeprobe.reporter import ReportFormatter
from routeprobe.runner import run_routes
from routeprobe.spec_loader import SpecLoadError, load_spec


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="routeprobe",
        description="Validate API routes from a YAML spec.",
    )
    parser.add_argument("spec", help="Path to the YAML spec file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="format",
        help="Output format for the console report (default: text).",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        metavar="TAG",
        default=None,
        help="Only probe routes that carry at least one of these tags.",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Export the report to FILE (format inferred from extension: .json or .xml).",
    )
    parser.add_argument(
        "--export-format",
        choices=["json", "junit"],
        default=None,
        dest="export_format",
        help="Explicit export format; overrides extension detection.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        spec = load_spec(args.spec)
    except SpecLoadError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 2

    routes = spec["routes"]
    if args.tags:
        routes = filter_routes(routes, tags=args.tags)

    report = run_routes(spec["base_url"], routes)

    formatter = ReportFormatter(report, fmt=args.format)
    print(formatter.render())

    if args.export:
        fmt = args.export_format
        if fmt is None:
            ext = args.export.rsplit(".", 1)[-1].lower()
            fmt = "junit" if ext == "xml" else "json"
        try:
            export_report(report, args.export, fmt)
        except ExportError as exc:
            print(f"Export failed: {exc}", file=sys.stderr)
            return 2

    return 0 if report.failed == 0 else 1
