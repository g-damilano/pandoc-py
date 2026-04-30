"""AsciiDoc reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='asciidoc',
    aliases=('asciidoctor',),
    heading=lambda lvl, text: '=' * lvl + ' ' + text,
    code_block=lambda info, body: ['----', *body.split('\n'), '----'],
))
