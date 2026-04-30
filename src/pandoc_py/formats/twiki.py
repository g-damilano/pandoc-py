"""TWiki reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='twiki',
    heading=lambda lvl, text: '---' + '+' * max(1, min(lvl, 6)) + ' ' + text,
    bullet_prefix='   * ',
    ordered_prefix=lambda n: '   1 ',
    code_block=lambda info, body: ['<verbatim>', *body.split('\n'), '</verbatim>'],
))
