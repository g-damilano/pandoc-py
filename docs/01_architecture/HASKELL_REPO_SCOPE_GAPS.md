
# Haskell repo scope gaps

This file records scope gaps found during inventory so future iterations do not silently assume the current archive is the entire oracle.

## Gap 1 — AST source package is not present in `pandoc-main.zip` (mitigated by local source anchor)

The current archive does **not** include `Text.Pandoc.Definition.hs`.

Operational meaning:
- the canonical Pandoc AST definition is not fully present in this archive,
- the Python port cannot treat `pandoc-main.zip` alone as the complete structural source of truth,
- AST parity work now uses a captured local source anchor from `pandoc-types`, but full package-version pinning remains an explicit follow-up.

## Gap 2 — Repository behavior is split across multiple package roots

The archive contains behavior in:
- `src/` (main core tree)
- `pandoc-cli/`
- `pandoc-lua-engine/`
- `pandoc-server/`

Operational meaning:
- a simple one-root inventory is incomplete,
- CLI, Lua, and server parity must be tracked as separate workstreams,
- completion claims must always state which package roots are in scope.

## Gap 3 — Citeproc is partly present as code and partly supported by data/resources

The main source tree includes `Text/Pandoc/Citeproc/*`, while the repo also carries supporting citeproc-localization resources.

Operational meaning:
- citation parsing can be ported before full bibliography rendering,
- full citeproc parity should remain a later workstream with explicit resource tracking.

## Required operating rule

No future iteration may claim “repository inventory complete” without stating whether the external AST source package has been separately captured.


## Gap-closure note

A local `pandoc-types` definition-source anchor now exists under `third_party/pandoc-types/`, so future work should treat the AST blind spot as **structurally mitigated** rather than still-open. The remaining open item is exact package-version pinning, not total source absence.
