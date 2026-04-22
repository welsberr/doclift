# Roadmap

## Near Term

- stabilize the normalized bundle schema for downstream adapters
- add a `doclift` bundle consumer path in Didactopus
- extend test coverage around table parsing, title repair, and layout manifests
- add fixture-based regression tests from representative legacy corpora
- improve CLI output for batch conversion summaries

## Format Expansion

- add a higher-fidelity `.docx` path
- add RTF support
- add WordPerfect discovery and conversion plugins
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

- define a Didactopus source adapter for `doclift` bundles
- define a GroundRecall importer for `doclift` manifests and sidecars
- document provenance mapping from `doclift` artifacts into downstream stores
