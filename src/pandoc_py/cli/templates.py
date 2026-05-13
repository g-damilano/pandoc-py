"""Minimal pandoc-compatible template engine.

Implements a working subset of pandoc's template language sufficient
for ``--template`` / ``-V`` / metadata interpolation in standalone
documents:

* ``$variable$`` and ``${variable}`` interpolation (period-separated paths
  walk into nested maps).
* ``$if(var)$ … $else$ … $endif$`` conditionals (with ``$elseif$``).
* ``$for(var)$ … $sep$ … $endfor$`` iteration with the anaphoric ``it``.
* A handful of pipes: ``uppercase``, ``lowercase``, ``length``, ``first``,
  ``last``, ``rest``, ``reverse``, ``chomp``, ``pairs``.
* ``$--`` line comments.
* ``$$`` literal-dollar escape.

Implementation strategy: the template is tokenized into a flat stream of
text fragments and directives, then a recursive evaluator walks the
stream so block directives (``$if$ … $endif$``, ``$for$ … $endfor$``)
nest correctly even when they appear inline rather than on their own
lines.
"""
from __future__ import annotations

import re
from typing import Any


_DIRECTIVE_RE = re.compile(
    r'\$\$|\$--[^\n]*\n?|'
    r'\$\s*(?:'
    r'(?P<kind>if|elseif|else|endif|for|sep|endfor)\s*(?:\(\s*(?P<arg>[^)]*?)\s*\))?'
    r'|'
    r'(?P<name>[A-Za-z][\w.\-]*(?:\s*/\s*[A-Za-z][\w-]*(?:\s+[^/$]*?)?)*)'
    r')\s*\$|'
    r'\$\{\s*(?P<bname>[A-Za-z][\w.\-]*(?:\s*/\s*[A-Za-z][\w-]*(?:\s+[^/}]*?)?)*)\s*\}'
)


def _walk(value: Any, parts: list[str]) -> Any:
    cur = value
    for part in parts:
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _is_truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, (list, tuple)):
        return any(_is_truthy(x) for x in value)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, str):
        return value.strip() != ''
    return bool(value)


def _apply_pipe(value: Any, pipe: str) -> Any:
    name, *_args = pipe.split(None, 1)
    name = name.strip()
    if name == 'uppercase':
        return value.upper() if isinstance(value, str) else value
    if name == 'lowercase':
        return value.lower() if isinstance(value, str) else value
    if name == 'length':
        try:
            return len(value)
        except TypeError:
            return 0
    if name == 'first':
        return value[0] if isinstance(value, (list, tuple)) and value else value
    if name == 'last':
        return value[-1] if isinstance(value, (list, tuple)) and value else value
    if name == 'rest':
        return value[1:] if isinstance(value, (list, tuple)) and value else value
    if name == 'reverse':
        if isinstance(value, str):
            return value[::-1]
        if isinstance(value, (list, tuple)):
            return list(reversed(value))
        return value
    if name == 'chomp':
        return value.rstrip() if isinstance(value, str) else value
    if name == 'pairs':
        if isinstance(value, dict):
            return [{'key': k, 'value': v} for k, v in value.items()]
        if isinstance(value, (list, tuple)):
            return [{'key': i + 1, 'value': v} for i, v in enumerate(value)]
        return value
    return value


def _resolve(name: str, ctx: dict[str, Any]) -> Any:
    raw = name.strip()
    pipes: list[str] = []
    if '/' in raw:
        head, *tail = [t.strip() for t in raw.split('/')]
        pipes = tail
        raw = head
    parts = raw.split('.')
    if parts and parts[0] == 'it' and 'it' in ctx:
        value = _walk(ctx['it'], parts[1:])
    else:
        value = _walk(ctx, parts)
    for pipe in pipes:
        value = _apply_pipe(value, pipe)
    return value


def _render_value(value: Any) -> str:
    if value is None or value is False:
        return ''
    if value is True:
        return 'true'
    if isinstance(value, (list, tuple)):
        return ''.join(_render_value(v) for v in value)
    if isinstance(value, dict):
        return 'true' if value else ''
    return str(value)


# --- token stream ---------------------------------------------------------

class _Tok:
    __slots__ = ('kind', 'value', 'arg')

    def __init__(self, kind: str, value: str = '', arg: str = ''):
        self.kind = kind        # 'text', 'var', 'if', 'elseif', 'else', 'endif',
                                #         'for', 'sep', 'endfor', 'literal_dollar', 'comment'
        self.value = value      # text content / variable reference
        self.arg = arg          # for if(...) and for(...)


def _tokenize(template: str) -> list[_Tok]:
    out: list[_Tok] = []
    pos = 0
    for m in _DIRECTIVE_RE.finditer(template):
        if m.start() > pos:
            out.append(_Tok('text', template[pos:m.start()]))
        token = m.group(0)
        if token == '$$':
            out.append(_Tok('text', '$'))
        elif token.startswith('$--'):
            pass  # comment
        elif m.group('kind'):
            out.append(_Tok(m.group('kind'), arg=(m.group('arg') or '').strip()))
        elif m.group('name'):
            out.append(_Tok('var', m.group('name')))
        elif m.group('bname'):
            out.append(_Tok('var', m.group('bname')))
        pos = m.end()
    if pos < len(template):
        out.append(_Tok('text', template[pos:]))
    return out


# --- recursive evaluator --------------------------------------------------

