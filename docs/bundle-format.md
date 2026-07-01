# Bundle Format

## Top-level

`manifest.json`
- bundle version
- source root
- converter summary
- document list

`conversion_report.json`
- per-document conversion metrics
- counts for tables, figure references, and errors

`assets/figure_asset_inventory.json`
- optional inventory of external image/figure files discovered under an asset root

## Per-document

Each normalized document lives under `documents/<document-id>/`.

`document.md`
- readable normalized text
- extracted table and figure sections when available

`document.layout.json`
- line-oriented layout manifest
- indentation, tabs, and coarse line classification

`document.tables.json`
- table references found in text
- recovered tables with captions, raw lines, parsed rows, and source line ranges

`document.figures.json`
- explicit figure references from text
- related external assets when available

`document.chunks.json`
- normalized paragraphs with source line anchors
- first-pass `role` values such as `summary`, `claim`, `premise`, `evidence`,
  `objection`, `critique`, `definition`, `method`, and `question`
- `analysis_hints` for downstream review queues; these are machine cues, not
  reviewed findings
- `confidence_hint` for extraction/classification confidence

## Stability

The schema should be stable enough for downstream adapters.
Converters may improve row parsing or figure linking without breaking field names.
