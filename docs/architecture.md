# Architecture

`doclift` is intended to sit between raw legacy sources and downstream domain-specific systems.

## Layers

1. Format detection
2. Format-specific extraction
3. Structural recovery
4. Normalized bundle emission
5. Downstream import by applications such as Didactopus or GroundRecall

## Design constraints

- deterministic outputs
- explicit provenance
- structured sidecars for non-prose information
- graceful degradation when exact layout cannot be recovered
- container-friendly execution to reduce cross-platform variance

## Output philosophy

The primary artifact is not a page-faithful rendering. It is a normalized bundle:

- readable by humans
- structured enough for agents and pipelines
- explicit about uncertainty and extraction limits

## Initial format strategy

- `.doc`: implemented through `catdoc`, with layout/table recovery on extracted text
- `.docx`: planned as a higher-fidelity path
- `.wpd`: planned as a plugin/adapter target, not hard-coded into core assumptions

## Why separate from Didactopus

`doclift` owns document rescue and normalization complexity.
`Didactopus` should stay focused on course ingestion, concept extraction, and learning-path generation.
