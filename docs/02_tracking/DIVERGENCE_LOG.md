# Divergence log

Use this log for every unresolved mismatch between oracle Pandoc and Python behavior.

| Divergence ID | Capability | Fixture / Input | Oracle result | Python result | Severity | Class | Suspected cause | Status | Resolution plan |
|---|---|---|---|---|---|---|---|---|---|
| DIV-SEED-000 | None | None | None | None | None | None | Seed file | Closed | Replace with live divergences as they arise |

| DIV-0033 | CLI-JSON-INPUT-001 | `tests/fixtures/smoke_json/atx_heading.json` via `--from json --to markdown` | Oracle markdown omits or normalizes some auto-generated details differently | The governed route now uses semantic markdown round-trip JSON comparison instead of byte comparison, and heading-attribute spacing in the markdown writer was corrected so the admitted JSON-input corpus reparses identically | Medium | formatting_only | `roundtrip_markdown_json` is now the approved comparator for the current JSON-input markdown route | Closed | admitted as `VER-DIFF-JSON-MARKDOWN-001` and `VER-DIFF-JSON-MARKDOWN-SMOKE-001` after 58 passing oracle-backed semantic markdown reports |

## Divergence classes

- formatting_only
- normalization_gap
- semantic_mismatch
- unsupported_feature
- crash
- performance_regression
- nondeterminism

| DIV-0034 | RD-CMX task list bullet | `tests/fixtures/smoke/task_list_bullet.md` via `--from commonmark_x --to json` | Oracle keeps `[ ]` / `[x]` markers as literal text on this surface | Python now restores task markers to literal text before governed emission on the dedicated commonmark_x surface | Medium | semantic_mismatch | source-format-gated task-marker restoration landed in `read_commonmark_x` | Closed | admitted as `RD-CMX-CLOSURE-TASK-BULLET-001` after 4-rail oracle verification |
| DIV-0035 | RD-CMX task list ordered | `tests/fixtures/smoke/task_list_ordered.md` via `--from commonmark_x --to json` | Oracle keeps ordered-list task markers as literal text on this surface | Python now restores ordered task markers to literal text before governed emission on the dedicated commonmark_x surface | Medium | semantic_mismatch | source-format-gated task-marker restoration landed in `read_commonmark_x` | Closed | admitted as `RD-CMX-CLOSURE-TASK-ORDERED-001` after 4-rail oracle verification |
| DIV-0036 | RD-CMX inline footnote | `tests/fixtures/smoke/footnote_inline.md` via `--from commonmark_x --to json` | Oracle keeps `^[...]` literal in the paragraph on this surface | Python now protects inline-footnote syntax before markdown parsing so the dedicated commonmark_x surface preserves it literally | Medium | semantic_mismatch | inline-note protection landed in `read_commonmark_x` | Closed | admitted as `RD-CMX-CLOSURE-FOOTNOTE-INLINE-001` after 4-rail oracle verification |
| DIV-0037 | RD-CMX raw block comment newline | `tests/fixtures/smoke/raw_block_comment.md` via `--from commonmark_x --to json` | Oracle preserves trailing newline inside `RawBlock` text | Python now preserves the terminal newline on the dedicated commonmark_x surface and trims writer emission to avoid round-trip doubling | Low | semantic_mismatch | commonmark_x raw-block normalization plus writer trim landed | Closed | admitted as `RD-CMX-CLOSURE-RAWBLOCK-COMMENT-001` after 4-rail oracle verification |
| DIV-0038 | RD-CMX raw block attr newline | `tests/fixtures/smoke/raw_block_attr.md` via `--from commonmark_x --to json` | Oracle preserves trailing newline inside `RawBlock` text | Python now preserves the terminal newline on the dedicated commonmark_x surface and trims writer emission to avoid round-trip doubling | Low | semantic_mismatch | commonmark_x raw-block normalization plus writer trim landed | Closed | admitted as `RD-CMX-CLOSURE-RAWBLOCK-ATTR-001` after 4-rail oracle verification |
| DIV-0039 | RD-CMX raw block script newline | `tests/fixtures/smoke/raw_block_script.md` via `--from commonmark_x --to json` | Oracle preserves trailing newline inside `RawBlock` text | Python now preserves the terminal newline on the dedicated commonmark_x surface and trims writer emission to avoid round-trip doubling | Low | semantic_mismatch | commonmark_x raw-block normalization plus writer trim landed | Closed | admitted as `RD-CMX-CLOSURE-RAWBLOCK-SCRIPT-001` after 4-rail oracle verification |
| DIV-0040 | RD-CMX raw block hr newline | `tests/fixtures/smoke/raw_block_hr.md` via `--from commonmark_x --to json` | Oracle preserves trailing newline inside `RawBlock` text | Python now preserves the terminal newline on the dedicated commonmark_x surface and trims writer emission to avoid round-trip doubling | Low | semantic_mismatch | commonmark_x raw-block normalization plus writer trim landed | Closed | admitted as `RD-CMX-CLOSURE-RAWBLOCK-HR-001` after 4-rail oracle verification |
