# Pandoc Haskell → Python Port Program

## Goal
Build a Python implementation of Pandoc that is managed as a staged port rather than an unbounded rewrite, with continuous visibility over:

- what exists in Haskell
- what has been ported to Python
- what is partially implemented
- what remains missing
- what is verified
- what is known to diverge
- what is blocked or risky

The governing rule is not merely “feature present in Python,” but **behavior verified against Pandoc**.

---

## Program objective
Deliver a Python port that can execute the same conversions as Pandoc for a defined scope and produce equivalent outputs under controlled normalization rules, with a verification layer that continuously compares Python behavior against the Haskell reference implementation.

---

## Non-negotiable operating principles

1. **Port by capability slices, not by file count.**
   We do not measure progress by translated modules alone. We measure by user-visible capabilities that are implemented and verified.

2. **Reference behavior remains Pandoc.**
   The Haskell implementation is the oracle until the Python version is mature enough to stand on its own.

3. **Every implementation task must link to verification.**
   No reader, writer, AST node, CLI option, or transform is considered done unless attached to passing differential checks.

4. **Track partiality explicitly.**
   “Implemented but not verified,” “verified for basic cases only,” and “known divergence” are distinct states.

5. **Preserve architecture traceability.**
   Every Python module should map to a known Haskell source area and an explicit capability scope.

---

## Repository program structure recommended for the Python port

```text
pandoc-python/
  docs/
    00_program/
      roadmap.md
      capability-matrix.md
      release-criteria.md
      glossary.md
    01_architecture/
      haskell-to-python-mapping.md
      ast-design.md
      io-boundaries.md
      normalization-rules.md
      verification-architecture.md
    02_tracking/
      backlog.md
      implementation-log.md
      divergence-log.md
      risk-register.md
      decision-log.md
      verification-status.md
  src/
    pandoc_py/
      ast/
      common/
      parsing/
      readers/
      writers/
      transforms/
      media/
      cli/
      lua/
      server/
  tests/
    unit/
    integration/
    golden/
    differential/
    fixtures/
    normalization/
  tools/
    extract_capabilities/
    differential_runner/
    corpus_manager/
    coverage_report/
```

---

## Major workstreams

### WS0 — Program control and observability
Create the management system that prevents drift.

Deliverables:
- roadmap
- backlog
- implementation log
- divergence log
- risk register
- architecture mapping
- capability matrix
- verification dashboard

### WS1 — Static inventory of Pandoc Haskell codebase
Build a map of the Haskell system before porting.

Track:
- source modules
- public entry points
- readers
- writers
- AST types
- option structures
- transforms/filters
- file-format-specific helpers
- CLI/server/lua boundaries
- existing tests and fixtures

Outputs:
- module inventory
- capability inventory
- dependency overview
- Haskell→Python mapping table

### WS2 — Target Python architecture
Define the Python shape before broad translation.

Required decisions:
- AST representation
- parser abstraction style
- streaming vs in-memory boundaries
- error model
- option/config model
- extension handling
- normalization strategy for equivalence
- plugin/filter/lua policy

### WS3 — Core semantic layer
Port the portable conceptual core before format-specific breadth.

Includes:
- document AST
- metadata model
- inline/block primitives
- attributes/classes/identifiers
- citation primitives
- table model
- math/raw blocks/raw inlines
- shared walkers/transforms/utilities

### WS4 — Reader framework
Build the shared parsing framework and then port readers one by one.

Suggested order:
1. native / json-like internal representations
2. markdown
3. html
4. latex
5. docx
6. epub / odt / pptx / others by demand

### WS5 — Writer framework
Build shared rendering abstractions and then port writers by value.

Suggested order:
1. native
2. json
3. markdown
4. html
5. latex
6. docx / pptx / epub / others by demand

### WS6 — CLI compatibility layer
Reproduce the practical user surface.

Includes:
- core flags
- input/output format selection
- metadata flags
- template behavior
- file handling
- error handling
- stdin/stdout paths

### WS7 — Advanced subsystems
These should not block the core port unless required by scope.

