# Verification contract

The purpose of verification is to prove behavioral equivalence within an explicit scope.

## Required evidence for a verified slice

- fixture set
- oracle invocation path
- Python invocation path
- declared comparator level
- normalization profile, if any
- result artifacts or report files
- pass/fail result recorded in trackers

## Comparator selection rule

Use the strictest comparator that is valid for the target format:
- byte equality when deterministic
- structured equality for JSON/native/AST-like outputs
- normalized semantic equality for text formats with non-semantic noise
- container-aware equivalence for archive formats
- round-trip AST comparison when direct comparison is brittle
- markdown/commonmark reparse to structured JSON when the writer surface is semantically stable but textually non-canonical

## Failure rule

A failing verification run must result in one of two outcomes:
- same-round fix and rerun, or
- logged divergence with narrowed scope

A failure may not disappear silently.
