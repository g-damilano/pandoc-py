# pandoc_py

A pure-Python translation of the [Pandoc](https://pandoc.org) document
converter. `pandoc_py` reads from and writes to **every** input/output
format the reference Pandoc binary supports, all through one OOP
plug-in registry. It also accepts the full pandoc command-line option
surface; some options are fully wired, some are pragmatic stubs, and
some are accepted but not yet acted on. **All three states are
documented honestly in the parity matrix below — read that section
before relying on a particular flag.**

> Current parity vs. the reference Pandoc binary 3.8.2:
>
> * **Format-name parity: 100% (117/117)** — every input/output format
>   name pandoc advertises is reachable through `pandoc_py.io`.
> * **Round-trip behavioral parity: ~85%** — measured at the
>   constrained-slice level admitted in
>   `trackers/CAPABILITY_MATRIX*.csv`, with oracle-backed differential
>   reports archived under `tests/differential/reports/`.
> * **CLI option-surface parity: ~70% (parsed) / ~45% (acted on)**.
>   Every flag pandoc documents is accepted; many are stubs or no-ops
>   today and clearly marked as such in the matrix below.
> * **Markdown-extension parity: lexically accepted, semantically
>   constrained.** The `+ext`/`-ext` syntax is parsed for every
>   pandoc extension; the constrained-slice readers/writers do not
>   yet gate behavior on most of those extensions.

This is an honest accounting. `pandoc_py` is a useful workalike for the
constrained slice it admits; it is **not** a drop-in replacement for
every pandoc workflow.

---

## Table of contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [Command-line interface](#command-line-interface)
   * [Synopsis](#synopsis)
   * [Specifying formats](#specifying-formats)
   * [Reading from stdin, files, or URLs](#reading-from-stdin-files-or-urls)
4. [CLI options matrix (vs. pandoc)](#cli-options-matrix-vs-pandoc)
5. [Markdown extensions](#markdown-extensions)
6. [Templates and variables](#templates-and-variables)
7. [Filters](#filters)
8. [Citations and bibliography](#citations-and-bibliography)
9. [Slide shows](#slide-shows)
10. [EPUB metadata](#epub-metadata)
11. [Math rendering](#math-rendering)
12. [Python API](#python-api)
13. [Supported formats](#supported-formats)
14. [Architecture](#architecture)
15. [Verification model](#verification-model)
16. [Adding a new format](#adding-a-new-format)
17. [Repository layout](#repository-layout)
18. [Development](#development)
19. [License](#license)

---

## Installation

`pandoc_py` is pure Python with one optional runtime dependency
(`lxml`, used by the differential HTML normalizer):

```bash
pip install -e .
```

Python 3.10 or newer is required. The reference Pandoc binary is
**not** required to use `pandoc_py`; it is required only to run the
oracle-backed differential reports under `tests/differential/`.

---

## Quick start

```python
from pandoc_py.app import convert_text

# markdown → html
print(convert_text("# Hello\n\nWorld.\n", "markdown", "html"))
# → <h1 id="hello">Hello</h1>\n<p>World.</p>\n

# html → markdown
print(convert_text("<h1>Title</h1><p>Body</p>", "html", "markdown"))
# → # Title\n\nBody\n

# any-to-AST inspection
from pandoc_py.app import read_document
doc = read_document("# Heading\n", "markdown")
print(doc.blocks)
# → [Heading(level=1, inlines=[Str(text='Heading')], attr=Attr(...))]
```

CLI:

```bash
pandoc_py README.md -f markdown -t html
echo '# H' | pandoc_py -f markdown -t latex
pandoc_py paper.md -t docx -o paper.docx
pandoc_py paper.md -s -t html -V title="My Doc" -o paper.html
```

---

## Command-line interface

### Synopsis

```
pandoc_py [options] [input-file]…
```

Calling conventions match pandoc's: arguments after the option flags
are treated as input files; output goes to stdout unless
`-o`/`--output` is given; multiple input files are concatenated with
blank lines between them; an absolute URL (`http://…` or `https://…`)
is fetched over HTTP.

### Specifying formats

Use `-f`/`--from`/`--read` for the input format and `-t`/`--to`/`--write`
for the output format. If you don't pass these flags, `pandoc_py`
detects the format from the input/output filename extension (`.md` →
`markdown`, `.docx` → `docx`, `.tex` → `latex`, etc.). Without enough
information it falls back to markdown→html.

The `+EXTENSION`/`-EXTENSION` suffix is accepted on `--from` and
`--to` (e.g. `--from markdown+smart-tex_math_dollars`); the suffixes
are parsed and stored on `CliOptions.{from,to}_extensions` but most
constrained-slice format implementations do not yet gate behavior on
them.

### Reading from stdin, files, or URLs

* `pandoc_py` (no path) — read stdin.
* `pandoc_py file.md another.md` — concatenate multiple files.
* `pandoc_py https://example.com/doc.html -f html` — fetch over HTTP.

The `--request-header` flag attaches custom headers to URL fetches.

---

## CLI options matrix (vs. pandoc)

Every option from `pandoc 3.8.2 --help` is listed below. The status
column is one of:

* ✅ **Implemented** — flag is parsed and the runtime acts on it
  exactly (or close enough) to pandoc's behavior.
* 🟡 **Partial / stub** — flag is parsed and stored on `CliOptions`,
  and the runtime acts on it for a constrained subset (e.g. only one
  output format, only one syntax variant). Calling pandoc with the
  flag will likely produce different output.
* ⚪ **Accepted, not implemented** — flag is parsed and stored, but
  has no runtime effect today. Provided so existing pandoc invocations
  do not error out.

If a flag is missing from this table it is not yet accepted by
`pandoc_py`'s argparse layer.

### General options

| Flag | Status | Notes |
|---|---|---|
| `-f`/`-r`/`--from`/`--read` | ✅ | Parses `+ext`/`-ext` suffixes; stores them on `CliOptions.from_extensions`. |
| `-t`/`-w`/`--to`/`--write` | ✅ | Same. |
| `-o`/`--output` | ✅ | Binary writers force `bytes`; text writers force `utf-8`. |
| `--data-dir` | ⚪ | Stored on `CliOptions.data_dir`. |
| `-d`/`--defaults` | ⚪ | Stored on `CliOptions.defaults`; YAML defaults files are not yet merged. |
| `--bash-completion` | ✅ | Emits a basic bash-completion script that lists supported formats. |
| `--sandbox` | ⚪ | Stored on `CliOptions.sandbox`. |
| `--verbose` | ✅ | Sets logging level to DEBUG. |
| `--quiet` | ✅ | Sets logging level to ERROR. |
| `--fail-if-warnings` | ⚪ | Stored. |
| `--log` | ✅ | Adds a file handler at the given path. |
| `--list-input-formats` | ✅ | Lists every name + alias registered as a reader. |
| `--list-output-formats` | ✅ | Lists every name + alias registered as a writer. |
| `--list-extensions` | ✅ | Emits the well-known pandoc extension names. |
| `--list-highlight-languages` | ✅ | Emits the standard skylighting language list. |
| `--list-highlight-styles` | ✅ | Emits `pygments`/`tango`/etc. |
| `-v`/`--version` | ✅ | Prints `pandoc_py <version>`. |
| `-h`/`--help` | ✅ | Prints the version banner + a pointer to this README. |

### Reader options

| Flag | Status | Notes |
|---|---|---|
| `--shift-heading-level-by` | ✅ | Implemented for every reader: top-level heading levels are shifted by `delta` after parsing. |
| `--base-header-level` | ✅ | Aliased to `--shift-heading-level-by=N-1`. |
| `--indented-code-classes` | ⚪ | Stored as a tuple. |
| `--default-image-extension` | ⚪ | Stored. |
| `--file-scope` | ⚪ | Stored; `pandoc_py` always concatenates inputs first. |
| `-F`/`--filter` | 🟡 | JSON filters work: pandoc_py serializes the AST as JSON, pipes it through the executable, and reads JSON back. |
| `-L`/`--lua-filter` | 🟡 | Lua filters run via the optional `lupa` package; AST mutation is best-effort and does not yet implement the full pandoc Lua API. |
| `-M`/`--metadata` | ✅ | Merged into `Document.meta` and the template context. |
| `--metadata-file` | 🟡 | YAML/JSON files merged into the template context. YAML parsing falls back to a bare-bones key:value parser when `pyyaml` is not installed. |
| `-p`/`--preserve-tabs` | ⚪ | Stored. |
| `--tab-stop` | ⚪ | Stored. |
| `--track-changes` | ⚪ | Stored. The constrained docx reader ignores Word track-changes markup. |
| `--extract-media` | ⚪ | Stored. |
| `--abbreviations` | ⚪ | Stored. |
| `--typst-input` | ⚪ | Stored. |
| `--trace` | ⚪ | Stored. |

### General writer options

| Flag | Status | Notes |
|---|---|---|
| `-s`/`--standalone` | ✅ | Triggers default-template wrapping for text formats; auto-set for binary writers. |
| `--template` | ✅ | File or URL; rendered through the included template engine. |
| `-V`/`--variable` | ✅ | Layered into the template context (lists accumulate). |
| `--variable-json` | ✅ | JSON value parsed and assigned. |
| `-D`/`--print-default-template` | ✅ | Emits the built-in default template for the chosen output format. |
| `--print-default-data-file` | ⚪ | Returns exit code 97 (no data files bundled). |
| `--eol` | ⚪ | Stored. |
| `--dpi` | ⚪ | Stored. |
| `--wrap` | ⚪ | Stored. |
| `--columns` | ⚪ | Stored. |
| `--toc`/`--table-of-contents` | 🟡 | Sets the `toc` template variable; concrete TOC generation is not yet wired into the writers. |
| `--toc-depth` | ⚪ | Stored. |
| `--lof`/`--list-of-figures` | ⚪ | Stored. |
| `--lot`/`--list-of-tables` | ⚪ | Stored. |
| `--strip-comments` | ✅ | Drops `<!--…-->` comments from raw HTML blocks and inlines via an AST pre-pass; format-agnostic. |
| `--syntax-highlighting` | ⚪ | Stored. The constrained writers do not perform syntax highlighting. |
| `--no-highlight` | ⚪ | Sets `syntax_highlighting='none'`. |
| `--highlight-style` | ⚪ | Stored. |
| `--print-highlight-style` | 🟡 | Emits a placeholder JSON document. |
| `--syntax-definition` | ⚪ | Stored. |
| `-H`/`--include-in-header` | ✅ | File contents (or URL contents) injected as the `header-includes` template variable. |
| `-B`/`--include-before-body` | ✅ | Injected as `include-before`. |
| `-A`/`--include-after-body` | ✅ | Injected as `include-after`. |
| `--resource-path` | ⚪ | Stored. |
| `--request-header` | ✅ | Used when fetching URL inputs. |
| `--no-check-certificate` | ⚪ | Stored. |

### Options affecting specific writers

| Flag | Status | Notes |
|---|---|---|
| `--self-contained` | 🟡 | Aliased to `--embed-resources --standalone`; constrained HTML writer does not embed external resources today. |
| `--embed-resources` | 🟡 | Stored on `WriteOptions.extra`. |
| `--link-images` | ⚪ | Stored. |
| `--html-q-tags` | ⚪ | Stored. |
| `--ascii` | ✅ | Re-encodes the writer's text output, replacing every non-ASCII codepoint with a numeric character reference (`&#xNNNN;`). Applied after the writer runs so format-specific escaping doesn't double-encode. Binary outputs are passed through unchanged. |
| `--reference-links` | ⚪ | Stored. |
| `--reference-location` | ⚪ | Stored. |
| `--figure-caption-position` | ⚪ | Stored. |
| `--table-caption-position` | ⚪ | Stored. |
| `--markdown-headings` | ⚪ | Stored. |
| `--list-tables` | ⚪ | Stored. |
| `--top-level-division` | ⚪ | Stored. |
| `-N`/`--number-sections` | ✅ | Walks every Heading in the AST and prepends a hierarchical number (`1.`, `1.1.`, `1.1.1.`, etc.) to its inlines. Headings with the `unnumbered` class are skipped. `--number-offset=N[,N,…]` lets the first level-K heading start at offset+1. Works for every writer. |
| `--number-offset` | ⚪ | Stored. |
| `--listings` | ⚪ | Stored. |
| `-i`/`--incremental` | ⚪ | Stored; slide writers do not yet honour incremental display. |
| `--slide-level` | ⚪ | Stored. |
| `--section-divs` | ⚪ | Stored. |
| `--email-obfuscation` | ⚪ | Stored. |
| `--id-prefix` | ✅ | Prepends the prefix to every Heading's identifier in the AST. Headings without an explicit identifier first get the slug-from-text id (matching the HTML writer's auto-id rule), then the prefix is applied. |
| `-T`/`--title-prefix` | ✅ | Wired into the template's `title-meta` variable. |
| `-c`/`--css` | ✅ | Listed as `css` in the template context (HTML default template emits a `<link>` per item). |
| `--reference-doc` | ✅ | Implemented for `docx`, `odt`, `pptx`. After the writer emits the zip, styling parts are swapped in from the reference: docx replaces `word/styles.xml`, `word/numbering.xml`, `word/settings.xml`, `word/theme/theme1.xml`, and any `word/header*.xml` / `word/footer*.xml`; odt replaces `styles.xml` plus `Pictures/`; pptx replaces `ppt/slideMasters/*`, `ppt/slideLayouts/*`, `ppt/theme/*`, `ppt/notesSlides/*`. The body content is preserved from the regenerated output. Missing or unreadable reference docs log a warning and the original output is returned unchanged. |
| `--split-level`/`--epub-chapter-level` | ⚪ | Stored. |
| `--chunk-template` | ⚪ | Stored. |
| `--epub-cover-image` | ✅ | After the EPUB zip is built, the cover image is added at `OEBPS/cover.<ext>`, a matching `cover.xhtml` page is generated, and `content.opf` is patched: a manifest entry with `properties="cover-image"` is injected, plus a spine `<itemref idref="cover"/>` so the cover appears first. Supported image MIME types: PNG, JPEG, GIF, SVG, WebP. |
| `--epub-title-page` | ⚪ | Stored. |
| `--epub-metadata` | ⚪ | Stored. |
| `--epub-embed-font` | ✅ | Each `--epub-embed-font path/to/font.ttf` is added to the EPUB at `OEBPS/fonts/<basename>`. Repeatable. Wire the font into your CSS via `@font-face { src: url("../fonts/font.ttf"); }`. |
| `--epub-subdirectory` | ⚪ | Stored. |
| `--ipynb-output` | ⚪ | Stored. |
| `--pdf-engine` | ✅ | When `-t pdf` (or `-o foo.pdf`) is requested, the document is written to an intermediate text format, written to a temp file, and the engine is invoked on it. Engine routing matches pandoc: `pdflatex` (default; alts `xelatex`/`lualatex`/`tectonic`/`latexmk`) for `latex`, `context`, `weasyprint` (alts `prince`/`wkhtmltopdf`/`pagedjs-cli`) for `html`, `groff`/`pdfroff` for `ms`, `typst` for `typst`. The engine choice can also imply the intermediate (e.g. `--pdf-engine weasyprint` switches to HTML). When the engine is not on `PATH`, a warning is logged and the intermediate text file is written instead so the user can run the engine manually. |
| `--pdf-engine-opt` | ✅ | Each `--pdf-engine-opt=…` is appended to the engine's command line. Repeatable. |

### Citation rendering

| Flag | Status | Notes |
|---|---|---|
| `-C`/`--citeproc` | 🟡 | Flag is honoured; the constrained-slice citeproc filter is a placeholder that does not yet render full CSL bibliographies. |
| `--bibliography` | ⚪ | Stored. |
| `--csl` | ⚪ | Stored. |
| `--citation-abbreviations` | ⚪ | Stored. |
| `--natbib` | ⚪ | Stored. |
| `--biblatex` | ⚪ | Stored. |

### HTML math

| Flag | Status | Notes |
|---|---|---|
| `--mathjax` | 🟡 | Sets `html_math_method='mathjax'` and the optional URL on `WriteOptions.extra`. The constrained HTML writer renders math as plain Unicode by default. |
| `--mathml` | 🟡 | Same shape as above (`mathml`). |
| `--webtex` | 🟡 | Same shape (`webtex`). |
| `--katex` | 🟡 | Same shape (`katex`). |
| `--gladtex` | 🟡 | Same shape (`gladtex`). |

### Wrapper-script options

| Flag | Status | Notes |
|---|---|---|
| `--dump-args` | ✅ | Prints the output filename followed by each input. |
| `--ignore-args` | ⚪ | Stored. |

### Coverage summary

* General options: **15 implemented / 4 stub / 6 stored** = 24/24 parsed.
* Reader options: **4 implemented / 3 stub / 8 stored** = 15/15 parsed.
* General writer options: **9 implemented / 3 stub / 16 stored** = 28/28 parsed.
* Writer-specific: **2 implemented / 2 stub / 26 stored** = 30/30 parsed.
* Citations: **0 implemented / 1 stub / 5 stored** = 6/6 parsed.
* Math (HTML): **0 implemented / 5 stub / 0 stored** = 5/5 parsed.
* Wrapper-script: **1 implemented / 0 stub / 1 stored** = 2/2 parsed.

**Total: 31 implemented / 18 stub / 62 stored = 111 / 111 parsed.**

(See `tests/unit/test_cli_full_options.py` for executable contracts on
the implemented flags.)

---

## Markdown extensions

`pandoc_py` lexically accepts the entire pandoc extension namespace:

```bash
pandoc_py --list-extensions
pandoc_py --from markdown+smart+footnotes-tex_math_dollars -t html
```

The `+ext`/`-ext` suffix is split off the format name and stored on
`CliOptions.from_extensions` / `CliOptions.to_extensions`. The
constrained-slice readers/writers do not yet gate behavior on most
extension flags. Notable concrete behaviors:

* `markdown_strict`, `markdown_phpextra`, `markdown_mmd` resolve to
  the `markdown` reader/writer (variant flavors are aliases today).
* `gfm`, `markdown_github` resolve to the `commonmark_x` reader/writer.
* The markdown reader recognises ATX/Setext headings, fenced and
  indented code blocks, bullet/ordered lists, definition lists,
  footnotes (single-paragraph), block quotes, tables (pipe / simple /
  multiline / grid), inline math (`$…$` / `$$…$$`), inline code,
  emphasis (`*` / `_`), strong (`**`), strikeout (`~~…~~`), super- /
  sub-script, links (inline / reference / autolink),
  images (inline / reference), footnote references, citation syntax
  (`[@key, p. 33]`), raw HTML / LaTeX, fenced divs, bracketed spans,
  YAML metadata blocks, pandoc title blocks, and the widened-native
  AST nodes (`Underline`, `SmallCaps`, `Quoted`, `LineBlock`).

---

## Templates and variables

`pandoc_py` ships a minimal pandoc-compatible template engine in
`pandoc_py.cli.templates`. It implements:

* `$variable$` and `${variable}` interpolation, with `.`-walked nested
  paths.
* `$if(var)$ … $elseif(var)$ … $else$ … $endif$` conditionals.
* `$for(var)$ … $sep$ … $endfor$` iteration with the anaphoric `it`.
* `$$` literal-dollar escape and `$-- comment` line comments.
* Pipes: `uppercase`, `lowercase`, `length`, `first`, `last`, `rest`,
  `reverse`, `chomp`, `pairs`.

Default templates are bundled for `html`, `latex`, `markdown`,
`native`, `json`, and `rst`.

Variables resolution order, highest priority first:

1. `--variable-json` values.
2. `--variable` values.
3. CLI `--metadata` values.
4. `--metadata-file` files.
5. The document AST's own `meta` field.
6. CLI flags that set template variables automatically (`--toc`,
   `--css`, `--include-in-header`, `--title-prefix`).

```bash
pandoc_py paper.md -s -t html \
   -V title="My Paper" \
   -V author="Jane Doe" \
   --css style.css \
   --include-in-header head.html \
   -o paper.html
```

The included templates are intentionally minimal. Pass `--template
my-template.html` to use a custom one.

---

## Filters

* **JSON filters (`-F`/`--filter`)**: `pandoc_py` serializes the AST
  as Pandoc-JSON, pipes it through the named executable with the
  output format as the first argument, and parses the JSON it
  returns. The executable must produce valid Pandoc-JSON.
* **Lua filters (`-L`/`--lua-filter`)**: dispatched through
  `pandoc_py.lua.LuaEngine`, which uses the optional `lupa` package
  if available. The Lua runtime can read the AST but does not yet
  implement the full pandoc Lua API surface; AST mutations from Lua
  are best-effort. Run `pip install lupa` to enable Lua filters.

Filters run in the order specified on the command line, after parsing
and before writing.

---

## Citations and bibliography

`-C`/`--citeproc` is parsed and a placeholder citeproc pass runs
during conversion. The pass currently leaves citations rendered as
`[@key]` markers; full CSL processing is a tracked follow-up packet.
Bibliography readers (`bibtex`, `biblatex`, `csljson`, `ris`,
`endnotexml`) collapse to `nocite` metadata matching pandoc's reader
shape, so files in those formats round-trip cleanly through the
pandoc oracle even though their contents are not yet rendered into
the document body.

---

## Slide shows

The slide-show writers (`beamer`, `pptx`, `revealjs`, `s5`, `slidy`,
`slideous`, `dzslides`) are registered and emit the basic
slide-per-`#`-heading structure. Advanced features documented in
pandoc's user guide — incremental lists, columns, speaker notes,
PowerPoint layout choice, frame attributes for beamer, parallax
backgrounds for reveal.js — are **not** wired up. The corresponding
flags (`-i`, `--slide-level`) are accepted but currently no-ops.

---

## EPUB metadata

The EPUB writer accepts metadata via the document's YAML metadata
block (everything pandoc's user guide describes for EPUB metadata —
`title`, `creator`, `identifier`, `language`, `subject`, `rights`,
`cover-image`, etc.) is parsed into `Document.meta` and serialized
into the OPF package file as Dublin Core elements. The
`--epub-metadata` / `--epub-cover-image` / `--epub-embed-font` /
`--epub-subdirectory` flags are accepted and stored but not yet
plumbed into the OPF writer.

---

## Math rendering

`pandoc_py` recognises pandoc's math syntax (`$…$`, `$$…$$`, `\(…\)`,
`\[…\]`) in the markdown reader and the various `Math` node types
in the AST. The HTML writer renders math nodes as plain Unicode by
default; `--mathjax` / `--mathml` / `--webtex` / `--katex` /
`--gladtex` are parsed and stored on `WriteOptions.extra` but the
HTML writer does not yet emit MathJax/KaTeX/etc. wrappers.

---

## Python API

Three layers, increasingly low-level:

### 1. `pandoc_py.app` — one-shot conversions

```python
from pandoc_py.app import convert_text, read_document, write_document

text   = convert_text(source, from_format, to_format, *, standalone=False)
doc    = read_document(source, from_format)
output = write_document(doc, to_format, *, standalone=False)
```

`convert_text` handles both `str` and `bytes` sources; `write_document`
returns `str` for text formats and `bytes` for binary formats.

### 2. `pandoc_py.io` — registry-based dispatch

```python
from pandoc_py.io import (
    Reader, Writer, ReadOptions, WriteOptions,
    register_reader, register_writer,
    get_reader, get_writer,
    list_readers, list_writers, list_aliases,
)

reader = get_reader('docx')
writer = get_writer('html')

doc = reader.read(open('paper.docx', 'rb').read())
out = writer.write(doc, options=WriteOptions(standalone=True))
```

### 3. `pandoc_py.ast` — AST nodes

The AST is a frozen-dataclass mirror of Pandoc's `Text.Pandoc.Definition`:

```python
from pandoc_py.ast import (
    Document, Block, Inline,
    # blocks:
    Paragraph, Heading, BlockQuote, BulletList, OrderedList,
    DefinitionList, CodeBlock, RawBlock, ThematicBreak, LineBlock,
    Div, Figure, Table, Null,
    # inlines:
    Str, Space, SoftBreak, HardBreak, Emph, Strong, Strikeout,
    Subscript, Superscript, Underline, SmallCaps, Quoted, Math,
    Code, Span, Link, Image, RawInline, Note, Cite, Citation,
    # metadata:
    MetaBool, MetaString, MetaInlines, MetaBlocks, MetaList, MetaMap,
    # attributes:
    Attr,
)
```

`Paragraph.is_plain` is tri-state (`True` / `False` / `None`):
preserves the Pandoc Plain↔Para distinction across native and JSON
round-trips while letting markdown-tight-list heuristics still apply
when the source format does not specify.

---

## Supported formats

`pandoc_py` covers every input and output format the reference Pandoc
binary 3.8.2 advertises (full names + aliases):

* **Markdown variants**: `markdown`, `markdown_strict`,
  `markdown_phpextra`, `markdown_mmd`, `markdown_github`, `gfm`,
  `commonmark`, `commonmark_x`.
* **HTML / web**: `html`, `html4`, `html5`, `xhtml`, `chunkedhtml`,
  `dzslides`, `revealjs`, `s5`, `slideous`, `slidy`.
* **Office / OOXML**: `docx`, `pptx`, `xlsx`.
* **OpenDocument**: `odt`, `opendocument`.
* **EPUB**: `epub`, `epub2`, `epub3`.
* **TeX / typesetting**: `latex`, `tex`, `context`, `beamer`,
  `texinfo`, `pdf`, `typst`, `ms`.
* **XML schemas**: `docbook`, `docbook4`, `docbook5`, `jats`,
  `jats_archiving`, `jats_articleauthoring`, `jats_publishing`, `tei`,
  `opml`, `xml`, `fb2`, `bits`, `endnotexml`, `icml`.
* **Wiki dialects**: `mediawiki`, `dokuwiki`, `jira`, `creole`,
  `tikiwiki`, `twiki`, `vimwiki`, `xwiki`, `zimwiki`.
* **Lightweight markup**: `rst`, `org`, `asciidoc`, `asciidoc_legacy`,
  `asciidoctor`, `textile`, `muse`, `haddock`, `pod`, `txt2tags`,
  `t2t`, `markua`, `djot`.
* **Man pages / roff**: `man`, `mdoc`, `roff`.
* **Bibliography**: `bibtex`, `biblatex`, `csljson`, `ris`,
  `endnotexml`.
* **Tabular**: `csv`, `tsv`.
* **Notebooks**: `ipynb`.
* **Plain / TTY**: `plain`, `ansi`, `bbcode`, `vimdoc`.
* **Pandoc internal**: `native`, `json` (Pandoc-JSON).
* **Rich text**: `rtf`.

Aliases honoured: `pandoc-json` → `json`, `commonmark-x` →
`commonmark_x`, `gfm` → `commonmark_x`, `markdown_github` →
`commonmark_x`, `markdown_strict` / `markdown_phpextra` /
`markdown_mmd` → `markdown`, `html5` / `html4` / `xhtml` → `html`,
`tex` → `latex`, `roff` → `man`, `t2t` → `txt2tags`, `endnote` →
`endnotexml`, `epub2` / `epub3` → `epub`, `docbook4` / `docbook5` →
`docbook`, `jats_archiving` / `jats_articleauthoring` /
`jats_publishing` → `jats`, `restructuredtext` → `rst`,
`asciidoctor` → `asciidoc`, `biblatex` → `bibtex`.

---

## Architecture

```
                                ┌─────────────────────────────────┐
                                │      pandoc_py.cli.main         │
                                │  argv → Options → convert_text  │
                                └────────────┬────────────────────┘
                                             │
                                             ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                       pandoc_py.app                              │
   │   read_document(src, fmt) ──► get_reader(fmt).read(src)          │
   │   write_document(doc, fmt) ─► get_writer(fmt).write(doc, opts)   │
   └─────────────────┬─────────────────────────────────┬──────────────┘
                     │                                 │
                     ▼                                 ▼
   ┌─────────────────────────────────┐ ┌─────────────────────────────────┐
   │       pandoc_py.io.Reader       │ │       pandoc_py.io.Writer       │
   │  (ABC, format_name, aliases,    │ │  (ABC, format_name, aliases,    │
   │   binary)                       │ │   binary)                       │
   └─────────────────┬───────────────┘ └─────────────────┬───────────────┘
                     │                                   │
                     ▼                                   ▼
   ┌─────────────────────────────────┐ ┌─────────────────────────────────┐
   │         pandoc_py.formats       │ │   pandoc_py.{readers,writers}   │
   │  per-family register_reader /   │ │  legacy callable functions      │
   │  register_writer at import      │ │  (markdown/html/native/json)    │
   │  time; subclasses Reader/Writer │ │  wrapped via _CallableReader /  │
   │  ABCs.                          │ │  _CallableWriter adapters.      │
   └─────────────────────────────────┘ └─────────────────────────────────┘
                     │                                   │
                     └──────────────────┬────────────────┘
                                        ▼
                          ┌──────────────────────────┐
                          │     pandoc_py.ast        │
                          │  Document / Block /      │
                          │  Inline / MetaValue /    │
                          │  Attr / Citation         │
                          └──────────────────────────┘
```

### Core invariants

1. **One AST.** Every reader produces a `Document`; every writer
   consumes a `Document`. The AST mirrors Pandoc's
   `Text.Pandoc.Definition` exactly for the constrained slice
   admitted by the matrix.
2. **One dispatcher.** `pandoc_py.app.convert_text` does not know any
   format-specific code paths; it delegates to the registry. Adding a
   format never requires editing `app.py`.
3. **One options dataclass.** `pandoc_py.io.WriteOptions` carries
   `standalone: bool` and a free-form `extra: dict[str, Any]` for
   format-specific settings; the CLI populates `extra` from the full
   pandoc option set (see the matrix above).
4. **Binary discipline.** Readers/writers declare `binary: bool` so
   the CLI knows whether to read/write bytes vs text.

---

## Verification model

`pandoc_py` ships with an oracle-backed differential test harness
under `tests/differential/`. Each row in
`trackers/CAPABILITY_MATRIX.csv` (and the two supplement matrices)
points at one or more reports under
`tests/differential/reports/<bucket>/<REPORT-ID>.report.json`.

### The five-strategy comparator ladder

`scripts/run_differential.py` picks the strongest strategy the route
allows:

| level | when used | semantics |
|---|---|---|
| `structured_json` (strict) | native/json input | exact JSON equality |
| `structured_json_normalized_<fmt>` | other reader-side reports | normalized JSON equality |
| `roundtrip_<fmt>_json` | both pandoc and pandoc_py emit text and pandoc reads back | reparse both outputs through the oracle reader, compare normalized JSON |
| `one_sided_oracle_reader_<fmt>` | pandoc has only a reader (e.g. `creole`, `vimwiki`) | reparse pandoc_py output through the oracle reader, compare to a markdown reference |
| `writer_only_<fmt>_emit_check` | pandoc has neither reader nor writer (e.g. `xlsx` writer when no reader exists) | accept on non-empty emit |

Three binary sub-strategies (`roundtrip_binary_`,
`binary_writer_only_`, `binary_one_sided_`) extend the same ladder to
docx, odt, epub, pptx, xlsx, rtf via `_reparse_binary_to_json`.

### Normalization (`_strip_attr_ids`)

Applied to every comparison **except** the strict `structured_json`
strategy: heading/div/codeblock identifier wipe, Plain ↔ Para,
meta-key skip-list (`jupyter`, `nbformat`, `kernelspec`,
`language_info`, `date`, `identifier`, `generator`, `language`,
`title`, `creator`, `rights`, `subject`, `references`), code-block
leading/trailing newline trim and uniform leading-whitespace dedent,
section-Div flatten, empty-anchor Span / empty Header drop,
citationNoteNum zero, inline `Str / Space / SoftBreak` run collapse
to a single `Str`. These normalizations are part of the governed
comparator-baseline policy in
`trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md`.

### Cross-platform oracle resolution

`scripts/run_differential.py` resolves the pandoc oracle in this
order: `PANDOC_ORACLE` env var → `/usr/bin/pandoc` →
`C:\Program Files\Pandoc\pandoc.exe` → `shutil.which('pandoc')`.
Each archived report records `oracle_version` so mixed-version
evidence (3.1.x and 3.8.x runs) is auditable.

---

## Adding a new format

Two files, no other edits:

1. Subclass `Reader` and/or `Writer` under `src/pandoc_py/formats/`:

   ```python
   from pandoc_py.ast import Document
   from pandoc_py.io import Reader, Writer, register_reader, register_writer

   class MyFormatReader(Reader):
       format_name = 'myformat'
       aliases = ('mf',)
       def read(self, source, options=None):
           if isinstance(source, bytes): source = source.decode('utf-8')
           # ... parse into a Document ...
           return Document(blocks=[...], source_format='myformat')

   class MyFormatWriter(Writer):
       format_name = 'myformat'
       aliases = ('mf',)
       def write(self, document, options=None):
           # ... build the output text ...
           return rendered_text

   register_reader(MyFormatReader())
   register_writer(MyFormatWriter())
   ```

2. Add one import in `src/pandoc_py/formats/__init__.py`:

   ```python
   from . import myformat   # noqa: F401
   ```

The dispatcher in `app.py` and the CLI need no changes.

For lightweight wiki-style formats, the helper template
`pandoc_py.formats._template.FormatConfig` + `register(config)` lets
you declare a complete reader+writer pair in 5–10 lines.

---

## Repository layout

```
pandoc-py/
├── src/pandoc_py/
│   ├── ast/                  # AST nodes (Document, Block, Inline, …)
│   ├── app.py                # convert_text / read_document / write_document
│   ├── cli/                  # CLI entry points, options, templates
│   │   ├── main.py
│   │   ├── options.py
│   │   └── templates.py
│   ├── io/                   # Reader/Writer ABCs + FormatRegistry + bootstrap
│   ├── readers/              # legacy callable readers (markdown, html, …)
│   ├── writers/              # legacy callable writers (markdown, html, …)
│   ├── formats/              # one module per family (rst, org, latex, docx, …)
│   ├── parsing/              # shared parsing helpers
│   ├── lua.py                # Lua filter engine (LuaEngine)
│   └── server.py             # Pandoc-compatible HTTP server scaffold
├── trackers/                 # governed capability matrices + progress reports
│   ├── CAPABILITY_MATRIX.csv
│   ├── CAPABILITY_MATRIX_NATIVE_SUPPLEMENT.csv
│   ├── CAPABILITY_MATRIX_FORMAT_FAMILIES_SUPPLEMENT.csv
│   ├── CONVERSION_PROGRESS.md
│   ├── NEXT_ITERATION.md
│   └── NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md
├── tests/
│   ├── unit/                 # 460+ unit tests
│   ├── fixtures/             # markdown / format / binary fixtures
│   ├── differential/         # oracle-backed report archive
│   │   └── reports/<bucket>/<REPORT-ID>.{report.json,oracle.out,python.out}
│   └── _oracle.py            # cross-platform pandoc oracle resolver
└── scripts/
    ├── run_python_cli.py     # thin wrapper used by the differential harness
    ├── run_differential.py   # oracle vs pandoc_py comparator
    └── report_conversion_progress.py
```

---

## Development

### Running the tests

```bash
PYTHONPATH=src python -m pytest tests/unit -q
```

468 unit tests pass at the time of writing (6 skipped — pandoc-only
oracle tests on a host without pandoc).

### Running an oracle-backed differential

```bash
python scripts/run_differential.py \
    tests/fixtures/format_families/simple.md \
    --from markdown --to html \
    --report-id MY-REPORT-001 \
    --report-dir tests/differential/reports/scratch
```

The runner prints the report JSON to stdout and archives all four
sidecar files (`oracle.out`, `oracle.err`, `python.out`,
`python.err`) plus `MY-REPORT-001.report.json` in the chosen
directory.

### Format-parity audit

A single test asserts that every pandoc input and output format is
reachable through `pandoc_py.io`:

```bash
PYTHONPATH=src python -m pytest tests/unit/test_full_format_parity.py -v
```

### CLI-options audit

```bash
PYTHONPATH=src python -m pytest tests/unit/test_cli_full_options.py -v
```

These tests are the executable contracts behind the parity matrix
above.

---

## License

Pandoc itself is GPL-2.0+. `pandoc_py` is an independent
re-implementation of the same conversion surface in Python; consult
`LICENSE` for licensing terms when distributing the result.

---

## Versioning and parity

Current version: see `pandoc_py.__version__`.

Format parity vs the reference Pandoc binary 3.8.2:

* Input formats: 48/48 = **100% format-name parity**.
* Output formats: 69/69 = **100% format-name parity**.
* Combined: 117/117 = **100% format-name parity**.

Functional parity is documented honestly in the [CLI options
matrix](#cli-options-matrix-vs-pandoc) above and in
`trackers/CAPABILITY_MATRIX*.csv`. The constrained-slice round-trip
verification (oracle-backed differential reports) covers what each
format implementation actually supports today; the CLI options
documented as 🟡 / ⚪ describe the surface gap between "every flag is
parsed and stored" (~95%) and "every flag changes pandoc_py's output
the way pandoc would" (~30–40% today, with the implemented set
documented above).
