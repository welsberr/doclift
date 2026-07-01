# Library Argument Ingestion

This document defines the first shared contract for using Library holdings as
grounded input to analysis, site review, research, and writing workflows.

The ingestion goal is not just summarization. Each source should be processed
into traceable units that preserve text provenance and expose argument-bearing
structure for later review.

## Pipeline

1. Inventory source files and record stable source identifiers, paths, hashes,
   source collections, and access restrictions.
2. Normalize documents with `doclift`, preserving extracted text, layout cues,
   table/figure references, conversion provenance, and chunk JSON.
3. Extract citation-bearing spans and resolve candidate works with CiteGeist.
4. Decompose argument-bearing chunks into draft propositions, premises,
   evidence, objections, rebuttals, critiques, and fallacy cues.
5. Import draft records into GroundRecall with source-span anchors and review
   status.
6. Promote reviewed records into Didactopus learning packs, SciSiteForge public
   pages, research notes, or writing scaffolds only after guardrail checks.

## doclift Contract

`document.chunks.json` is the earliest shared handoff. `doclift` should remain
deterministic and conservative:

- `role` is a first-pass chunk role, not a reviewed finding.
- `analysis_hints` lists machine-readable cues for downstream review queues.
- `confidence_hint` describes extraction/classification confidence, not truth.
- `text`, `line_start`, and `line_end` remain the provenance anchor.

Current chunk roles include `summary`, `claim`, `premise`, `evidence`,
`objection`, `critique`, `definition`, `method`, and `question`.

Current hint examples include `argument_chain_candidate`,
`needs_source_support`, `needs_citation_check`, `premise_candidate`,
`evidence_candidate`, `counterargument_candidate`, `critique_candidate`,
`definition_candidate`, and `fallacy_cue:<name>`.

## Local LLM Use

Local LLMs, including GenieHive-backed workers, may propose deeper decomposed
argument records from doclift chunks. Their output should be treated as draft
analysis until reviewed or validated by deterministic checks.

LLM jobs should:

- consume bounded chunks with source identifiers and line/page anchors;
- emit strict JSON records;
- quote only short source spans needed for anchoring;
- distinguish propositions, premises, inferences, conclusions, and critiques;
- preserve uncertainty instead of rewriting it as fact;
- identify known fallacy patterns as cues, not final diagnoses;
- record model, prompt, timestamp, and input hash for replay.

## Fallacy Taxonomy Sources

Fallacy recognition should use an expandable taxonomy rather than a fixed
source-code list. Good seed sources include Wikipedia overview pages for
fallacies, individual fallacy articles, public philosophy/logic teaching
materials, and examples already present in hosted site corpora and the Library.

Taxonomy records should store:

- canonical label;
- aliases and near-synonyms;
- short definition;
- distinguishing conditions;
- common false positives;
- source citations;
- example spans from reviewed public corpora;
- review status.

Many fallacy labels are context-sensitive. Detection should therefore produce
`fallacy_cue:<name>` records and candidate explanations, not automatic
judgments that an argument is fallacious.

## Claim Alignment and Lineage

Matching an ingested argument element to an external claim taxonomy, such as the
TalkOrigins Index to Creationist Claims, is a separate review problem from
extracting the argument element itself. A nearest text match is not sufficient.

Alignment records should store:

- source span and argument element identifier;
- candidate taxonomy entry identifiers;
- positive evidence for each candidate;
- negative evidence and likely confusions;
- match type, such as exact, narrower, broader, analogous, cites, borrows, or
  responds-to;
- confidence and review status;
- reviewer disposition and notes.

When multiple Index entries are plausible, ingestion should preserve all
candidate alignments until review. Downstream systems should avoid presenting a
single canonical Index link unless the alignment has been reviewed or the page
clearly labels it as a candidate.

Lineage analysis should distinguish explicit citation from silent borrowing,
shared stock arguments, paraphrase, and independent recurrence. Silent borrowing
should require stronger evidence than topical similarity: phrasing overlap,
argument-order similarity, shared examples, unusual terminology, or a plausible
publication path.

## Study-Aid Representation Pattern

Study aids such as CliffsNotes and Schaum-style outlines work because they do
more than summarize. They keep the source or subject organized into a stable
learning spine, then add bounded layers for orientation, interpretation,
glossary, practice, and review.

Library ingestion should preserve the same separation:

- source spine: chapter, section, claim, argument lane, or problem type;
- at-a-glance orientation: short public-safe overview and key terms;
- summary: what the source says, anchored to spans;
- analysis: why the source matters, separated from summary;
- glossary: terms, aliases, concepts, people, and claims;
- worked examples: source-backed examples of reasoning, critique, or evidence
  evaluation;
- practice prompts: retrieval questions, alignment checks, critique exercises,
  and source-support checks;
- coverage ledger: what has been summarized, analyzed, practiced, reviewed, or
  left incomplete.

Generated study-aid records must not replace the original source. They should
point back to the source, expose omissions, and distinguish expert-reviewed
analysis from machine-proposed draft aids.

## Guardrails

Forge or equivalent guardrails should enforce:

- no public release of restricted or private Library material;
- no promotion of unreviewed draft analysis as established knowledge;
- no unsupported factual claim without a source anchor or explicit gap marker;
- no hidden loss of content when a summary omits argument elements;
- no publication of long copyrighted excerpts beyond approved quotation limits;
- no search-corpus exposure of workbench-only notes, model logs, or raw queues.
- no study-aid page that hides the distinction between source summary,
  interpretation, practice material, and reviewer judgment.

Every generated summary should either list the argument elements it covers or
carry a `summary_only_incomplete` marker for later decomposition.

## Completeness

Ingestion should keep a completeness ledger per source:

- discovered;
- normalized;
- chunked;
- citation-pass complete;
- argument-pass complete;
- guardrail-pass complete;
- human-reviewed;
- public-safe or restricted.

Partial ingestion is acceptable only when it is visible and resumable.
