"""MediaWiki reader/writer — constrained slice."""
from ._template import FormatConfig, register

register(FormatConfig(
    name='mediawiki',
    heading=lambda lvl, text: '=' * lvl + ' ' + text + ' ' + '=' * lvl,
    bullet_prefix='* ',
    ordered_prefix=lambda n: '# ',
    code_block=lambda info, body: ['<pre>', *body.split('\n'), '</pre>'],
    thematic='----',
))
