"""Vimwiki reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='vimwiki',
    heading=lambda lvl, text: '=' * max(1, min(lvl, 6)) + ' ' + text + ' ' + '=' * max(1, min(lvl, 6)),
    bullet_prefix='* ',
    ordered_prefix=lambda n: '# ',
    code_block=lambda info, body: [f'{{{{{{{info}'.rstrip(), *body.split('\n'), '}}}'],
    thematic='----',
))
