# CommonMark_X breadth continuation evidence

This tranche widens the dedicated `commonmark_x` surface with additional markdown-safe behaviors that were already implemented in the shared markdown core and are now admitted under explicit oracle-backed `commonmark_x` evidence.

## Scope admitted in v46

- code-span paragraphs
- inline-link paragraphs
- soft-break paragraphs
- plain ATX headings
- tight bullet lists
- tight ordered lists
- inline-bearing bullet lists
- inline-bearing ordered lists
- headings containing code spans
- headings containing inline links
- headings containing emphasis and strong inlines
- URI autolink paragraphs
- email-autolink paragraphs

## Oracle-backed report counts

Each admitted fixture passed on all four `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- markdown -> commonmark_x output round-trip

Admitted fixtures:

- `code_span_paragraph`
- `link_paragraph`
- `softbreak_paragraph`
- `atx_heading`
- `bullet_list`
- `ordered_list`
- `bullet_list_inline`
- `ordered_list_inline`
- `heading_code_span`
- `heading_link`
- `heading_emphasis_strong`
- `autolink_paragraph`
- `email_autolink_paragraph`

## Total differential evidence

- **52/52** oracle-backed differential reports passing

All reports live under `tests/differential/reports/smoke_commonmark_x_breadth_v46/`.
