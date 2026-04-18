# CommonMark_X structural packet evidence

This tranche widens the dedicated `commonmark_x` surface with additional structural and attribute-bearing behaviors that were already implemented in the shared markdown core and are now admitted under explicit oracle-backed `commonmark_x` evidence.

## Scope admitted in v47

- plain Setext heading pairs
- Setext headings containing inline code
- bracketed span attributes
- heading attribute blocks
- link attribute blocks
- trailing-two-space hard-break paragraphs

## Oracle-backed report counts

Each admitted fixture passed on all four `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- markdown -> commonmark_x output round-trip

Admitted fixtures:

- `setext_headings`
- `setext_heading_inline`
- `bracketed_span`
- `heading_attrs`
- `link_attrs`
- `hardbreak_paragraph_two_space`

## Total differential evidence

- **24/24** oracle-backed differential reports passing

These reports were run as individually bounded packets to avoid the intermittent long-batch subprocess instability seen in larger `commonmark_x` sweeps.
