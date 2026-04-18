
# Decision log

| Decision ID | Date | Topic | Decision | Alternatives considered | Why chosen | Consequences |
|---|---|---|---|---|---|---|
| ADR-0001 | 2026-04-13 | Behavioral oracle | Use pinned Pandoc CLI as the reference oracle | Hand-authored expected outputs only; embedded Haskell integration | Fastest reliable route to differential verification | Requires version pinning and explicit normalization policy |
| ADR-0002 | 2026-04-15 | Program control layer | Add a formal index, iteration protocol, and contracts to govern all future work | Continue with only prose roadmap and lightweight trackers | Needed to keep multi-round AI work structured and non-random | Raises process discipline, but sharply improves continuity |
| ADR-0003 | 2026-04-15 | Inventory model | Split tracking into an active execution matrix and a repo-scope Haskell capability seed | Force the main capability matrix to immediately include every mapped-only repository surface | Keeps execution progress legible while still surfacing unmapped repository scope | Requires both trackers to be maintained together |
| ADR-0004 | 2026-04-15 | AST source truth | Treat the canonical AST source as externally anchored until `pandoc-types` is separately captured | Pretend `pandoc-main.zip` alone is sufficient | Inventory evidence shows the AST source package is outside the current archive | Blocks full AST-parity claims until the external source is captured |

| ADR-0005 | 2026-04-15 | External AST closure strategy | Capture `Text.Pandoc.Definition` locally as a structural source anchor and generate coverage assets from it before widening repo-scope tracking | Continue treating AST truth as abstractly external; delay source capture until later | Removes the largest remaining structural blind spot without pretending full package vendoring is already solved | Enables honest AST-core completion claims and sets up controlled denominator widening |

| ADR-0036 | 2026-04-15 | Control tranche admission | Admit app/options/parsing rows into the active denominator only after dedicated smoke tests and explicit source modules exist | Keep them implicit until later | Makes percentage more honest without opening unbounded format families | Requires the control layer to remain regression-tested |

| ADR-0042 | 2026-04-17 | Control-plane hardening | Add an explicit operating model, a work-packet contract, a machine-readable iteration-state file, and a validator that checks structural consistency and version drift | Continue relying on prose-only guidance and manual spot checks | Multi-round AI work needs a stricter repository-internal rail system and a fast way to detect control-plane decay | Slightly more process overhead, but better continuity and fewer silent tracker defects |
