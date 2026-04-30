"""DokuWiki reader/writer — constrained slice."""
from ._template import FormatConfig, register

# DokuWiki uses ====== H1 ====== through == H6 ==
def _dw_heading(lvl, text):
    eq = '=' * (7 - max(1, min(lvl, 6)))
    return f'{eq} {text} {eq}'

register(FormatConfig(
    name='dokuwiki',
    heading=_dw_heading,
    bullet_prefix='  * ',
    ordered_prefix=lambda n: '  - ',
    code_block=lambda info, body: ['<code>', *body.split('\n'), '</code>'],
    thematic='----',
))
