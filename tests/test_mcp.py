from __future__ import annotations

from pathlib import Path

from doclift.mcp import handle_request


def test_mcp_lists_tools() -> None:
    response = handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert {"inspect_document", "convert_document", "convert_directory"} <= names


def test_mcp_inspects_unknown_file(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("plain text", encoding="utf-8")
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "inspect_document", "arguments": {"source": str(source)}},
        }
    )
    text = response["result"]["content"][0]["text"]
    assert '"format_family": "unknown"' in text
    assert '"supported": false' in text


def test_mcp_reports_unknown_tool() -> None:
    response = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "missing", "arguments": {}},
        }
    )
    assert response["error"]["code"] == -32000
    assert "Unknown tool" in response["error"]["message"]
