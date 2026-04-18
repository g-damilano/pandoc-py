
# Haskell to Python mapping

This file is the architectural bridge between the Haskell reference implementation and the Python port.

## Mapping rules

- Map by subsystem and capability, not merely by file-name similarity.
- Track **package root** as well as module path.
- Do not assume `pandoc-main.zip` contains the whole structural oracle.
- Keep the execution matrix focused on active implementation slices, and use the Haskell seed inventory to anchor not-yet-opened work.

## Current source-package picture

| Package root | Role | Python target area | Status |
|---|---|---|---|
| `src/` | Main conversion core and shared libraries | `src/pandoc_py/` | Active port surface |
| `pandoc-cli/` | Executable entry point | `src/pandoc_py/cli/` | Active parity surface |
| `pandoc-lua-engine/` | Lua integration and module bridge | `src/pandoc_py/lua/` | Deferred behind core conversion parity |
| `pandoc-server/` | Server entry surface | `src/pandoc_py/server/` | Deferred behind core conversion parity |
| external `pandoc-types` | Canonical AST source package | `src/pandoc_py/ast/` | Source anchor captured locally; full package pin still open |

## Seed subsystem map

| Subsystem | Haskell source area | Python target area | Notes |
|---|---|---|---|
| AST / definitions | external `pandoc-types` package + JSON/native contracts | `src/pandoc_py/ast/` | Structural oracle is partly external to this archive |
| App / CLI orchestration | `src/Text/Pandoc/App.hs`, `src/Text/Pandoc/App/*`, `pandoc-cli/src/pandoc.hs` | `src/pandoc_py/cli/` | Split across core and CLI package roots |
| Shared parsing | `src/Text/Pandoc/Parsing.hs`, `src/Text/Pandoc/Parsing/*` | `src/pandoc_py/parsing/` | Reusable substrate for reader growth |
| Readers | `src/Text/Pandoc/Readers/*` | `src/pandoc_py/readers/` | 45 top-level reader families surfaced |
| Writers | `src/Text/Pandoc/Writers/*` | `src/pandoc_py/writers/` | 19 top-level writer families surfaced |
| Runtime/class/state | `src/Text/Pandoc/Class*` | `src/pandoc_py/runtime/` | Port policy still open |
| Citeproc | `src/Text/Pandoc/Citeproc*` | `src/pandoc_py/citeproc/` | Keep distinct from narrow citation parsing slices |
| Lua engine | `pandoc-lua-engine/src/Text/Pandoc/Lua*` | `src/pandoc_py/lua/` | Separate package root and later milestone |
| Server | `pandoc-server/src/Text/Pandoc/Server.hs` | `src/pandoc_py/server/` | Defer behind CLI + conversion parity |

## Inventory-backed mapping assets

- `trackers/HASKELL_MODULE_INVENTORY.csv` — module-level inventory across package roots
- `trackers/HASKELL_CAPABILITY_SEED.csv` — module-level capability seed for not-yet-opened work
- `docs/01_architecture/HASKELL_REPO_SCOPE_GAPS.md` — explicit inventory caveats and external references

## Expansion rule

When a new subsystem is opened, update **both**:
1. the active execution matrix: `trackers/CAPABILITY_MATRIX.csv`
2. the repo-scope inventory seed: `trackers/HASKELL_CAPABILITY_SEED.csv`

The first tracks active implementation truth. The second prevents unmapped repository surface from disappearing from view.


## External AST anchor assets

- `third_party/pandoc-types/src/Text/Pandoc/Definition.hs` — local source anchor for the external AST package
- `trackers/PANDOC_TYPES_SYMBOLS.csv` — extracted symbol inventory from the anchored definition source
- `trackers/AST_SOURCE_COVERAGE.csv` — mapping from current Python AST symbols to anchored Haskell symbols

## v36 control tranche

- `src/Text/Pandoc/App.hs` -> `src/pandoc_py/app.py`
- `src/Text/Pandoc/Options.hs` -> `src/pandoc_py/cli/options.py`
- `src/Text/Pandoc/Parsing.hs` -> `src/pandoc_py/parsing/common.py`
- external `pandoc-types/src/Text/Pandoc/Definition.hs` -> `third_party/pandoc-types/src/Text/Pandoc/Definition.hs` (local source anchor)
