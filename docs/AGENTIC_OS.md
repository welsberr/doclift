# doclift AgentOS Entry Point

Last reviewed: 2026-06-27

This repository follows the host-level AgentOS configuration at
`/home/netuser/.agentos`.

Overlay: `doclift`

Default roles:

- `grounded-research-assistant`
- `repository-engineer`

Required checks:

- `factual-review`
- `public-release`
- `stale-context-audit`

Private by default:

- Raw extraction dumps.
- Local-only file paths.
- Unreviewed OCR output.
- Copyright-sensitive source material.

Public release rule:

- Publish normalized summaries and allowed excerpts only after provenance,
  license, and quotation limits are reviewed.

Before publishing doclift-derived artifacts, verify source provenance, public
permission, and quotation limits.
