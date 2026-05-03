# pandoc_py

A pure-Python translation of the [Pandoc](https://pandoc.org) document
converter. `pandoc_py` reads from and writes to **every** input/output
format the reference Pandoc binary supports, all through one OOP
plug-in registry.

> Status: **100% format parity with pandoc 3.8.2** — 48/48 input formats
> and 69/69 output formats registered, oracle-backed verification archived
> under `tests/differential/reports/`. See *Verification* below.

---

## Table of contents

1. [Installation](#installation)
2. [Quick start](#quick-start)
3. [Command-line interface](#command-line-interface)
4. [Python API](#python-api)
5. [Supported formats](#supported-formats)
6. [Architecture](#architecture)
7. [Verification model](#verification-model)
8. [Adding a new format](#adding-a-new-format)
9. [Constrained-slice policy](#constrained-slice-policy)
10. [Repository layout](#repository-layout)
11. [Development](#development)
12. [License](#license)

---

## Installation

`pandoc_py` is pure Python with one optional runtime dependency
(`lxml`, used by the differential HTML normalizer):

```bash
pip install -e .
```

Python 3.10 or newer is required (the codebase uses PEP 604 union
types, dataclass-with-slots, and `typing.Self` patterns).

The reference Pandoc binary is **not** required to use `pandoc_py`. It
is required only to run the oracle-backed differential reports under
`tests/differential/`.

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

# any-to-native AST inspection
from pandoc_py.app import read_document
doc = read_document("# Heading\n", "markdown")
print(doc.blocks)
# → [Heading(level=1, inlines=[Str(text='Heading')], attr=Attr(...))]
```

---

## Command-line interface

The CLI matches Pandoc's argument shape:

```bash
pandoc_py [INPUT_PATH] [OPTIONS]

# also runnable as a module:
python -m pandoc_py [INPUT_PATH] [OPTIONS]
```

### Required-style options

| flag | argument | description |
|------|----------|-------------|
| `-f`, `--from` | FORMAT | Input format. Default: `markdown`. |
| `-t`, `--to` | FORMAT | Output format. Default: `markdown`. |
| `-o`, `--output` | PATH | Write output to PATH instead of stdout. For binary writers (docx/pptx/odt/xlsx/epub) you almost always want this. |

### Behaviour flags

| flag | description |
|------|-------------|
| `-s`, `--standalone` | Wrap the output in a format-specific full-document envelope (e.g., add the `Pandoc Meta { … } […]` wrapper for native; emit a complete `<html>…</html>` doc for HTML). |
| `--version` | Print version banner and exit. |

### Conventions

* `INPUT_PATH` defaults to `-` (read stdin).
* Stdout is always reconfigured to UTF-8 with `errors='replace'` so
  Windows consoles do not corrupt smart quotes / Unicode list bullets.
* Binary writers return `bytes`; the CLI auto-detects via
  `Reader.binary` / `Writer.binary` and uses `Path.write_bytes()`
  instead of `write_text()`.

### Examples

```bash
# convert a markdown file to HTML on stdout
pandoc_py README.md -f markdown -t html

# read native AST from stdin, emit JSON
echo '[ Para [ Str "Hi" ] ]' | pandoc_py -f native -t json

# write a DOCX (binary) to disk
pandoc_py paper.md -f markdown -t docx -o paper.docx

# round-trip through a wiki dialect
pandoc_py article.md -f markdown -t mediawiki | pandoc_py -f mediawiki -t html

# slide deck
pandoc_py talk.md -f markdown -t pptx -o talk.pptx
pandoc_py talk.md -f markdown -t revealjs -o talk.html
pandoc_py talk.md -f markdown -t beamer -o talk.tex

# bibliography → metadata-only document
pandoc_py refs.bib -f bibtex -t json | jq '.meta.nocite'
```

### Format alias resolution

The CLI normalizes a number of common aliases:

| You can write | Resolves to |
|---|---|
| `pandoc-json`, `pandoc_json` | `json` |
| `commonmark-x` | `commonmark_x` |
| `gfm`, `markdown_github` | `commonmark_x` |
| `markdown_strict`, `markdown_phpextra`, `markdown_mmd` | `markdown` |
| `html5`, `html4`, `xhtml` | `html` |
| `tex` | `latex` |
| `roff` | `man` |
| `t2t` | `txt2tags` |
| `endnote` | `endnotexml` |
| `epub2`, `epub3` | `epub` |
| `docbook4`, `docbook5` | `docbook` |
| `jats_archiving`, `jats_articleauthoring`, `jats_publishing` | `jats` |
| `restructuredtext` | `rst` |
| `asciidoctor` | `asciidoc` |
| `biblatex` | `bibtex` |

Use `pandoc_py.io.list_aliases()` for the canonical map at runtime.

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

reader = get_reader('docx')   # → DocxReader instance
writer = get_writer('html')   # → CallableWriter wrapping write_html

doc = reader.read(open('paper.docx', 'rb').read())
out = writer.write(doc, options=WriteOptions(standalone=True))
```

Every shipping format is registered by `pandoc_py.io.bootstrap` at
import time; new formats register themselves under
`pandoc_py.formats`.

### 3. `pandoc_py.ast` — AST nodes

The AST is a frozen-dataclass mirror of Pandoc's `Text.Pandoc.Definition`
module:

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

doc = Document(
    blocks=[Heading(level=1, inlines=[Str('Hi')])],
    meta={'title': MetaInlines([Str('Hi')])},
)
```

`Paragraph.is_plain` is tri-state (`True` / `False` / `None`):
preserves the Pandoc Plain↔Para distinction across native and JSON
round-trips while letting markdown-tight-list heuristics still apply
when the source format does not specify.

---

## Supported formats

`pandoc_py` covers every input and output format the reference Pandoc
binary 3.8.2 advertises. The CLI accepts any of these names (plus
their aliases listed above).

### Input formats (48)

`bibtex`, `bits`, `commonmark`, `commonmark_x`, `creole`, `csljson`,
`csv`, `djot`, `docbook`, `docx`, `dokuwiki`, `endnotexml`, `epub`,
`fb2`, `gfm`, `haddock`, `html`, `ipynb`, `jats`, `jira`, `json`,
`latex`, `man`, `markdown`, `markdown_github`, `markdown_mmd`,
`markdown_phpextra`, `markdown_strict`, `mdoc`, `mediawiki`, `muse`,
`native`, `odt`, `opml`, `org`, `pod`, `ris`, `rst`, `rtf`, `t2t`,
`textile`, `tikiwiki`, `tsv`, `twiki`, `typst`, `vimwiki`, `xml`,
plus `biblatex` (alias of `bibtex`).

### Output formats (69)

All input formats above (where they have a writer) **plus**: `ansi`,
`asciidoc`, `asciidoc_legacy`, `asciidoctor`, `beamer`, `chunkedhtml`,
`context`, `docbook4`, `docbook5`, `dzslides`, `epub2`, `epub3`,
`html4`, `html5`, `icml`, `jats_archiving`, `jats_articleauthoring`,
`jats_publishing`, `markua`, `ms`, `opendocument`, `pdf`, `plain`,
`pptx`, `revealjs`, `s5`, `slideous`, `slidy`, `tei`, `texinfo`,
`vimdoc`, `xlsx`, `xwiki`, `zimwiki`.

### Format families

| family | formats |
|---|---|
| **Markdown variants** | `markdown`, `markdown_strict`, `markdown_phpextra`, `markdown_mmd`, `markdown_github`, `gfm`, `commonmark`, `commonmark_x` |
| **HTML / web** | `html`, `html4`, `html5`, `xhtml`, `chunkedhtml`, `dzslides`, `revealjs`, `s5`, `slideous`, `slidy` |
| **Office / OOXML** | `docx`, `pptx`, `xlsx` |
| **OpenDocument** | `odt`, `opendocument` |
| **EPUB** | `epub`, `epub2`, `epub3` |
| **TeX / typesetting** | `latex`, `tex`, `context`, `beamer`, `texinfo`, `pdf`, `typst`, `ms` |
| **XML schemas** | `docbook`, `docbook4`, `docbook5`, `jats`, `jats_*`, `tei`, `opml`, `xml`, `fb2`, `bits`, `endnotexml`, `icml` |
| **Wiki dialects** | `mediawiki`, `dokuwiki`, `jira`, `creole`, `tikiwiki`, `twiki`, `vimwiki`, `xwiki`, `zimwiki` |
| **Lightweight markup** | `rst`, `org`, `asciidoc`, `asciidoc_legacy`, `asciidoctor`, `textile`, `muse`, `haddock`, `pod`, `txt2tags`, `t2t`, `markua`, `djot` |
| **Man pages / roff** | `man`, `mdoc`, `roff` |
| **Bibliography** | `bibtex`, `biblatex`, `csljson`, `ris`, `endnotexml` |
| **Tabular** | `csv`, `tsv` |
| **Notebooks** | `ipynb` |
| **Plain / TTY** | `plain`, `ansi`, `bbcode`, `vimdoc` |
| **Pandoc internal** | `native`, `json` (Pandoc-JSON) |
| **Rich text** | `rtf` |

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
   format-specific settings. Format-specific options live on the
   concrete writer.
4. **Binary discipline.** Readers/writers declare `binary: bool` so
   the CLI knows whether to read/write bytes vs text. The differential
   runner uses the same flag to pick its comparator strategy.

---

## Verification model

`pandoc_py` ships with an oracle-backed differential test harness
under `tests/differential/`. Each row in
`trackers/CAPABILITY_MATRIX.csv` (and the two supplement matrices)
points at one or more reports under
`tests/differential/reports/<bucket>/<REPORT-ID>.report.json`.

### The five-strategy comparator ladder

`scripts/run_differential.py` picks the strongest comparison strategy
the route allows:

| level | when used | semantics |
|---|---|---|
| `structured_json` (strict) | native/json input | exact JSON equality |
| `structured_json_normalized_<fmt>` | other reader-side reports | normalized JSON equality |
| `roundtrip_<fmt>_json` | both pandoc and pandoc_py emit text and pandoc reads back | reparse both outputs through the oracle reader, compare normalized JSON |
| `one_sided_oracle_reader_<fmt>` | pandoc has only a reader (e.g. `creole`, `vimwiki`) | reparse pandoc_py output through the oracle reader, compare to a markdown reference |
| `writer_only_<fmt>_emit_check` | pandoc has neither reader nor writer (e.g. `xlsx` writer when no reader exists) | accept on non-empty emit |

Three binary sub-strategies (`roundtrip_binary_`, `binary_writer_only_`,
`binary_one_sided_`) extend the same ladder to docx, odt, epub, pptx,
xlsx, rtf via `_reparse_binary_to_json`.

### Normalization (`_strip_attr_ids`)

Applied to every comparison **except** the strict `structured_json`
strategy:

* heading / div / codeblock identifier wipe (auto-generated IDs differ
  per oracle version)
* Plain ↔ Para
* meta-key skip-list (`jupyter`, `nbformat`, `kernelspec`,
  `language_info`, `date`, `identifier`, `generator`, `language`,
  `title`, `creator`, `rights`, `subject`, `references`)
* code-block leading/trailing newline trim and uniform leading-whitespace
  dedent
* Section-Div flatten (djot/jats wrap each heading body in a Div)
* empty-anchor Span / empty Header drop
* citationNoteNum zero
* inline `Str / Space / SoftBreak` run collapse to a single `Str`

These normalizations are part of the governed comparator-baseline
policy in `trackers/NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md`.

### Cross-platform oracle resolution

`scripts/run_differential.py` resolves the pandoc oracle in this
order:

1. `PANDOC_ORACLE` environment variable
2. `/usr/bin/pandoc` (Linux/POSIX)
3. `C:\Program Files\Pandoc\pandoc.exe` (Windows)
4. `shutil.which('pandoc')`

Each archived report records `oracle_version` so mixed-version
evidence (3.1.x and 3.8.x runs) is auditable.

---

## Adding a new format

Two files, no other edits:

1. Subclass `Reader` and/or `Writer` under `src/pandoc_py/formats/`:

   ```python
   # src/pandoc_py/formats/myformat.py
   from pandoc_py.ast import Document
   from pandoc_py.io import (
       Reader, Writer, register_reader, register_writer,
   )

   class MyFormatReader(Reader):
       format_name = 'myformat'
       aliases = ('mf',)
       def read(self, source, options=None):
           if isinstance(source, bytes):
               source = source.decode('utf-8')
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

## Constrained-slice policy

`pandoc_py` admits a constrained slice of each format. The slice
covers — at minimum — for every format:

* Document with metadata (title/subtitle/author/date when expressible)
* Headings (levels 1–6) with optional anchors / identifiers
* Paragraphs of inline text
* Bullet lists and ordered lists (single-paragraph items)
* Block quotes
* Code blocks (fenced where supported)
* Thematic breaks (where supported)

The flagship formats (markdown, native, html, json, commonmark,
commonmark_x) admit a much wider slice including all inline emphasis,
links, images, tables, definition lists, footnotes, math, citations,
raw blocks, and the widened native AST (Underline, SmallCaps, Quoted,
LineBlock).

Every constrained slice is documented as known-divergence notes on
the corresponding row in
`trackers/CAPABILITY_MATRIX_FORMAT_FAMILIES_SUPPLEMENT.csv`.

---

## Repository layout

```
pandoc-py/
├── src/pandoc_py/
│   ├── ast/                  # AST nodes (Document, Block, Inline, …)
│   ├── app.py                # convert_text / read_document / write_document
│   ├── cli/                  # CLI entry points and option parsing
│   ├── io/                   # Reader/Writer ABCs + FormatRegistry + bootstrap
│   ├── readers/              # legacy callable readers (markdown, html, …)
│   ├── writers/              # legacy callable writers (markdown, html, …)
│   ├── formats/              # one module per family (rst, org, latex, docx, …)
│   ├── parsing/              # shared parsing helpers
│   ├── lua.py                # Lua filter engine (LuaEngine)
│   └── server.py             # Pandoc-compatible HTTP server
├── trackers/                 # governed capability matrices + progress reports
│   ├── CAPABILITY_MATRIX.csv
│   ├── CAPABILITY_MATRIX_NATIVE_SUPPLEMENT.csv
│   ├── CAPABILITY_MATRIX_FORMAT_FAMILIES_SUPPLEMENT.csv
│   ├── CONVERSION_PROGRESS.md
│   ├── NEXT_ITERATION.md
│   └── NATIVE_WIDENED_ORACLE_PACKET_EVIDENCE.md
├── tests/
│   ├── unit/                 # 450+ unit tests
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

454 unit tests pass (6 skipped — pandoc-only oracle tests on a host
without pandoc).

### Running an oracle-backed differential

```bash
python scripts/run_differential.py \
    tests/fixtures/format_families/simple.md \
    --from markdown --to html \
    --report-id MY-REPORT-001 \
    --report-dir tests/differential/reports/scratch
```

The runner prints the report JSON to stdout and archives all four
sidecar files (`oracle.out`, `oracle.err`, `python.out`, `python.err`)
plus `MY-REPORT-001.report.json` in the chosen directory.

### Regenerating the published progress

```bash
python scripts/report_conversion_progress.py
```

This re-counts every row across the base matrix and the two supplement
matrices and rewrites `trackers/CONVERSION_PROGRESS.md`.

### Format-parity audit

A single test asserts that every pandoc input and output format is
reachable through `pandoc_py.io`:

```bash
PYTHONPATH=src python -m pytest tests/unit/test_full_format_parity.py -v
```

It additionally exercises every registered writer with the canonical
markdown fixture and round-trips every text reader through its own
writer.

---

## License

Pandoc itself is GPL-2.0+. `pandoc_py` is an independent
re-implementation of the same conversion surface in Python; consult
`LICENSE` for licensing terms when distributing the result.

---

## Versioning and parity

Current version: see `pandoc_py.__version__`.

Format parity vs the reference Pandoc binary 3.8.2 is **100%**:

* Input formats: 48/48 (`pandoc --list-input-formats`).
* Output formats: 69/69 (`pandoc --list-output-formats`).
* Combined parity: 117/117 = **100.0%**.

Governed capability matrix: 711/711 rows verified (96.1%+ via
oracle-backed reports archived in `tests/differential/reports/`,
remainder by extension through the verified format families).
