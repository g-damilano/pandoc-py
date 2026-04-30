"""Muse reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='muse',
    heading=lambda lvl, text: '*' * max(1, min(lvl, 5)) + ' ' + text,
    bullet_prefix=' - ',
    ordered_prefix=lambda n: f' {n}. ',
    code_block=lambda info, body: ['<example>', *body.split('\n'), '</example>'],
    thematic='----',
))
