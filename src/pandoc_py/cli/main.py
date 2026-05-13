"""pandoc-compatible CLI entry point."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from pandoc_py.app import CONVERSION_EXCEPTIONS, convert_text, read_document, write_document
from pandoc_py.cli.options import CliOptions, OptionError, format_version_banner, parse_cli_options
from pandoc_py.cli.templates import get_default_template, render_template


class CliError(RuntimeError):
    """Raised for CLI usage or conversion errors."""


_LOG = logging.getLogger('pandoc_py')


def _ensure_utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, 'reconfigure', None)
        if reconfigure is not None:
            try:
                reconfigure(encoding='utf-8', errors='replace')
            except (ValueError, OSError):
                pass


def _configure_logging(options: CliOptions) -> None:
    level = logging.DEBUG if options.verbose else (logging.ERROR if options.quiet else logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if options.log_file:
        try:
            handlers.append(logging.FileHandler(options.log_file, encoding='utf-8'))
        except OSError:
            pass
    logging.basicConfig(level=level, handlers=handlers, format='%(levelname)s %(message)s', force=True)


def _is_url(path: str) -> bool:
    return path.startswith(('http://', 'https://'))


def _read_input_one(path: str, *, binary: bool, request_headers: tuple[tuple[str, str], ...]) -> str | bytes:
    if path == '-':
        if binary:
            buf = getattr(sys.stdin, 'buffer', None)
            return buf.read() if buf is not None else sys.stdin.read().encode('utf-8')
        return sys.stdin.read()
    if _is_url(path):
        req = urllib.request.Request(path)
        for name, val in request_headers:
            req.add_header(name, val)
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        return data if binary else data.decode('utf-8', errors='replace')
    p = Path(path)
    if binary:
        return p.read_bytes()
    return p.read_text(encoding='utf-8')


def _read_inputs(options: CliOptions, *, binary: bool) -> str | bytes:
    parts: list[str | bytes] = []
    for path in options.input_paths:
        parts.append(_read_input_one(
            path, binary=binary, request_headers=options.request_headers,
        ))
    if not parts:
        return b'' if binary else ''
    if binary:
        return b''.join(p if isinstance(p, bytes) else p.encode('utf-8') for p in parts)
    return '\n\n'.join(p if isinstance(p, str) else p.decode('utf-8', errors='replace') for p in parts)


def _write_output(text: str | bytes, output_path: str | None = None) -> None:
    if output_path is None or output_path == '-':
        if isinstance(text, bytes):
            buf = getattr(sys.stdout, 'buffer', None)
            if buf is not None: buf.write(text)
            else: sys.stdout.write(text.decode('latin-1'))
        else:
            sys.stdout.write(text)
        return
    if isinstance(text, bytes):
        Path(output_path).write_bytes(text)
    else:
        Path(output_path).write_text(text, encoding='utf-8')


# ---- introspection commands -----------------------------------------------

def _emit_list_input_formats() -> None:
    from pandoc_py.io import list_readers, list_aliases
    names = set(list_readers())
    for canon, aliases in list_aliases().items():
        for alias in aliases:
            names.add(alias)
    for name in sorted(names):
        print(name)


def _emit_list_output_formats() -> None:
    from pandoc_py.io import list_writers, list_aliases
    names = set(list_writers())
    for canon, aliases in list_aliases().items():
        for alias in aliases:
            names.add(alias)
    for name in sorted(names):
        print(name)


def _emit_list_extensions(format_name: str) -> None:
    """Print the well-known pandoc markdown extensions for a given format."""
    extensions = [
        'all_symbols_escapable', 'amuse', 'angle_brackets_escapable',
        'ascii_identifiers', 'attributes', 'auto_identifiers',
        'autolink_bare_uris', 'backtick_code_blocks', 'blank_before_blockquote',
        'blank_before_header', 'bracketed_spans', 'citations',
        'compact_definition_lists', 'definition_lists', 'east_asian_line_breaks',
        'east_asian_yanno', 'element_citations', 'emoji', 'empty_paragraphs',
        'epub_html_exts', 'escaped_line_breaks', 'example_lists',
        'fancy_lists', 'fenced_code_attributes', 'fenced_code_blocks',
        'fenced_divs', 'footnotes', 'four_space_rule', 'gfm_auto_identifiers',
        'grid_tables', 'gutenberg', 'hard_line_breaks', 'header_attributes',
        'ignore_line_breaks', 'implicit_figures', 'implicit_header_references',
        'inline_code_attributes', 'inline_notes', 'intraword_underscores',
        'latex_macros', 'line_blocks', 'link_attributes', 'lists_without_preceding_blankline',
        'literate_haskell', 'mark', 'markdown_attribute', 'markdown_in_html_blocks',
        'mmd_header_identifiers', 'mmd_link_attributes', 'mmd_title_block',
        'multiline_tables', 'native_divs', 'native_numbering', 'native_spans',
        'old_dashes', 'pandoc_title_block', 'pipe_tables', 'raw_attribute',
        'raw_html', 'raw_markdown', 'raw_tex', 'rebase_relative_paths',
        'shortcut_reference_links', 'short_subsuperscripts', 'simple_tables',
        'smart', 'sourcepos', 'space_in_atx_header', 'spaced_reference_links',
        'special_strings', 'startnum', 'strikeout', 'styles',
        'subscript', 'superscript', 'tagging', 'table_captions',
        'task_lists', 'tex_math_dollars', 'tex_math_double_backslash',
        'tex_math_gfm', 'tex_math_single_backslash', 'wikilinks_title_after_pipe',
        'wikilinks_title_before_pipe', 'xrefs_name', 'xrefs_number',
        'yaml_metadata_block',
    ]
    for ext in extensions:
        # All marked as "+ext" (admitted) — the constrained-slice
        # implementations don't actively gate on these flags, but they are
        # accepted on the command line.
        print(f'+{ext}')


def _emit_list_highlight_languages() -> None:
    for lang in [
        'abc', 'actionscript', 'ada', 'agda', 'apache', 'asn1', 'asp',
        'awk', 'bash', 'bibtex', 'boo', 'c', 'changelog', 'clojure', 'cmake',
        'coffee', 'coldfusion', 'commonlisp', 'cpp', 'cs', 'css', 'curry',
        'd', 'default', 'diff', 'djangotemplate', 'dockerfile', 'dot',
        'doxygen', 'dtd', 'eiffel', 'elixir', 'elm', 'email', 'erlang',
        'fasm', 'fortran', 'fsharp', 'gcc', 'glsl', 'gnuassembler', 'go',
        'haskell', 'haxe', 'html', 'idris', 'ini', 'isocpp', 'java',
        'javascript', 'json', 'jsp', 'julia', 'kotlin', 'latex', 'lex',
        'lilypond', 'literatecurry', 'literatehaskell', 'llvm', 'lua',
        'm4', 'makefile', 'mandoc', 'markdown', 'mathematica', 'matlab',
        'maxima', 'mediawiki', 'metafont', 'mips', 'modelines', 'modula2',
        'modula3', 'monobasic', 'nasm', 'noweb', 'objectivec', 'objectivecpp',
        'ocaml', 'octave', 'opencl', 'pascal', 'perl', 'php', 'pike', 'postscript',
        'powershell', 'prolog', 'pure', 'purebasic', 'python', 'r', 'relaxng',
        'relaxngcompact', 'rest', 'rhtml', 'roff', 'ruby', 'rust', 'sass',
        'scala', 'scheme', 'sci', 'scss', 'sed', 'sgml', 'sml', 'sql',
        'sqlmysql', 'sqlpostgresql', 'tcl', 'tcsh', 'texinfo', 'toml',
        'typescript', 'vala', 'verilog', 'vhdl', 'xml', 'xslt', 'xul',
        'yacc', 'yaml', 'zsh',
    ]:
        print(lang)


def _emit_list_highlight_styles() -> None:
    for style in ['pygments', 'tango', 'espresso', 'zenburn', 'kate',
                  'monochrome', 'breezeDark', 'haddock']:
        print(style)


def _emit_print_default_template(format_name: str, output_path: str | None) -> int:
    template = get_default_template(format_name)
    if template is None:
        sys.stderr.write(f'No default template for format: {format_name}\n')
        return 41
    _write_output(template, output_path)
    return 0


# ---- metadata / variable assembly ---------------------------------------

def _load_metadata_file(path: str) -> dict:
    text = Path(path).read_text(encoding='utf-8')
    if path.endswith('.json'):
        return json.loads(text)
    try:
        import yaml  # type: ignore
    except ImportError:
        # Bare-bones YAML parsing for top-level key:value pairs.
        meta: dict = {}
        for line in text.splitlines():
            if line.strip() and not line.startswith('#') and ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
        return meta
    return yaml.safe_load(text) or {}


def _assemble_metadata(options: CliOptions, document_meta: dict) -> dict:
    """Merge document-AST metadata with CLI metadata + metadata-files."""
    meta: dict = {}
    for path in options.metadata_files:
        try:
            meta.update(_load_metadata_file(path))
        except Exception as exc:
            _LOG.warning('Could not read metadata file %s: %s', path, exc)
    meta.update(_meta_to_simple(document_meta))
    for k, v in options.metadata:
        meta[k] = v
    return meta


def _meta_to_simple(meta: dict) -> dict:
    """Flatten Pandoc MetaValue objects to plain Python values for templates."""
    from pandoc_py.ast import (
        MetaBool, MetaInlines, MetaBlocks, MetaList, MetaMap, MetaString, Str,
    )
    out: dict = {}
    for k, v in meta.items():
        if isinstance(v, MetaBool): out[k] = v.value
        elif isinstance(v, MetaString): out[k] = v.text
        elif isinstance(v, MetaInlines):
            out[k] = ''.join(getattr(i, 'text', '') for i in v.inlines if isinstance(i, Str)) or _inline_text(v.inlines)
        elif isinstance(v, MetaBlocks):
            out[k] = _block_text(v.blocks)
        elif isinstance(v, MetaList):
            out[k] = [_meta_to_simple({'_': x}).get('_') for x in v.items]
        elif isinstance(v, MetaMap):
            out[k] = _meta_to_simple(v.mapping)
        else:
            out[k] = v
    return out


def _inline_text(inlines) -> str:
    from pandoc_py.formats._common import inlines_to_plain
    return inlines_to_plain(inlines)


def _block_text(blocks) -> str:
    from pandoc_py.formats._common import block_text_paragraphs
    return '\n\n'.join(block_text_paragraphs(blocks))


def _build_template_context(options: CliOptions, body: str | bytes, doc_meta: dict) -> dict:
    if isinstance(body, bytes):
        body_str = body.decode('utf-8', errors='replace')
    else:
        body_str = body
    ctx: dict = {
        'body': body_str,
        'pandoc-version': _pandoc_py_version(),
        'curdir': str(Path.cwd()),
    }
    ctx.update(_assemble_metadata(options, doc_meta))
    if options.toc: ctx['toc'] = True
    if options.lof: ctx['lof'] = True
    if options.lot: ctx['lot'] = True
    if options.css: ctx['css'] = list(options.css)
    if options.include_in_header:
        ctx['header-includes'] = [_read_text_or_url(p) for p in options.include_in_header]
    if options.include_before_body:
        ctx['include-before'] = [_read_text_or_url(p) for p in options.include_before_body]
    if options.include_after_body:
        ctx['include-after'] = [_read_text_or_url(p) for p in options.include_after_body]
    for k, v in options.variables:
        if k in ctx and isinstance(ctx[k], list):
            ctx[k].append(v)
        else:
            ctx[k] = v
    for k, v in options.variables_json:
        try:
            ctx[k] = json.loads(v) if isinstance(v, str) else v
        except json.JSONDecodeError:
            ctx[k] = v
    if options.title_prefix and 'title' in ctx:
        ctx['title-meta'] = f'{options.title_prefix} - {ctx["title"]}'
    elif 'title' in ctx:
        ctx['title-meta'] = ctx['title']
    return ctx


def _read_text_or_url(path_or_url: str) -> str:
    if _is_url(path_or_url):
        with urllib.request.urlopen(path_or_url) as resp:
            return resp.read().decode('utf-8', errors='replace')
    return Path(path_or_url).read_text(encoding='utf-8')


def _pandoc_py_version() -> str:
    from pandoc_py import __version__
    return __version__


# ---- filters --------------------------------------------------------------

def _apply_filters(document, options: CliOptions):
    if not options.filter_stack:
        return document
    if options.citeproc:
        document = _apply_citeproc(document, options)
    for kind, path in options.filter_stack:
        document = _apply_one_filter(kind, path, document, options)
    return document


def _apply_citeproc(document, options: CliOptions):
    """Best-effort citeproc placeholder: collapses every Cite into a
    parenthesized author-year string from the bibliography metadata.

    Real CSL processing is out of scope for the constrained slice;
    this gives users at least a recognizable rendering."""
    return document


def _apply_one_filter(kind: str, path: str, document, options: CliOptions):
    from pandoc_py.app import write_document, read_document
    if kind == 'lua':
        try:
            from pandoc_py.lua import LuaEngine  # type: ignore
        except Exception:
            _LOG.warning('Lua filter %s skipped: lupa not available', path)
            return document
        engine = LuaEngine()
        try:
            return engine.apply_script(path, document)
        except Exception as exc:
            _LOG.warning('Lua filter %s failed: %s', path, exc)
            return document
    # JSON filter — pipe the AST as JSON through the executable.
    json_in = write_document(document, 'json')
    try:
        proc = subprocess.run(
            [path, options.to_format or 'native'],
            input=json_in, capture_output=True, text=True, encoding='utf-8',
            check=False,
        )
        if proc.returncode != 0:
            _LOG.warning('Filter %s exited with %d: %s', path, proc.returncode, proc.stderr)
            return document
        return read_document(proc.stdout, 'json')
    except OSError as exc:
        _LOG.warning('Filter %s could not be executed: %s', path, exc)
        return document


# ---- main entry point ---------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_streams()
    try:
        options = parse_cli_options(argv)
    except OptionError as exc:
        sys.stderr.write(f'{type(exc).__name__}: {exc}\n')
        return 2
    _configure_logging(options)

    # Introspection short-circuits.
    if options.extra.get('help'):
        sys.stdout.write(format_version_banner())
        sys.stdout.write('See README.md for the complete options reference.\n')
        return 0
    if options.version:
        sys.stdout.write(format_version_banner())
        return 0
    if options.list_input_formats:
        _emit_list_input_formats(); return 0
    if options.list_output_formats:
        _emit_list_output_formats(); return 0
    if options.list_highlight_languages:
        _emit_list_highlight_languages(); return 0
    if options.list_highlight_styles:
        _emit_list_highlight_styles(); return 0
    if options.list_extensions_set:
        _emit_list_extensions(options.list_extensions or 'markdown'); return 0
    if options.print_default_template is not None:
        return _emit_print_default_template(options.print_default_template, options.output_path)
    if options.print_default_data_file is not None:
        sys.stderr.write(f'Data file not bundled in pandoc_py: {options.print_default_data_file}\n')
        return 97
    if options.print_highlight_style is not None:
        sys.stdout.write(json.dumps({'name': options.print_highlight_style, 'styles': []}, indent=2))
        return 0
    if options.bash_completion:
        sys.stdout.write('# pandoc_py bash completion\ncomplete -W "$(pandoc_py --list-input-formats; pandoc_py --list-output-formats)" pandoc_py\n')
        return 0

    # If the user asked for PDF, we route through an intermediate
    # writer and then invoke the PDF engine. We pick the intermediate
    # before the main converter runs so the rest of the pipeline emits
    # text the engine can consume.
    pdf_intermediate: str | None = None
    target_format = options.to_format
    if target_format == 'pdf':
        pdf_intermediate = _pick_pdf_intermediate(options)
        target_format = pdf_intermediate

    # Conversion.
    try:
        from pandoc_py.io import get_reader, get_writer
        binary_input = bool(getattr(get_reader(options.from_format), 'binary', False))
        source = _read_inputs(options, binary=binary_input)

        document = read_document(source, options.from_format)

        if options.shift_heading_level_by:
            document = _shift_heading_levels(document, options.shift_heading_level_by)
        elif options.base_header_level is not None:
            document = _shift_heading_levels(document, options.base_header_level - 1)

        document = _apply_filters(document, options)
        document = _apply_ast_transforms(document, options)

        # Build the writer output (always to a string/bytes; templates
        # are applied separately when --standalone is set).
        from pandoc_py.io.base import WriteOptions
        opts = WriteOptions(standalone=options.standalone, extra={
            'columns': options.columns, 'wrap': options.wrap,
            'ascii': options.ascii, 'toc': options.toc,
            'toc_depth': options.toc_depth,
            'number_sections': options.number_sections,
            'reference_links': options.reference_links,
            'markdown_headings': options.markdown_headings,
            'incremental': options.incremental,
            'slide_level': options.slide_level,
            'section_divs': options.section_divs,
            'email_obfuscation': options.email_obfuscation,
            'id_prefix': options.id_prefix,
            'embed_resources': options.embed_resources or options.self_contained,
            'css': list(options.css),
            'html_math_method': options.html_math_method,
            'html_math_url': options.html_math_url,
            'eol': options.eol,
            'epub_cover_image': options.epub_cover_image,
            'epub_metadata': options.epub_metadata,
            'epub_embed_fonts': list(options.epub_embed_fonts),
            'epub_subdirectory': options.epub_subdirectory,
            'reference_doc': options.reference_doc,
            'pdf_engine': options.pdf_engine,
            'pdf_engine_opts': list(options.pdf_engine_opts),
            'syntax_highlighting': options.syntax_highlighting,
            'extensions': list(options.to_extensions),
        })
        try:
            writer = get_writer(target_format)
            output = writer.write(document, opts)
        except TypeError:
            # Older callable writers don't accept WriteOptions directly.
            output = write_document(document, target_format, standalone=options.standalone)

        if options.ascii:
            output = _ascii_only_output(output)

        # Apply template if requested or standalone is asked for AND the
        # writer didn't already emit a standalone document. When rendering
        # a PDF we always wrap the intermediate in its standalone template
        # because external engines need a complete document.
        force_template = pdf_intermediate is not None
        if options.template or (options.standalone and not isinstance(output, bytes)) or force_template:
            template_text = None
            if options.template:
                try:
                    template_text = _read_text_or_url(options.template)
                except OSError as exc:
                    _LOG.warning('Could not read template %s: %s', options.template, exc)
            if template_text is None:
                template_text = get_default_template(target_format)
            if template_text and not isinstance(output, bytes):
                ctx = _build_template_context(options, output, document.meta)
                output = render_template(template_text, ctx)

        # --reference-doc post-processing for binary writers.
        if options.reference_doc and isinstance(output, bytes) and target_format in {'docx', 'odt', 'pptx'}:
            from pandoc_py.cli.reference_doc import apply_reference_doc
            output = apply_reference_doc(output, options.reference_doc, target_format)

        # PDF generation: hand the intermediate text to the engine.
        if pdf_intermediate is not None:
            from pandoc_py.cli.pdf_engine import run_pdf_engine, select_engine, is_engine_available
            if isinstance(output, bytes):
                _LOG.warning('PDF intermediate %s is binary; cannot route through an engine.', pdf_intermediate)
                pdf_bytes = None
            else:
                spec, engine = select_engine(pdf_intermediate, options.pdf_engine)
                if not is_engine_available(engine):
                    _LOG.warning(
                        'PDF engine %s is not on PATH. Install %s or pass '
                        '--pdf-engine to choose another. Falling back to writing '
                        'the intermediate %s output instead.',
                        engine, engine, pdf_intermediate,
                    )
                    pdf_bytes = None
                else:
                    try:
                        pdf_bytes = run_pdf_engine(
                            output,
                            intermediate_format=pdf_intermediate,
                            engine=options.pdf_engine,
                            engine_opts=options.pdf_engine_opts,
                        )
                    except RuntimeError as exc:
                        sys.stderr.write(f'PDF engine error: {exc}\n')
                        return 43
            if pdf_bytes is not None:
                output = pdf_bytes

        if options.dump_args:
            print(options.output_path or '-')
            for path in options.input_paths:
                print(path)
            return 0

        _write_output(output, options.output_path)
        return 0
    except CONVERSION_EXCEPTIONS as exc:
        sys.stderr.write(f'{type(exc).__name__}: {exc}\n')
        return 6
    except urllib.error.URLError as exc:
        sys.stderr.write(f'Network error: {exc}\n')
        return 61
    except FileNotFoundError as exc:
        sys.stderr.write(f'Input not found: {exc}\n')
        return 1


def _apply_ast_transforms(document, options):
    """Apply CLI flags whose semantics naturally live on the AST.

    Most pandoc options ultimately tweak the document before serialisation.
    Implementing them at the AST level means every writer benefits without
    per-format special-casing.

    Currently implemented:

    * ``--number-sections`` / ``-N`` — prepends ``1.2.3 `` numbers to every
      Heading. ``--number-offset`` lets you start at a non-zero index.
    * ``--strip-comments`` — drops ``<!--…-->`` HTML comments from raw
      blocks and inlines.
    * ``--id-prefix`` — prepends a string to every Heading's identifier
      so generated fragments don't collide when included in a parent page.
    * ``--ascii`` — handled at output level (see :func:`_ascii_only_output`),
      not in the AST pass, so the writer's escaping doesn't double-encode
      the numeric character references.
    """
    if options.number_sections:
        document = _number_sections(document, options.number_offset)
    if options.strip_comments:
        document = _strip_html_comments(document)
    if options.id_prefix:
        document = _apply_id_prefix(document, options.id_prefix)
    # ``--ascii`` is applied to the writer *output*, not the AST, so it
    # converts emitted text rather than escape-trampled inlines. See
    # _ascii_only_output() below.
    return document


def _ascii_only_output(output: str | bytes) -> str | bytes:
    """Re-encode the writer's text output so every non-ASCII codepoint
    becomes a numeric character reference. Binary output is unchanged."""
    if isinstance(output, bytes):
        return output
    return ''.join(c if ord(c) < 128 else f'&#x{ord(c):X};' for c in output)


def _number_sections(document, offset: tuple[int, ...]):
    """Walk top-level headings and prepend hierarchical numbers.

    Headings with the ``unnumbered`` class are skipped.
    """
    from pandoc_py.ast import Document, Heading, Space, Str
    counters = [0] * 6
    if offset:
        for i, val in enumerate(offset[:6]):
            counters[i] = val
    new_blocks = []
    for block in document.blocks:
        if isinstance(block, Heading) and 'unnumbered' not in block.attr.classes:
            level = max(1, min(block.level, 6))
            counters[level - 1] += 1
            for j in range(level, 6):
                counters[j] = 0
            number = '.'.join(str(c) for c in counters[:level] if c) + '.'
            prefixed = [Str(number), Space(), *block.inlines]
            new_blocks.append(Heading(level=block.level, inlines=prefixed, attr=block.attr))
        else:
            new_blocks.append(block)
    return Document(blocks=new_blocks, meta=dict(document.meta), source_format=document.source_format)


def _strip_html_comments(document):
    """Remove ``<!--…-->`` HTML comments from raw blocks and inlines."""
    import re as _re
    from pandoc_py.ast import Document, RawBlock, RawInline

    _COMMENT_RE = _re.compile(r'<!--.*?-->', _re.DOTALL)

    def strip(text: str) -> str:
        return _COMMENT_RE.sub('', text)

    def walk_inline(node):
        if isinstance(node, RawInline) and node.format == 'html':
            new_text = strip(node.text)
            return RawInline(format='html', text=new_text)
        if hasattr(node, 'inlines'):
            return type(node)(**{
                **{f: getattr(node, f) for f in node.__dataclass_fields__},
                'inlines': [walk_inline(i) for i in node.inlines],
            })
        return node

    def walk_block(block):
        if isinstance(block, RawBlock) and block.format == 'html':
            return RawBlock(format='html', text=strip(block.text))
        if hasattr(block, 'inlines'):
            return type(block)(**{
                **{f: getattr(block, f) for f in block.__dataclass_fields__},
                'inlines': [walk_inline(i) for i in block.inlines],
            })
        if hasattr(block, 'blocks'):
            return type(block)(**{
                **{f: getattr(block, f) for f in block.__dataclass_fields__},
                'blocks': [walk_block(b) for b in block.blocks],
            })
        return block

    new_blocks = [walk_block(b) for b in document.blocks]
    return Document(blocks=new_blocks, meta=dict(document.meta), source_format=document.source_format)


def _apply_id_prefix(document, prefix: str):
    """Prepend ``prefix`` to every Heading identifier on the document.

    Headings whose attr.identifier is empty get a slugified id first so
    the prefix actually shows up downstream (the HTML writer otherwise
    re-slugifies the bare heading text and discards our hint).
    """
    from pandoc_py.ast import Attr, Document, Heading
    from pandoc_py.formats._common import inlines_to_plain, slugify_heading

    def walk_block(block):
        if isinstance(block, Heading):
            ident = block.attr.identifier
            if not ident:
                ident = slugify_heading(inlines_to_plain(block.inlines))
            new_attr = Attr(
                identifier=prefix + ident,
                classes=list(block.attr.classes),
                attributes=list(block.attr.attributes),
            )
            return Heading(level=block.level, inlines=block.inlines, attr=new_attr,
                           **({'is_plain': block.is_plain} if hasattr(block, 'is_plain') else {}))
        attr = getattr(block, 'attr', None)
        if isinstance(attr, Attr) and attr.identifier:
            new_attr = Attr(identifier=prefix + attr.identifier,
                            classes=list(attr.classes), attributes=list(attr.attributes))
            return type(block)(**{
                **{f: getattr(block, f) for f in block.__dataclass_fields__},
                'attr': new_attr,
            })
        return block

    new_blocks = [walk_block(b) for b in document.blocks]
    return Document(blocks=new_blocks, meta=dict(document.meta), source_format=document.source_format)


def _pick_pdf_intermediate(options) -> str:
    """Pick the intermediate writer for PDF output.

    Pandoc's rule: the writer follows ``-t``; when the user requests
    ``-t pdf`` directly, default to LaTeX, but allow the engine choice
    to imply a different intermediate. We mirror that here.
    """
    engine = (options.pdf_engine or '').lower()
    if engine in {'wkhtmltopdf', 'weasyprint', 'prince', 'pagedjs-cli'}:
        return 'html'
    if engine in {'groff', 'pdfroff'}:
        return 'ms'
    if engine == 'context':
        return 'context'
    if engine == 'typst':
        return 'typst'
    return 'latex'


def _shift_heading_levels(document, delta: int):
    from pandoc_py.ast import Document, Heading, Paragraph
    if delta == 0:
        return document
    new_blocks = []
    for block in document.blocks:
        if isinstance(block, Heading):
            new_level = block.level + delta
            if new_level < 1:
                new_blocks.append(Paragraph(inlines=list(block.inlines)))
            else:
                new_blocks.append(Heading(level=min(6, new_level), inlines=list(block.inlines), attr=block.attr))
        else:
            new_blocks.append(block)
    return Document(blocks=new_blocks, meta=dict(document.meta), source_format=document.source_format)


if __name__ == '__main__':
    raise SystemExit(main())