Includes:
- citeproc behavior
- lua filters / lua engine integration or compatibility layer
- server functionality
- embedded resources / media bag
- templates
- reference docs
- PDF-related pipeline boundaries

### WS8 — Verification and release gating
This runs continuously, not at the end.

Includes:
- fixture execution against both engines
- output normalization
- AST comparison where appropriate
- semantic comparison for rich formats
- differential reports
- regression locks

---

## Recommended porting order

### Phase 1 — Establish the control system
Before heavy coding:
- create all tracking documents
- define status taxonomy
- define equivalence rules
- inventory the Haskell codebase
- identify target MVP scope

### Phase 2 — Build the verification harness first
Before broad translation:
- install and pin Pandoc reference version
- build a differential runner that invokes Pandoc CLI and Python CLI/library
- define normalization rules for comparisons
- ingest the existing Pandoc test corpus where possible
- generate first capability coverage report

### Phase 3 — Build the core AST and internal native format
This gives a stable internal truth layer.

Minimum outputs:
- Python AST
- serialization to an internal/native representation
- parsing from internal/native representation
- AST walkers and normalization tools

### Phase 4 — Land one end-to-end capability slice
Best first slice:
- Markdown reader
- Native/JSON writer
- CLI path
- Differential tests

This proves the architecture.

### Phase 5 — Expand through paired reader/writer milestones
Suggested paired milestones:
- Markdown reader + Markdown writer
- HTML reader + HTML writer
- LaTeX writer, then LaTeX reader
- Docx reader/writer only when the shared OOXML and archive handling layers are ready

### Phase 6 — Expand CLI coverage and advanced options
Only after core conversions are stable.

### Phase 7 — Advanced subsystems and hard formats
- citeproc
- lua compatibility
- pptx, odt, epub, docx deep parity
- server support if needed

---

## Definition of completion states

Every tracked item must use one of these states:

- **Not started**
- **Mapped only** — Haskell source located, Python target defined
- **Skeleton only** — Python structure created, behavior absent
- **Partially implemented**
- **Implemented, unverified**
- **Verified on smoke corpus**
- **Verified on standard corpus**
- **Verified on extended corpus**
- **Known divergence**
- **Blocked**
- **Deferred**
- **Done**

---

## Capability matrix schema

Use one row per capability.

| Capability ID | Area | Haskell source | Python target | User-visible behavior | Priority | State | Verification level | Known divergences | Notes |
|---|---|---|---|---|---|---|---|---|---|
| RD-MD-001 | Reader | Text/Pandoc/Readers/Markdown | pandoc_py/readers/markdown.py | Parse ATX headings | High | Not started | None | None | Basic markdown block parsing |

This matrix becomes the real source of truth.

---

## Backlog schema

Each backlog item should be written as an engineering unit with verification attached.

### Item template
- **ID:**
- **Title:**
- **Area:**
- **Type:** feature / architecture / verification / infra / docs / bug / divergence
- **Haskell reference:**
- **Python target:**
- **Why it matters:**
- **Dependencies:**
- **Acceptance criteria:**
- **Verification method:** unit / integration / differential / golden / corpus
- **Status:**
- **Owner:**
- **Notes:**

### Example
- **ID:** RD-MD-ATX-001
- **Title:** Port ATX heading parsing from Markdown reader
- **Area:** Reader / Markdown
- **Type:** feature
- **Haskell reference:** `src/Text/Pandoc/Readers/Markdown.hs`
- **Python target:** `src/pandoc_py/readers/markdown.py`
- **Why it matters:** Core markdown functionality
- **Dependencies:** AST heading nodes, attribute parsing
- **Acceptance criteria:** ATX headings parse into equivalent AST structure for agreed fixtures
- **Verification method:** differential AST comparison on fixture corpus
- **Status:** Not started

---

## Implementation log schema

This is chronological and should not be replaced by backlog state changes.

| Date | Entry ID | Area | Change made | Why | Files touched | Verification run | Outcome | Follow-up |
|---|---|---|---|---|---|---|---|---|
| 2026-04-13 | LOG-0001 | Program | Initialized roadmap/backlog/verification structure | Prevent uncontrolled rewrite | docs/00_program, docs/02_tracking | N/A | Complete | Start module inventory |

