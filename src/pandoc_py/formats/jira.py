"""Jira/Confluence wiki reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='jira',
    heading=lambda lvl, text: f'h{max(1, min(lvl, 6))}. ' + text,
    bullet_prefix='* ',
    ordered_prefix=lambda n: '# ',
    quote_prefix='bq. ',
    code_block=lambda info, body: ['{code}', *body.split('\n'), '{code}'],
    thematic='----',
))