def _eval(tokens: list[_Tok], i: int, ctx: dict[str, Any], stop: set[str]) -> tuple[str, int]:
    parts: list[str] = []
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind in stop:
            return ''.join(parts), i
        if tok.kind == 'text':
            parts.append(tok.value); i += 1
        elif tok.kind == 'var':
            parts.append(_render_value(_resolve(tok.value, ctx))); i += 1
        elif tok.kind == 'if':
            body, i = _eval_if(tokens, i, ctx)
            parts.append(body)
        elif tok.kind == 'for':
            body, i = _eval_for(tokens, i, ctx)
            parts.append(body)
        else:
            # Stray closing/keyword — emit nothing and skip.
            i += 1
    return ''.join(parts), i


def _eval_if(tokens: list[_Tok], i: int, ctx: dict[str, Any]) -> tuple[str, int]:
    """Evaluate $if(arg)$ … $elseif(arg2)$ … $else$ … $endif$ starting at i."""
    cond = tokens[i].arg
    i += 1
    branches: list[tuple[str | None, list[_Tok]]] = []  # (cond, body-tokens)
    cur_cond: str | None = cond
    cur_body: list[_Tok] = []
    depth = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == 'if':
            depth += 1; cur_body.append(tok); i += 1; continue
        if tok.kind == 'endif':
            depth -= 1
            if depth == 0:
                branches.append((cur_cond, cur_body))
                i += 1
                break
            cur_body.append(tok); i += 1; continue
        if depth == 1 and tok.kind == 'elseif':
            branches.append((cur_cond, cur_body))
            cur_cond = tok.arg; cur_body = []; i += 1; continue
        if depth == 1 and tok.kind == 'else':
            branches.append((cur_cond, cur_body))
            cur_cond = None; cur_body = []; i += 1; continue
        cur_body.append(tok); i += 1
    for cond_arg, body in branches:
        if cond_arg is None:
            return _eval(body, 0, ctx, set())[0], i
        if _is_truthy(_resolve(cond_arg, ctx)):
            return _eval(body, 0, ctx, set())[0], i
    return '', i


def _eval_for(tokens: list[_Tok], i: int, ctx: dict[str, Any]) -> tuple[str, int]:
    """Evaluate $for(arg)$ … $sep$ … $endfor$ starting at i."""
    arg = tokens[i].arg
    i += 1
    body: list[_Tok] = []
    sep_body: list[_Tok] = []
    in_sep = False
    depth = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == 'for':
            depth += 1
            (sep_body if in_sep else body).append(tok); i += 1; continue
        if tok.kind == 'endfor':
            depth -= 1
            if depth == 0:
                i += 1; break
            (sep_body if in_sep else body).append(tok); i += 1; continue
        if depth == 1 and tok.kind == 'sep':
            in_sep = True; i += 1; continue
        (sep_body if in_sep else body).append(tok); i += 1

    iterable = _resolve(arg, ctx)
    if iterable is None:
        return '', i
    if isinstance(iterable, dict):
        iterable = [iterable]
    elif not isinstance(iterable, (list, tuple)):
        iterable = [iterable]
    rendered: list[str] = []
    for item in iterable:
        inner_ctx = dict(ctx); inner_ctx['it'] = item; inner_ctx[arg] = item
        rendered.append(_eval(body, 0, inner_ctx, set())[0])
    if sep_body:
        sep_text = _eval(sep_body, 0, ctx, set())[0]
        return sep_text.join(rendered), i
    return ''.join(rendered), i


def render_template(template: str, context: dict[str, Any]) -> str:
    """Render `template` with the given context dictionary."""
    tokens = _tokenize(template)
    rendered, _ = _eval(tokens, 0, context, set())
    return rendered


# --- Built-in default templates ----------------------------------------

DEFAULT_TEMPLATES: dict[str, str] = {
    'html': (
        '<!DOCTYPE html>\n'
        '<html$if(lang)$ lang="$lang$"$endif$>\n'
        '<head>\n'
        '  <meta charset="utf-8" />\n'
        '$if(title-meta)$  <title>$title-meta$</title>\n$endif$'
        '$for(css)$  <link rel="stylesheet" href="$css$" />\n$endfor$'
        '$for(header-includes)$$header-includes$\n$endfor$'
        '</head>\n'
        '<body>\n'
        '$for(include-before)$$include-before$\n$endfor$'
        '$if(toc)$<nav id="TOC">$toc$</nav>\n$endif$'
        '$body$\n'
        '$for(include-after)$$include-after$\n$endfor$'
        '</body>\n'
        '</html>\n'
    ),
    'latex': (
        '\\documentclass{article}\n'
        '$for(header-includes)$$header-includes$\n$endfor$'
        '$if(title)$\\title{$title$}\n$endif$'
        '$if(author)$\\author{$author$}\n$endif$'
        '$if(date)$\\date{$date$}\n$endif$'
        '\\begin{document}\n'
        '$if(title)$\\maketitle\n$endif$'
        '$for(include-before)$$include-before$\n$endfor$'
        '$if(toc)$\\tableofcontents\n$endif$'
        '$body$\n'
        '$for(include-after)$$include-after$\n$endfor$'
        '\\end{document}\n'
    ),
    'markdown': (
        '$if(title)$% $title$\n$endif$'
        '$if(author)$% $for(author)$$author$$sep$; $endfor$\n$endif$'
        '$if(date)$% $date$\n$endif$'
        '\n$body$\n'
    ),
    'native': '$body$\n',
    'json': '$body$\n',
    'rst': (
        '$if(title)$$title$\n=========\n\n$endif$'
        '$body$\n'
    ),
}


def get_default_template(format_name: str) -> str | None:
    if format_name in DEFAULT_TEMPLATES:
        return DEFAULT_TEMPLATES[format_name]
    if format_name in {'html5', 'html4', 'xhtml'}:
        return DEFAULT_TEMPLATES['html']
    if format_name in {'tex', 'beamer', 'latex'}:
        return DEFAULT_TEMPLATES['latex']
    return None
