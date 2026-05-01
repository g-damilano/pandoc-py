"""Textile reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='textile',
    heading=lambda lvl, text: f'h{max(1, min(lvl, 6))}. ' + text,
    bullet_prefix='* ',
    ordered_prefix=lambda n: '# ',
    quote_prefix='bq. ',
    # Pandoc-aligned: bc. on a single line with content (line-based, no closer).
    code_block=lambda info, body: [f'bc. {body}'],
))
