from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from .convert import convert_directory, convert_supported_file
from .inspect import inspect_path
from .legacy_doc import collect_figure_assets
from .okf_export import emit_okf_bundle


SERVER_INFO = {"name": "doclift-mcp", "version": "0.1.0"}


def _json_text(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


def _inspect_document(arguments: dict[str, Any]) -> dict[str, Any]:
    return _json_text(inspect_path(Path(arguments["source"])))


def _convert_document(arguments: dict[str, Any]) -> dict[str, Any]:
    source = Path(arguments["source"])
    out_dir = Path(arguments["out_dir"])
    asset_root = Path(arguments["asset_root"]) if arguments.get("asset_root") else None
    assets = collect_figure_assets(asset_root) if asset_root else []
    bundle = convert_supported_file(source, source.parent, out_dir, figure_assets=assets)
    return _json_text(bundle.model_dump())


def _convert_directory_tool(arguments: dict[str, Any]) -> dict[str, Any]:
    source_root = Path(arguments["source_root"])
    out_dir = Path(arguments["out_dir"])
    asset_root = Path(arguments["asset_root"]) if arguments.get("asset_root") else None
    report = convert_directory(source_root, out_dir, asset_root=asset_root)
    payload = report.model_dump()
    if arguments.get("emit_okf"):
        payload["okf_bundle"] = emit_okf_bundle(report, out_dir)
    return _json_text(payload)


TOOLS: dict[str, dict[str, Any]] = {
    "inspect_document": {
        "description": "Inspect a legacy document and return format, title, count, and quality metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {"source": {"type": "string"}},
            "required": ["source"],
        },
        "handler": _inspect_document,
    },
    "convert_document": {
        "description": "Convert one supported legacy document into a doclift bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string"},
                "out_dir": {"type": "string"},
                "asset_root": {"type": "string"},
            },
            "required": ["source", "out_dir"],
        },
        "handler": _convert_document,
    },
    "convert_directory": {
        "description": "Convert supported documents under a directory tree into a doclift bundle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_root": {"type": "string"},
                "out_dir": {"type": "string"},
                "asset_root": {"type": "string"},
                "emit_okf": {"type": "boolean", "default": False},
            },
            "required": ["source_root", "out_dir"],
        },
        "handler": _convert_directory_tool,
    },
}


def list_tools() -> list[dict[str, Any]]:
    return [
        {key: value for key, value in tool.items() if key != "handler"} | {"name": name}
        for name, tool in TOOLS.items()
    ]


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    try:
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            }
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            result = {"tools": list_tools()}
        elif method == "tools/call":
            name = params.get("name")
            tool = TOOLS.get(name)
            if tool is None:
                raise ValueError(f"Unknown tool: {name}")
            handler: Callable[[dict[str, Any]], dict[str, Any]] = tool["handler"]
            result = handler(params.get("arguments") or {})
        else:
            raise ValueError(f"Unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def serve(input_stream=sys.stdin, output_stream=sys.stdout) -> None:
    for line in input_stream:
        if not line.strip():
            continue
        response = handle_request(json.loads(line))
        if response is not None:
            output_stream.write(json.dumps(response) + "\n")
            output_stream.flush()


def main() -> None:
    serve()
