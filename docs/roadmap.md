# Roadmap

## Near Term

- stabilize the normalized bundle schema for downstream adapters
- extend test coverage around table parsing, title repair, and layout manifests
- add fixture-based regression tests from representative legacy corpora
- improve CLI output for batch conversion summaries

## Format Expansion

- add a higher-fidelity `.docx` path
- add RTF support
- harden WordPerfect conversion with fixture-based regression tests and optional
  alternate extractors such as `wp2latex`
- expand quality-gated fallback conversion beyond the current `.doc` text path
- add optional OCR-assisted pipelines for scanned legacy material

## Structural Recovery

- improve multi-line table caption handling
- distinguish equations, taxonomy outlines, and nested lists more accurately
- support figure-to-text linking when explicit references exist
- separate external asset inventory from inferred figure linkage confidence

## Runtime and Packaging

- harden the Docker/Compose runtime for reproducible cross-platform conversion
- add a small HTTP service wrapper for queued conversions
- publish container image and package release workflow

## Integration

- document and harden the `doclift -> Didactopus -> GroundRecall` handoff path
- document provenance mapping from `doclift` artifacts into downstream stores

## Recently Completed

- added WordPerfect `.wp`, `.wp5`, `.wp6`, and `.wpd` conversion through
  LibreOffice writerperfect/libwpd with conversion sidecars
- added a Didactopus source adapter for `doclift` bundles
- added a Didactopus CLI path for `doclift` bundle to draft-pack generation
- added a GroundRecall importer for `doclift` manifests and sidecars
