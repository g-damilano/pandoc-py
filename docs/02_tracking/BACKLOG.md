
# Backlog

Use one entry per engineering unit.

## Item template

- ID:
- Title:
- Area:
- Type: feature / architecture / verification / infra / docs / bug / divergence
- Haskell reference:
- Python target:
- Why it matters:
- Dependencies:
- Acceptance criteria:
- Verification method:
- Status:
- Owner:
- Notes:

## Active seed items

- ID: INV-M1-001
  Title: Seed Haskell repo inventory across package roots and generate mapping assets
  Area: Program / Architecture / Inventory
  Type: docs / infra
  Haskell reference: `pandoc-main.zip` package roots and Haskell module trees
  Python target: `docs/01_architecture/*`, `trackers/HASKELL_*`, `scripts/extract_haskell_inventory.py`
  Why it matters: prevents false assumptions about scope and gives future iterations a concrete source map
  Dependencies: control scaffold already present
  Acceptance criteria: package-root-aware inventory, scope-gap file, mapping update, module CSV, capability-seed CSV, and extraction script all exist
  Verification method: deterministic regeneration from archive + file review
  Status: complete
  Owner: unassigned
  Notes: inventory shows AST source package is partly external to the archive

- ID: AST-SCOPE-001
  Title: Capture external AST source package and lock AST contract against it
  Area: AST / Inventory / Contracts
  Type: architecture / docs / infra
  Haskell reference: external `pandoc-types` source package
  Python target: `src/pandoc_py/ast/`, `docs/01_architecture/`, `docs/03_contracts/`
  Why it matters: full structural parity cannot be claimed while the canonical AST source is outside the captured inventory
  Dependencies: M1 inventory complete
  Acceptance criteria: external AST source is referenced or ingested; AST contract updated with explicit source anchors; blocker removed from scope-gap register
  Verification method: inventory validation + contract review
  Status: complete
  Owner: unassigned
  Notes: local pandoc-types source anchor and scripted coverage assets now close the active AST scope gap

- ID: CITE-CORE-001
  Title: Add citation primitives to AST and Pandoc-JSON payload support
  Area: AST / JSON / Markdown reader-writer
  Type: feature
  Haskell reference: markdown reader/writer citation handling areas plus citeproc boundaries
  Python target: `src/pandoc_py/ast/`, `src/pandoc_py/readers/markdown.py`, `src/pandoc_py/writers/markdown.py`, `src/pandoc_py/writers/pandoc_json.py`
  Why it matters: next large coherent family with strong user-visible value and clear verification payoff
  Dependencies: active inventory complete; capability rows declared before implementation; external AST scope gap acknowledged
  Acceptance criteria: simple citations parse, serialize, and compare against oracle on declared smoke fixtures
  Verification method: unit + differential smoke + structured JSON
  Status: complete
  Owner: unassigned
  Notes: landed as a constrained citation slice with markdown + JSON parity, smoke fixtures, and explicit exclusion of full citeproc rendering

- ID: WR-NATIVE-001
  Title: Add Pandoc native writer route and oracle-backed semantic verification
  Area: Writer / CLI / Verification
  Type: feature
  Haskell reference: `Text/Pandoc/Writers/Native.hs`, native-format tests
  Python target: `src/pandoc_py/writers/native.py`, `src/pandoc_py/cli/main.py`, `scripts/run_differential.py`
  Why it matters: widens the executable verified surface with a structurally rich debug-orientated output route
  Dependencies: current AST slice, markdown reader, oracle parser for round-trip verification
  Acceptance criteria: markdown→native route exists, reparses through oracle native parser, and passes a curated smoke corpus
  Verification method: unit + differential smoke + oracle native->json round trip
  Status: complete
  Owner: unassigned
  Notes: semantic comparison uses oracle reparse rather than brittle byte-level formatting equality


- ID: CTRL-OPT-PARSE-001
  Title: Admit app/options/parsing control tranche into active governed denominator
  Area: Program / CLI / Parsing
  Type: architecture / feature / verification
  Haskell reference: `src/Text/Pandoc/App.hs`, `src/Text/Pandoc/Options.hs`, `src/Text/Pandoc/Parsing.hs`
  Python target: `src/pandoc_py/app.py`, `src/pandoc_py/cli/options.py`, `src/pandoc_py/parsing/common.py`
  Why it matters: makes the percentage more honest by governing the current control surface instead of leaving it implicit
  Dependencies: AST scope anchor closed; current markdown/json/html/native slice stable
  Acceptance criteria: app/options/parsing modules exist, dedicated smoke tests pass, and rows are admitted into the active matrix
  Verification method: unit smoke
  Status: complete
  Owner: unassigned
  Notes: landed in v36 with 15 passing smoke tests

- [x] Admit implemented markdown/commonmark/html/native module-family seed rows into governed matrix once route evidence is sealed.


- ID: CTRL-PLANE-042
  Title: Harden control plane with operating model, work-packet contract, iteration-state index, and validator
  Area: Program / Governance / Validation
  Type: architecture / infra / docs
  Haskell reference: none directly; governs the full port program
  Python target: `docs/00_program/*`, `docs/03_contracts/*`, `trackers/*`, `scripts/validate_control_plane.py`
  Why it matters: reduces drift across iterations and catches structural inconsistencies such as version/report mismatch before they accumulate
  Dependencies: existing control scaffold
  Acceptance criteria: operating model exists, work-packet contract exists, machine-readable iteration state exists, control-plane validator passes, and project index points to the new rails
  Verification method: run validator + targeted unit suite
  Status: complete
  Owner: unassigned
  Notes: also closes the current package-version/report drift
