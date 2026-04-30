"""Haddock reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='haddock',
    heading=lambda lvl, text: '=' * max(1, min(lvl, 6)) + ' ' + text,
    bullet_prefix='* ',
    ordered_prefix=lambda n: f'{n}. ',
    code_block=lambda info, body: ['@', *body.split('\n'), '@'],
))
