"""Djot reader/writer — constrained slice."""
from ._template import FormatConfig, register

# Djot uses markdown-like surface for our admitted slice, with `~~~` for code fences.
register(FormatConfig(
    name='djot',
    code_block=lambda info, body: [f'~~~{info}'.rstrip(), *body.split('\n'), '~~~'],
))
