# doclift

`doclift` is a legacy-document normalization toolkit for turning old office documents into reviewable, structured bundles.

The initial target is legacy Word `.doc` files, but the repository boundary is intentionally broader:

- extract legacy document text and metadata
- preserve layout cues that survive extraction
- recover tables, figure references, and other structural signals
- emit normalized Markdown plus JSON sidecars
- produce deterministic conversion reports for downstream systems such as Didactopus and GroundRecall

## Scope

`doclift` is not a learner-facing system. It is a source-normalization layer that other projects can consume.

Current implementation:

- legacy Word `.doc` conversion through `catdoc`
- bundle emission with:
  - `document.md`
  - `document.layout.json`
  - `document.tables.json`
  - `document.figures.json`
  - `manifest.json`
  - `conversion_report.json`
- course/workspace-level external figure asset inventory

Planned follow-on formats:

- WordPerfect
- RTF
- DOCX as a higher-fidelity path
- old HTML
- OCR-assisted scanned documents

## Install

```bash
pip install -e .
doclift --help
```

## Quick Start

Inspect a source:

```bash
doclift inspect /path/to/legacy.doc
```

Convert one document:

```bash
doclift convert /path/to/legacy.doc /tmp/doclift-out
```

Convert a directory tree and inventory external figure assets:

```bash
doclift convert-dir /path/to/source-tree /tmp/doclift-bundle --asset-root /path/to/source-tree
```

## Bundle Layout

```text
out/
  conversion_report.json
  manifest.json
  assets/
    figure_asset_inventory.json
  documents/
    some-doc/
      document.md
      document.layout.json
      document.tables.json
      document.figures.json
```

## Relationship To Other Projects

- `Didactopus` should consume `doclift` bundles rather than own legacy format handling.
- `GroundRecall` can use the same bundles for provenance-aware import.
- other archival or scholarly tooling can reuse the same normalization path without depending on Didactopus.