Use this as an execution diary.

---

## Divergence log schema

This is critical. Do not bury mismatches in general notes.

| Divergence ID | Capability | Fixture / Input | Haskell result | Python result | Severity | Class | Suspected cause | Status | Resolution plan |
|---|---|---|---|---|---|---|---|---|---|
| DIV-0001 | RD-MD-001 | `heading_attributes_01.md` | Heading attr preserved | Attr dropped | High | semantic mismatch | attribute parser incomplete | Open | implement attribute parse and rerun |

### Divergence classes
- formatting-only
- normalization gap
- semantic mismatch
- unsupported feature
- crash
- performance regression
- nondeterminism

---

## Risk register schema

| Risk ID | Risk | Area | Likelihood | Impact | Trigger | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| R-001 | Rewrite expands faster than verification coverage | Program | High | High | Features landing without oracle tests | Verification required in Definition of Done | Open | Active |

Key starting risks:
- parser architecture chosen too early and becomes constraining
- rich binary formats consume effort before core AST is stable
- lua/citeproc/server work obscures base conversion progress
- output comparison too strict or too loose
- normalization rules hide real semantic defects
- Pandoc behavior depends on subtle option interactions not yet modeled

---

## Decision log schema

Every important architecture decision should be captured.

| Decision ID | Date | Topic | Decision | Alternatives considered | Why chosen | Consequences |
|---|---|---|---|---|---|---|
| ADR-0001 | 2026-04-13 | Verification oracle | Treat pinned Pandoc CLI as behavioral oracle | direct Haskell embedding, hand-made expectations only | fastest reliable differential reference | requires version pinning and normalization policy |

---

## Verification architecture

## Core idea
For each supported capability, run the same input through:

1. **Reference Pandoc** (pinned Haskell binary)
2. **Python Pandoc port**

Then compare outputs using the strictest valid comparison method for that capability.

---

## Comparison hierarchy

### Level A — Byte-for-byte equality
Use only when fully deterministic and expected.

Suitable for:
- normalized JSON
- normalized native representations
- some plain text outputs

### Level B — Structured equality
Parse both results into a structured representation and compare trees.

Suitable for:
- AST / native / JSON outputs
- metadata structures
- normalized table structures

### Level C — Semantic normalized equality
Use a normalization layer before comparison.

Normalization examples:
- whitespace normalization
- attribute ordering normalization
- key ordering normalization
- zip container file ordering normalization
- timestamp stripping
- generated IDs or metadata cleanup

Suitable for:
- HTML
- LaTeX
- OOXML-derived outputs

### Level D — Container-aware equivalence
For formats like DOCX, ODT, EPUB, PPTX:
- unpack zip containers
- compare selected XML parts semantically
- ignore irrelevant generated metadata where justified
- compare media bag entries and manifest structures

### Level E — Round-trip semantic tests
When direct output comparison is brittle:
- produce output from Haskell and Python
- read both back into a normalized AST
- compare resulting ASTs

---

## Verification layers to implement

### V1 — Unit tests
Small local behavior tests for Python-only functions.

### V2 — Golden tests
Expected outputs for stable cases.

### V3 — Differential tests
Run reference Pandoc vs Python on same inputs.

### V4 — Corpus tests
Run a large fixture corpus grouped by capability.

### V5 — Regression tests
Any resolved bug/divergence becomes a locked test.

### V6 — Performance guardrails
Track major performance regressions where they matter.

---

## Differential runner design

### Inputs
- fixture file or string
- input format
- output format
- option bundle
- optional normalization profile

### Execution
- invoke pinned `pandoc` binary
- invoke Python CLI/library
- collect stdout/stderr/exit code
- capture artifacts for rich output formats
- normalize
- compare
- emit machine-readable report

### Outputs
- pass/fail
- comparison level used
- diff summary
- full artifact paths
- divergence classification
- capability tags

### Suggested report fields

```json
{
  "fixture_id": "md_heading_attr_001",
  "input_format": "markdown",
  "output_format": "native",
  "pandoc_version": "pinned",
  "python_version": "current",
  "comparison_level": "structured",
  "status": "fail",
  "divergence_class": "semantic mismatch",
  "summary": "Heading attributes missing on Python output"
}
```

