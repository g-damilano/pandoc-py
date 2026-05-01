"""Txt2Tags reader/writer — constrained slice."""
from ._template import FormatConfig, register

# Txt2Tags uses === text === up to ===== text =====
register(FormatConfig(
    name='txt2tags',
    aliases=('t2t',),
    # pandoc t2t reader: `=` (one) is H1, `==` is H2, etc.
    heading=lambda lvl, text: '=' * max(1, min(lvl, 5)) + ' ' + text + ' ' + '=' * max(1, min(lvl, 5)),
    bullet_prefix='- ',
    ordered_prefix=lambda n: '+ ',
    code_block=lambda info, body: ['```', *body.split('\n'), '```'],
))
