"""AsciiDoc reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='asciidoc',
    aliases=('asciidoctor',),
    # AsciiDoc convention: H1 = `= Title` (document title); pandoc emits
    # H1 as `== Heading` because it reserves `=` for the doctitle.
    heading=lambda lvl, text: '=' * (lvl + 1) + ' ' + text,
    bullet_prefix='* ',
    code_block=lambda info, body: ['....', *body.split('\n'), '....'],
))
