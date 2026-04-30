"""Typst reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='typst',
    heading=lambda lvl, text: '=' * max(1, min(lvl, 6)) + ' ' + text,
    bullet_prefix='- ',
    ordered_prefix=lambda n: '+ ',
    code_block=lambda info, body: ['```' + (info or ''), *body.split('\n'), '```'],
    thematic='#line(length: 100%)',
))
