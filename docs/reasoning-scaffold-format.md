# Reasoning Scaffold Format

doclift should support reviewed reasoning scaffolds as an extraction and emission target for educational documents. The goal is to turn long prose, app guides, and source notes into stable concept records that downstream systems can review and reuse.

## Boundary

A reasoning scaffold is not raw hidden chain-of-thought. It is a compact, public, reviewable representation of useful reasoning:

- learner question
- answer summary
- verification prompt
- misconception guard
- source slots or reviewed citations
- tool-specific prompt seeds when useful

Downstream tools are expected to use this shape operationally. In particular,
Didactopus should be able to use reviewed scaffold fields to drive learner
questions, evidence checks, misconception handling, and revision prompts.
That makes field preservation part of the contract, not a cosmetic detail.

## Extraction Target

When extracting from a document, prefer records with this shape:

```json
{
  "id": "stable-record-id",
  "type": "definition-check",
  "question": "What question does this record answer?",
  "answer_summary": "Concise reviewed explanation.",
  "verification_prompt": "What should be checked?",
  "misconception_guard": "What mistake should be avoided?",
  "didactopus_prompt_seed": "Optional learner-task prompt."
}
```

The document-level wrapper should include:

- `schema`
- `id`
- `title`
- `created`
- `updated`
- `status`
- `concept_targets`
- `site_links`
- `records`
- `citegeist_source_slots`
- `next_review_steps`

## Reference Fixture

Use the evo-edu Notebook pilot as the first local fixture:

- `notebook/concepts/allele-frequency-change.scaffold.json`

Future doclift work should be able to validate, transform, or generate this shape without requiring the learner-facing HTML.
