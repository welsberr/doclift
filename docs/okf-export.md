# OKF Companion Export

`doclift` keeps its normalized bundle contract centered on `manifest.json`, per-document Markdown, extracted text, and JSON sidecars. It can also emit an OKF-style companion bundle for tools that prefer human-readable Markdown packages with frontmatter.

```bash
doclift convert-dir /path/to/source-tree /tmp/doclift-bundle --emit-okf
```

The optional companion bundle is written under:

```text
/tmp/doclift-bundle/okf/
  index.md
  log.md
  manifest.json
  documents/
    <document-id>.md
```

Each document page carries frontmatter with the doclift document id, source path, chunk path, table/figure counts, and source Markdown path. The page body reuses the normalized Markdown output, so downstream systems can browse or import doclift output without knowing the full sidecar schema.