---

## Verification corpus strategy

Use multiple concentric corpora.

### Corpus A — Smoke corpus
Very small, fast, always run.

### Corpus B — Capability corpus
Grouped by capability, moderate size.

### Corpus C — Pandoc upstream-derived corpus
Adapt as much of Pandoc’s existing test material as feasible.

### Corpus D — Adversarial corpus
Inputs designed to trigger edge cases:
- nested lists
- mixed attributes
- tables with spans
- citations
- raw blocks/inlines
- unusual encodings
- malformed but tolerated inputs

### Corpus E — Real-world corpus
Representative documents from practical usage.

---

## Normalization policy

This must be explicit and versioned. Otherwise equivalence claims become unreliable.

### Allowed normalization
- trailing whitespace removal
- line ending normalization
- stable key ordering
- stable attribute ordering where order is semantically irrelevant
- removal of known non-semantic generated metadata

### Disallowed normalization
- stripping semantically meaningful nodes
- flattening distinct block types into shared text
- removing links, citations, identifiers, classes, styles, or captions simply to obtain a pass

---

## Release gates

A milestone is not accepted unless:

1. capability rows are mapped
2. Python implementation exists
3. verification exists
4. smoke corpus passes
5. standard corpus pass rate reaches threshold
6. known divergences are documented
7. no untracked failures remain

---

## Recommended MVP scope

To avoid a runaway program, define an MVP such as:

- internal AST
- native/json representation
- markdown reader
- markdown writer
- html writer
- essential CLI path
- differential harness
- backlog + logs + divergence control

This is enough to prove the approach before moving into DOCX/PPTX/ODT complexity.

---

## Initial backlog

### Program / control
- Initialize roadmap, backlog, implementation log, divergence log, risk register
- Define status taxonomy and Definition of Done
- Pin Pandoc reference version
- Define normalization policy v1

### Inventory
- Generate Haskell module inventory
- Tag modules by subsystem: AST, readers, writers, CLI, lua, server, helpers
- Map current Pandoc tests to capabilities
- Build first capability matrix

### Verification
- Implement differential runner shell
- Implement native/json structured comparator
- Implement HTML normalized comparator
- Implement zip-container comparator scaffold for DOCX/ODT/PPTX/EPUB
- Build smoke corpus

### Core implementation
- Define Python AST model
- Implement AST serializers/deserializers
- Implement attribute and metadata primitives
- Implement AST walker utilities

### First functional slice
- Implement native reader/writer or JSON/native interchange
- Implement markdown block parser skeleton
- Port headings, paragraphs, emphasis, strong, links, code, lists
- Add CLI entry point for read→write path
- Run first end-to-end differential suite

---

## Suggested milestone structure

### M0 — Program initialized
Tracking and verification scaffolding exist.

### M1 — Inventory complete
We know what Pandoc contains and how we will map it.

### M2 — Differential harness operational
We can compare both systems on controlled fixtures.

### M3 — Core AST stable
Internal representation supports first real conversions.

### M4 — First verified slice complete
Markdown → native/json works and is differentially tested.

### M5 — First user-usable slice complete
Markdown ↔ Markdown/HTML with CLI path.

### M6+ — Format expansion by value and demand
LaTeX, HTML reader, then rich container formats.

---

## What to track every week

At minimum, produce:
- backlog delta
- capability matrix delta
- new divergences
- resolved divergences
- verification pass rates by capability
- blocked items
- decision log additions
- risk changes

---

## Recommended immediate next actions

1. Create the tracking documents and schemas.
2. Pin the Pandoc reference version used as oracle.
3. Build the Haskell subsystem inventory.
4. Build the capability matrix skeleton.
5. Implement the differential runner for one simple route.
6. Freeze MVP scope before broad coding.

---

## Practical rule for the whole program

A feature is not done when Python can do something.
A feature is done when:
- Python can do it,
- the Haskell reference can do it,
- both have been compared appropriately,
- any remaining mismatch is either resolved or explicitly logged.

