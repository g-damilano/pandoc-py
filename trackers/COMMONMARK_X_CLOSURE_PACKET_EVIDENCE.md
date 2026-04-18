# CommonMark_X closure packet evidence

This packet closes the next bounded group of oracle-visible `commonmark_x` divergences without widening comparator policy or opening richer format scope.

## Scope admitted in v50

- bullet-list task markers stay literal (`task_list_bullet`)
- ordered-list task markers stay literal (`task_list_ordered`)
- inline footnote syntax stays literal (`footnote_inline`)
- raw HTML comment blocks preserve terminal newline (`raw_block_comment`)
- fenced raw HTML blocks preserve terminal newline (`raw_block_attr`)
- raw HTML script blocks preserve terminal newline (`raw_block_script`)
- raw HTML hr blocks preserve terminal newline (`raw_block_hr`)

## Oracle-backed report counts

Each admitted fixture passed on all four governed `commonmark_x` verification rails:

- input -> JSON
- input -> HTML
- input -> native
- commonmark_x -> commonmark_x output round-trip through oracle reparse

## Total differential evidence

- **28/28** oracle-backed differential reports passing

## Additional targeted unit coverage

- **17/17** `test_commonmark_x_surface.py` tests passing
- **112/112** targeted regression tests passing across `test_commonmark_x_surface.py`, `test_minimal_markdown_slice.py`, and `test_cli_options_surface.py`
