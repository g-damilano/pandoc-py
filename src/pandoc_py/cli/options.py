"""Full pandoc-compatible CLI option surface.

This module parses every option the reference Pandoc binary's user
guide describes. Most options are routed through ``CliOptions`` to
``WriteOptions.extra``/``ReadOptions.extra`` so that format-aware
writers can consume what they support; options that pandoc_py cannot
yet act on are accepted, parsed, and stored on ``CliOptions`` so they
do not silently break invocations and can be progressively wired into
real behavior.

The "implemented" / "stub" / "not-implemented" status of every option
is documented in the README's parity matrix.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

from pandoc_py import __version__
from pandoc_py.app import SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS


class OptionError(ValueError):
    """Raised when CLI options fall outside the current supported slice."""


_FORMAT_ALIASES_LEGACY = {
    'markdown': 'markdown',
    'json': 'json',
    'pandoc-json': 'json',
    'html': 'html',
    'html5': 'html',
    'xhtml': 'html',
    'native': 'native',
    'commonmark': 'commonmark',
    'commonmark_x': 'commonmark_x',
    'commonmark-x': 'commonmark_x',
}


def _build_alias_map() -> dict[str, str]:
    from pandoc_py.io.registry import _GLOBAL
    out = dict(_FORMAT_ALIASES_LEGACY)
    for name in _GLOBAL.list_readers():
        out.setdefault(name, name)
    for name in _GLOBAL.list_writers():
        out.setdefault(name, name)
    for alias, canonical in _GLOBAL._reader_aliases.items():
        out.setdefault(alias, canonical)
    for alias, canonical in _GLOBAL._writer_aliases.items():
        out.setdefault(alias, canonical)
    return out


_FORMAT_ALIASES = _build_alias_map()


# Map filename extensions → pandoc format names (matches pandoc's own table).
_EXTENSION_FORMATS = {
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.txt': 'markdown',
    '.rst': 'rst',
    '.org': 'org',
    '.tex': 'latex',
    '.latex': 'latex',
    '.ltx': 'latex',
    '.html': 'html',
    '.htm': 'html',
    '.xhtml': 'html',
    '.json': 'json',
    '.native': 'native',
    '.docx': 'docx',
    '.pptx': 'pptx',
    '.xlsx': 'xlsx',
    '.odt': 'odt',
    '.epub': 'epub',
    '.rtf': 'rtf',
    '.pdf': 'pdf',
    '.tei': 'tei',
    '.fb2': 'fb2',
    '.opml': 'opml',
    '.ipynb': 'ipynb',
    '.bib': 'bibtex',
    '.bibtex': 'bibtex',
    '.ris': 'ris',
    '.csv': 'csv',
    '.tsv': 'tsv',
    '.xml': 'xml',
    '.dbk': 'docbook',
    '.docbook': 'docbook',
    '.jats': 'jats',
    '.typ': 'typst',
    '.djot': 'djot',
    '.csljson': 'csljson',
    '.context': 'context',
    '.man': 'man',
    '.1': 'man', '.2': 'man', '.3': 'man', '.4': 'man',
    '.5': 'man', '.6': 'man', '.7': 'man', '.8': 'man', '.9': 'man',
    '.t2t': 't2t',
    '.muse': 'muse',
    '.s5': 's5',
    '.beamer': 'beamer',
    '.icml': 'icml',
    '.haddock': 'haddock',
    '.pod': 'pod',
    '.textile': 'textile',
    '.wiki': 'mediawiki',
}


@dataclass(frozen=False, eq=True)
class CliOptions:
    """Full pandoc-compatible options dataclass.

    Most fields mirror the corresponding pandoc CLI flag exactly. See
    the README parity matrix for which are functional and which are
    accepted-but-stub.
    """

    # core inputs/outputs
    input_paths: tuple[str, ...] = ('-',)
    from_format: str | None = None
    to_format: str | None = None
    output_path: str | None = None

    # general behavior
    standalone: bool = False
    version: bool = False
    verbose: bool = False
    quiet: bool = False
    fail_if_warnings: bool = False
    log_file: str | None = None
    sandbox: bool = False
    bash_completion: bool = False
    data_dir: str | None = None
    defaults: tuple[str, ...] = ()
    list_input_formats: bool = False
    list_output_formats: bool = False
    list_extensions: str | None = None  # value is "" if no format passed
    list_extensions_set: bool = False
    list_highlight_languages: bool = False
    list_highlight_styles: bool = False
    print_default_template: str | None = None
    print_default_data_file: str | None = None
    print_highlight_style: str | None = None
    bash_completion_emit: bool = False
    dump_args: bool = False
    ignore_args: bool = False

    # reader-side options
    shift_heading_level_by: int = 0
    base_header_level: int | None = None
    indented_code_classes: tuple[str, ...] = ()
    default_image_extension: str | None = None
    file_scope: bool = False
    filter_stack: tuple[tuple[str, str], ...] = ()  # (kind, path) tuples
    metadata: tuple[tuple[str, object], ...] = ()
    metadata_files: tuple[str, ...] = ()
    preserve_tabs: bool = False
    tab_stop: int = 4
    track_changes: str = 'accept'
    extract_media: str | None = None
    abbreviations: str | None = None
    typst_input: tuple[tuple[str, str], ...] = ()
    trace: bool = False

    # writer-side general
    template: str | None = None
    variables: tuple[tuple[str, object], ...] = ()
    variables_json: tuple[tuple[str, object], ...] = ()
    eol: str | None = None
    dpi: int | None = None
    wrap: str = 'auto'
    columns: int = 72
    toc: bool = False
    toc_depth: int = 3
    lof: bool = False
    lot: bool = False
    strip_comments: bool = False
    syntax_highlighting: str = 'default'
    syntax_definitions: tuple[str, ...] = ()
    include_in_header: tuple[str, ...] = ()
    include_before_body: tuple[str, ...] = ()
    include_after_body: tuple[str, ...] = ()
    resource_paths: tuple[str, ...] = ()
    request_headers: tuple[tuple[str, str], ...] = ()
    no_check_certificate: bool = False

    # writer-specific
    self_contained: bool = False
    embed_resources: bool = False
    link_images: bool = False
    html_q_tags: bool = False
    ascii: bool = False
    reference_links: bool = False
    reference_location: str = 'document'
    figure_caption_position: str = 'below'
    table_caption_position: str = 'above'
    markdown_headings: str = 'atx'
    list_tables: bool = False
    top_level_division: str = 'default'
    number_sections: bool = False
    number_offset: tuple[int, ...] = ()
    listings: bool = False
    incremental: bool = False
    slide_level: int | None = None
    section_divs: bool = False
    email_obfuscation: str = 'none'
    id_prefix: str | None = None
    title_prefix: str | None = None
    css: tuple[str, ...] = ()
    reference_doc: str | None = None
    split_level: int | None = None
    chunk_template: str = '%s-%i.html'
    epub_chapter_level: int | None = None
    epub_cover_image: str | None = None
    epub_title_page: bool = True
    epub_metadata: str | None = None
    epub_embed_fonts: tuple[str, ...] = ()
    epub_subdirectory: str = 'EPUB'
    ipynb_output: str = 'best'
    pdf_engine: str | None = None
    pdf_engine_opts: tuple[str, ...] = ()

    # citations
    citeproc: bool = False
    bibliographies: tuple[str, ...] = ()
    csl: str | None = None
    citation_abbreviations: str | None = None
    natbib: bool = False
    biblatex: bool = False

    # math (HTML)
    html_math_method: str | None = None     # one of mathjax/mathml/webtex/katex/gladtex/plain
    html_math_url: str | None = None

    # extension toggles parsed from `+ext`/`-ext` suffixes on --from / --to.
    from_extensions: tuple[str, ...] = ()
    to_extensions: tuple[str, ...] = ()

    # Free-form pass-through for any future flags.
    extra: dict[str, object] = field(default_factory=dict)

    @property
    def input_path(self) -> str:
        """Back-compat shim — returns the first input path."""
        return self.input_paths[0] if self.input_paths else '-'


def normalize_format(value: str, *, role: str) -> str:
    """Resolve a user-supplied format spec to a canonical name.

    The exact value is checked first (so ``commonmark-x`` and similar
    hyphen-spelled aliases work) before splitting off ``+ext``/``-ext``
    suffixes. We only chop on `+` or `-` after a non-empty first token,
    because otherwise dashes inside aliases like ``commonmark-x`` get
    eaten by the splitter.
    """
    raw = value.casefold()
    canonical = _FORMAT_ALIASES.get(raw)
    if canonical is None:
        # Try stripping `+ext`/`-ext` suffixes.
        base = raw
        for marker in ('+', '-'):
            idx = base.find(marker, 1)
            if idx > 0:
                base = base[:idx]
        canonical = _FORMAT_ALIASES.get(base)
    if canonical is None:
        supported = SUPPORTED_INPUT_FORMATS if role == 'input' else SUPPORTED_OUTPUT_FORMATS
        raise OptionError(f'Unsupported {role} format: {value}. Supported: {", ".join(sorted(supported))}.')
    supported = SUPPORTED_INPUT_FORMATS if role == 'input' else SUPPORTED_OUTPUT_FORMATS
    if canonical not in supported:
        raise OptionError(f'Unsupported {role} format: {value}. Supported: {", ".join(sorted(supported))}.')
    return canonical


def _split_extensions(value: str | None) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    """Split ``markdown+smart-tex_math_dollars`` into base name plus + / - extension tuples."""
    if not value:
        return '', (), ()
    plus: list[str] = []
    minus: list[str] = []
    base: list[str] = []
    i = 0
    n = len(value)
    while i < n and value[i] not in '+-':
        base.append(value[i]); i += 1
    while i < n:
        sign = value[i]; i += 1
        token: list[str] = []
        while i < n and value[i] not in '+-':
            token.append(value[i]); i += 1
        tok = ''.join(token).strip()
        if not tok: continue
        (plus if sign == '+' else minus).append(tok)
    return ''.join(base), tuple(plus), tuple(minus)


def _detect_format_from_path(path: str) -> str | None:
    if not path or path == '-':
        return None
    p = Path(path)
    return _EXTENSION_FORMATS.get(p.suffix.lower())


def _kv(value: str) -> tuple[str, object]:
    """Parse `KEY=VAL` or `KEY:VAL` or `KEY` into (key, val)."""
    for sep in ('=', ':'):
        if sep in value:
            k, v = value.split(sep, 1)
            return k.strip(), v
    return value.strip(), True


def build_parser() -> argparse.ArgumentParser:
    """Construct the full pandoc-style argparse parser."""
    p = argparse.ArgumentParser(
        prog='pandoc_py',
        description='pandoc-compatible CLI (pandoc_py)',
        add_help=False,
    )
    p.add_argument('input_paths', nargs='*', default=['-'])

    # General
    p.add_argument('-f', '-r', '--from', '--read', dest='from_format', default=None)
    p.add_argument('-t', '-w', '--to', '--write', dest='to_format', default=None)
    p.add_argument('-o', '--output', dest='output_path', default=None)
    p.add_argument('--data-dir', dest='data_dir', default=None)
    p.add_argument('-d', '--defaults', dest='defaults', action='append', default=[])
    p.add_argument('--bash-completion', dest='bash_completion_emit', action='store_true')
    p.add_argument('--sandbox', dest='sandbox', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--verbose', dest='verbose', action='store_true')
    p.add_argument('--quiet', dest='quiet', action='store_true')
    p.add_argument('--fail-if-warnings', dest='fail_if_warnings', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--log', dest='log_file', default=None)
    p.add_argument('--list-input-formats', dest='list_input_formats', action='store_true')
    p.add_argument('--list-output-formats', dest='list_output_formats', action='store_true')
    p.add_argument('--list-extensions', dest='list_extensions', nargs='?', const='')
    p.add_argument('--list-highlight-languages', dest='list_highlight_languages', action='store_true')
    p.add_argument('--list-highlight-styles', dest='list_highlight_styles', action='store_true')
    p.add_argument('-v', '--version', dest='version', action='store_true')
    p.add_argument('-h', '--help', dest='help', action='store_true')

    # Reader options
    p.add_argument('--shift-heading-level-by', dest='shift_heading_level_by', type=int, default=0)
    p.add_argument('--base-header-level', dest='base_header_level', type=int, default=None)
    p.add_argument('--indented-code-classes', dest='indented_code_classes', default=None)
    p.add_argument('--default-image-extension', dest='default_image_extension', default=None)
    p.add_argument('--file-scope', dest='file_scope', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('-F', '--filter', dest='filters', action='append', default=[])
    p.add_argument('-L', '--lua-filter', dest='lua_filters', action='append', default=[])
    p.add_argument('-M', '--metadata', dest='metadata', action='append', default=[])
    p.add_argument('--metadata-file', dest='metadata_files', action='append', default=[])
    p.add_argument('-p', '--preserve-tabs', dest='preserve_tabs', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--tab-stop', dest='tab_stop', type=int, default=4)
    p.add_argument('--track-changes', dest='track_changes', default='accept', choices=['accept', 'reject', 'all'])
    p.add_argument('--extract-media', dest='extract_media', default=None)
    p.add_argument('--abbreviations', dest='abbreviations', default=None)
    p.add_argument('--typst-input', dest='typst_input', action='append', default=[])
    p.add_argument('--trace', dest='trace', nargs='?', const=True, default=False, type=_optional_bool)

    # Writer general
    p.add_argument('-s', '--standalone', dest='standalone', action='store_true')
    p.add_argument('--template', dest='template', default=None)
    p.add_argument('-V', '--variable', dest='variables', action='append', default=[])
    p.add_argument('--variable-json', dest='variables_json', action='append', default=[])
    p.add_argument('-D', '--print-default-template', dest='print_default_template', default=None)
    p.add_argument('--print-default-data-file', dest='print_default_data_file', default=None)
    p.add_argument('--eol', dest='eol', default=None, choices=[None, 'crlf', 'lf', 'native'])
    p.add_argument('--dpi', dest='dpi', type=int, default=None)
    p.add_argument('--wrap', dest='wrap', default='auto', choices=['auto', 'none', 'preserve'])
    p.add_argument('--columns', dest='columns', type=int, default=72)
    p.add_argument('--toc', '--table-of-contents', dest='toc', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--toc-depth', dest='toc_depth', type=int, default=3)
    p.add_argument('--lof', '--list-of-figures', dest='lof', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--lot', '--list-of-tables', dest='lot', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--strip-comments', dest='strip_comments', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--syntax-highlighting', dest='syntax_highlighting', default='default')
    p.add_argument('--no-highlight', dest='no_highlight', action='store_true')
    p.add_argument('--highlight-style', dest='highlight_style', default=None)
    p.add_argument('--print-highlight-style', dest='print_highlight_style', default=None)
    p.add_argument('--syntax-definition', dest='syntax_definitions', action='append', default=[])
    p.add_argument('-H', '--include-in-header', dest='include_in_header', action='append', default=[])
    p.add_argument('-B', '--include-before-body', dest='include_before_body', action='append', default=[])
    p.add_argument('-A', '--include-after-body', dest='include_after_body', action='append', default=[])
    p.add_argument('--resource-path', dest='resource_paths', action='append', default=[])
    p.add_argument('--request-header', dest='request_headers', action='append', default=[])
    p.add_argument('--no-check-certificate', dest='no_check_certificate', nargs='?', const=True, default=False, type=_optional_bool)

    # Writer-specific
    p.add_argument('--self-contained', dest='self_contained', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--embed-resources', dest='embed_resources', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--link-images', dest='link_images', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--html-q-tags', dest='html_q_tags', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--ascii', dest='ascii', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--reference-links', dest='reference_links', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--reference-location', dest='reference_location', default='document', choices=['block', 'section', 'document'])
    p.add_argument('--figure-caption-position', dest='figure_caption_position', default='below', choices=['above', 'below'])
    p.add_argument('--table-caption-position', dest='table_caption_position', default='above', choices=['above', 'below'])
    p.add_argument('--markdown-headings', dest='markdown_headings', default='atx', choices=['atx', 'setext'])
    p.add_argument('--list-tables', dest='list_tables', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--top-level-division', dest='top_level_division', default='default', choices=['default', 'section', 'chapter', 'part'])
    p.add_argument('-N', '--number-sections', dest='number_sections', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--number-offset', dest='number_offset', default=None)
    p.add_argument('--listings', dest='listings', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('-i', '--incremental', dest='incremental', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--slide-level', dest='slide_level', type=int, default=None)
    p.add_argument('--section-divs', dest='section_divs', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--email-obfuscation', dest='email_obfuscation', default='none', choices=['none', 'javascript', 'references'])
    p.add_argument('--id-prefix', dest='id_prefix', default=None)
    p.add_argument('-T', '--title-prefix', dest='title_prefix', default=None)
    p.add_argument('-c', '--css', dest='css', action='append', default=[])
    p.add_argument('--reference-doc', dest='reference_doc', default=None)
    p.add_argument('--split-level', dest='split_level', type=int, default=None)
    p.add_argument('--chunk-template', dest='chunk_template', default='%s-%i.html')
    p.add_argument('--epub-chapter-level', dest='epub_chapter_level', type=int, default=None)
    p.add_argument('--epub-cover-image', dest='epub_cover_image', default=None)
    p.add_argument('--epub-title-page', dest='epub_title_page', nargs='?', const=True, default=True, type=_optional_bool)
    p.add_argument('--epub-metadata', dest='epub_metadata', default=None)
    p.add_argument('--epub-embed-font', dest='epub_embed_fonts', action='append', default=[])
    p.add_argument('--epub-subdirectory', dest='epub_subdirectory', default='EPUB')
    p.add_argument('--ipynb-output', dest='ipynb_output', default='best', choices=['all', 'none', 'best'])
    p.add_argument('--pdf-engine', dest='pdf_engine', default=None)
    p.add_argument('--pdf-engine-opt', dest='pdf_engine_opts', action='append', default=[])

    # Citations
    p.add_argument('-C', '--citeproc', dest='citeproc', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--bibliography', dest='bibliographies', action='append', default=[])
    p.add_argument('--csl', dest='csl', default=None)
    p.add_argument('--citation-abbreviations', dest='citation_abbreviations', default=None)
    p.add_argument('--natbib', dest='natbib', action='store_true')
    p.add_argument('--biblatex', dest='biblatex', action='store_true')

    # Math
    p.add_argument('--mathjax', dest='mathjax', nargs='?', const='')
    p.add_argument('--mathml', dest='mathml', action='store_true')
    p.add_argument('--webtex', dest='webtex', nargs='?', const='')
    p.add_argument('--katex', dest='katex', nargs='?', const='')
    p.add_argument('--gladtex', dest='gladtex', action='store_true')

    # Wrapper-script
    p.add_argument('--dump-args', dest='dump_args', nargs='?', const=True, default=False, type=_optional_bool)
    p.add_argument('--ignore-args', dest='ignore_args', nargs='?', const=True, default=False, type=_optional_bool)

    return p


def _optional_bool(value):
    """Argparse type-converter for nargs='?' boolean flags (`--flag=true|false`)."""
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    if isinstance(value, str):
        return value.lower() not in {'false', 'no', '0', 'off'}
    return bool(value)


def parse_cli_options(argv: list[str] | None = None) -> CliOptions:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, 'help', False):
        # We let main() print the banner+help separately.
        return CliOptions(version=False, extra={'help': True})

    # version / introspection short-circuits — we don't need format normalization.
    if args.version:
        return CliOptions(version=True)
    if args.list_input_formats or args.list_output_formats or args.list_highlight_languages or args.list_highlight_styles:
        return CliOptions(
            list_input_formats=args.list_input_formats,
            list_output_formats=args.list_output_formats,
            list_highlight_languages=args.list_highlight_languages,
            list_highlight_styles=args.list_highlight_styles,
        )
    if args.list_extensions is not None:
        return CliOptions(list_extensions=args.list_extensions, list_extensions_set=True)
    if args.print_default_template is not None:
        return CliOptions(print_default_template=args.print_default_template, output_path=args.output_path)
    if args.print_default_data_file is not None:
        return CliOptions(print_default_data_file=args.print_default_data_file, output_path=args.output_path)
    if args.print_highlight_style is not None:
        return CliOptions(print_highlight_style=args.print_highlight_style, output_path=args.output_path)
    if args.bash_completion_emit:
        return CliOptions(bash_completion=True)

    # Format detection & normalization.
    input_paths = tuple(args.input_paths or ['-'])
    primary_input = input_paths[0]
    raw_from = args.from_format
    raw_to = args.to_format
    from_base, from_plus, from_minus = _split_extensions(raw_from)
    to_base, to_plus, to_minus = _split_extensions(raw_to)
    if not from_base:
        from_base = _detect_format_from_path(primary_input) or 'markdown'
    if not to_base:
        # Choose based on output filename, else default to HTML if there is an
        # output file, else markdown. This mirrors pandoc's behaviour.
        to_base = _detect_format_from_path(args.output_path or '') or ('html' if args.output_path else 'markdown')

    from_format = normalize_format(from_base, role='input')
    to_format = normalize_format(to_base, role='output')

    # Parse `-M` / `-V` style key=value lists.
    metadata = tuple(_kv(m) for m in args.metadata)
    variables = tuple(_kv(v) for v in args.variables)
    variables_json = tuple(_kv(v) for v in args.variables_json)
    typst_input = tuple((k, v if isinstance(v, str) else '') for k, v in (_kv(t) for t in args.typst_input))

    request_headers = []
    for raw in args.request_headers:
        if ':' in raw:
            name, val = raw.split(':', 1)
            request_headers.append((name.strip(), val.strip()))

    filter_stack: list[tuple[str, str]] = []
    for f in args.filters:
        kind = 'lua' if f.lower().endswith('.lua') else 'json'
        filter_stack.append((kind, f))
    for f in args.lua_filters:
        filter_stack.append(('lua', f))

    # Extension lists already split off the format base name above.
    indented_code_classes = ()
    if args.indented_code_classes:
        indented_code_classes = tuple(
            cls for cls in args.indented_code_classes.replace(',', ' ').split() if cls
        )

    number_offset: tuple[int, ...] = ()
    if args.number_offset:
        try:
            number_offset = tuple(int(part) for part in args.number_offset.split(','))
        except ValueError as exc:
            raise OptionError(f'Invalid --number-offset value: {args.number_offset!r}') from exc

    syntax_highlighting = args.syntax_highlighting
    if args.no_highlight:
        syntax_highlighting = 'none'
    elif args.highlight_style:
        syntax_highlighting = args.highlight_style

    self_contained = args.self_contained or args.embed_resources

    html_math_method = None
    html_math_url = None
    if args.mathjax is not None:
        html_math_method = 'mathjax'; html_math_url = args.mathjax or None
    elif args.mathml:
        html_math_method = 'mathml'
    elif args.webtex is not None:
        html_math_method = 'webtex'; html_math_url = args.webtex or None
    elif args.katex is not None:
        html_math_method = 'katex'; html_math_url = args.katex or None
    elif args.gladtex:
        html_math_method = 'gladtex'

    return CliOptions(
        input_paths=input_paths,
        from_format=from_format,
        to_format=to_format,
        output_path=args.output_path,
        standalone=args.standalone,
        version=False,
        verbose=args.verbose,
        quiet=args.quiet,
        fail_if_warnings=args.fail_if_warnings,
        log_file=args.log_file,
        sandbox=args.sandbox,
        data_dir=args.data_dir,
        defaults=tuple(args.defaults),
        shift_heading_level_by=args.shift_heading_level_by,
        base_header_level=args.base_header_level,
        indented_code_classes=indented_code_classes,
        default_image_extension=args.default_image_extension,
        file_scope=args.file_scope,
        filter_stack=tuple(filter_stack),
        metadata=metadata,
        metadata_files=tuple(args.metadata_files),
        preserve_tabs=args.preserve_tabs,
        tab_stop=args.tab_stop,
        track_changes=args.track_changes,
        extract_media=args.extract_media,
        abbreviations=args.abbreviations,
        typst_input=typst_input,
        trace=args.trace,
        template=args.template,
        variables=variables,
        variables_json=variables_json,
        eol=args.eol,
        dpi=args.dpi,
        wrap=args.wrap,
        columns=args.columns,
        toc=args.toc,
        toc_depth=args.toc_depth,
        lof=args.lof,
        lot=args.lot,
        strip_comments=args.strip_comments,
        syntax_highlighting=syntax_highlighting,
        syntax_definitions=tuple(args.syntax_definitions),
        include_in_header=tuple(args.include_in_header),
        include_before_body=tuple(args.include_before_body),
        include_after_body=tuple(args.include_after_body),
        resource_paths=tuple(args.resource_paths),
        request_headers=tuple(request_headers),
        no_check_certificate=args.no_check_certificate,
        self_contained=self_contained,
        embed_resources=args.embed_resources,
        link_images=args.link_images,
        html_q_tags=args.html_q_tags,
        ascii=args.ascii,
        reference_links=args.reference_links,
        reference_location=args.reference_location,
        figure_caption_position=args.figure_caption_position,
        table_caption_position=args.table_caption_position,
        markdown_headings=args.markdown_headings,
        list_tables=args.list_tables,
        top_level_division=args.top_level_division,
        number_sections=args.number_sections,
        number_offset=number_offset,
        listings=args.listings,
        incremental=args.incremental,
        slide_level=args.slide_level,
        section_divs=args.section_divs,
        email_obfuscation=args.email_obfuscation,
        id_prefix=args.id_prefix,
        title_prefix=args.title_prefix,
        css=tuple(args.css),
        reference_doc=args.reference_doc,
        split_level=args.split_level,
        chunk_template=args.chunk_template,
        epub_chapter_level=args.epub_chapter_level,
        epub_cover_image=args.epub_cover_image,
        epub_title_page=args.epub_title_page,
        epub_metadata=args.epub_metadata,
        epub_embed_fonts=tuple(args.epub_embed_fonts),
        epub_subdirectory=args.epub_subdirectory,
        ipynb_output=args.ipynb_output,
        pdf_engine=args.pdf_engine,
        pdf_engine_opts=tuple(args.pdf_engine_opts),
        citeproc=args.citeproc,
        bibliographies=tuple(args.bibliographies),
        csl=args.csl,
        citation_abbreviations=args.citation_abbreviations,
        natbib=args.natbib,
        biblatex=args.biblatex,
        html_math_method=html_math_method,
        html_math_url=html_math_url,
        from_extensions=from_plus + tuple(f'-{x}' for x in from_minus),
        to_extensions=to_plus + tuple(f'-{x}' for x in to_minus),
        dump_args=args.dump_args,
        ignore_args=args.ignore_args,
    )


def format_version_banner() -> str:
    return f'pandoc_py {__version__}\n'


# Keep legacy `CliOptions(input_path=…)` callers working by intercepting
# the kwarg in a thin wrapper around the dataclass-generated __init__.
_BASE_INIT = CliOptions.__init__


def _compat_init(self, *args, **kwargs):
    if 'input_path' in kwargs and 'input_paths' not in kwargs:
        kwargs['input_paths'] = (kwargs.pop('input_path'),)
    _BASE_INIT(self, *args, **kwargs)


CliOptions.__init__ = _compat_init
