
# Risk register

| Risk ID | Risk | Area | Likelihood | Impact | Trigger | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| R-001 | Implementation grows faster than verification coverage | Program | High | High | New capabilities land without oracle checks | Treat verification as part of done, not a later step | Unassigned | Active |
| R-002 | Grammar broadening creates hard-to-triage semantic drift | Reader / Writer | High | High | Broad parser additions without constrained fixtures | Keep slices fail-closed and comparator-backed | Unassigned | Active |
| R-003 | Over-normalization hides real mismatches | Verification | Medium | High | Comparator rules become too permissive | Version and review normalization policy | Unassigned | Active |
| R-004 | Hard container formats absorb effort before core semantics stabilize | Program scope | Medium | High | DOCX/PPTX/EPUB work starts too early | Finish stronger AST and structured comparison rails first | Unassigned | Active |
| R-005 | Architectural choices become implicit and are forgotten | Architecture | Medium | Medium | Repeated changes without ADRs | Require decision log updates for architecture shifts | Unassigned | Active |
| R-006 | The captured archive is mistaken for the full structural oracle | Inventory / AST | Medium | High | Future work ignores the external AST package or loses provenance on the local source anchor | Keep the local `pandoc-types` source anchor explicit and require provenance maintenance in future AST rounds | Unassigned | Mitigated |
| R-007 | Package-root split causes missing parity claims for CLI, Lua, or server behavior | Inventory / Scope control | Medium | High | Work tracks only `src/` and ignores `pandoc-cli/`, `pandoc-lua-engine/`, or `pandoc-server/` | Track package root in all mapping and inventory assets | Unassigned | Active |

| R-036 | Control-surface refactor breaks existing conversion routes | CLI / Parsing | Medium | High | Moving helper logic out of markdown reader and main CLI | Run targeted markdown/json/html/native regression tests before matrix admission | Open | Mitigated in v36 with targeted route tests + smoke helper tests |
