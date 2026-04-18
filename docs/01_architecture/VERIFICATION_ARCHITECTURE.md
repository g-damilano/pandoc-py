# Verification architecture

## Oracle

Pinned Pandoc CLI is the behavioral oracle until explicitly replaced.

## Execution pattern

For a given fixture:
1. run reference Pandoc
2. run Python port
3. capture stdout, stderr, exit code, and artifacts
4. normalize only as allowed by policy
5. compare using the declared comparator level
6. emit a machine-readable report

## Verification layers

- unit
- golden
- differential smoke
- capability corpus
- extended corpus
- regression locks

## Report minimum fields

- fixture id
- capability id(s)
- input format
- output format
- comparator level
- result
- divergence class when failing
- artifact paths
- notes
