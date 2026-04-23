from __future__ import annotations

from pydantic import BaseModel, Field


class LayoutLine(BaseModel):
    line_no: int
    indent_level: int = 0
    has_tabs: bool = False
    kind: str
    text: str


class TableArtifact(BaseModel):
    table_id: str
    caption: str
    start_line: int
    end_line: int
    raw_lines: list[str] = Field(default_factory=list)
    parsed_rows: list[list[str]] = Field(default_factory=list)
    section_labels: list[str] = Field(default_factory=list)
    column_count_guess: int = 0


class FigureAsset(BaseModel):
    asset_id: str
    path: str
    relative_path: str
    name: str
    container: str = ""
    looks_like_figure: bool = False


class DocumentBundle(BaseModel):
    document_id: str
    title: str
    document_kind: str = "document"
    source_path: str
    source_path_kind: str = "source_root_relative"
    output_dir: str
    markdown_path: str
    layout_path: str
    tables_path: str
    figures_path: str
    bundle_path_kind: str = "bundle_root_relative"
    table_count: int = 0
    figure_reference_count: int = 0


class ConversionReport(BaseModel):
    source_root: str
    source_root_kind: str = "source_label"
    converter: str
    document_count: int = 0
    documents: list[DocumentBundle] = Field(default_factory=list)
    external_figure_asset_count: int = 0
