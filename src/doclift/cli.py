from __future__ import annotations

import argparse
import json
from pathlib import Path

from .convert import convert_directory, convert_doc
from .inspect import inspect_path
from .legacy_doc import collect_figure_assets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Legacy-document normalization toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a source file")
    inspect_parser.add_argument("source")

    convert_parser = subparsers.add_parser("convert", help="Convert a single legacy Word .doc file")
    convert_parser.add_argument("source")
    convert_parser.add_argument("out")
    convert_parser.add_argument("--asset-root", default=None)

    convert_dir_parser = subparsers.add_parser("convert-dir", help="Convert all supported files in a directory tree")
    convert_dir_parser.add_argument("source_root")
    convert_dir_parser.add_argument("out")
    convert_dir_parser.add_argument("--asset-root", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "inspect":
        print(json.dumps(inspect_path(Path(args.source)), indent=2))
        return
    if args.command == "convert":
        asset_root = Path(args.asset_root) if args.asset_root else None
        assets = collect_figure_assets(asset_root) if asset_root else []
        bundle = convert_doc(Path(args.source), Path(args.out), figure_assets=assets)
        print(json.dumps(bundle.model_dump(), indent=2))
        return
    if args.command == "convert-dir":
        asset_root = Path(args.asset_root) if args.asset_root else None
        report = convert_directory(Path(args.source_root), Path(args.out), asset_root=asset_root)
        print(json.dumps(report.model_dump(), indent=2))
        return


if __name__ == "__main__":
    main()
