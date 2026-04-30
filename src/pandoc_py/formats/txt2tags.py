"""Txt2Tags reader/writer — constrained slice."""
from ._template import FormatConfig, register

# Txt2Tags uses === text === up to ===== text =====
register(FormatConfig(
    name='txt2tags',
    aliases=('t2t',),
    heading=lambda lvl, text: '=' * (max(1, min(lvl, 5)) + 1) + ' ' + text + ' ' + '=' * (max(1, min(lvl, 5)) + 1),
    bullet_prefix='- ',
    ordered_prefix=lambda n: '+ ',
    code_block=lambda info, body: ['```', *body.split('\n'), '```'],
))
