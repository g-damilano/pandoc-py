# Haskell repo inventory

This document seeds **M1 — Inventory complete** for the current `pandoc-main.zip` reference archive.

## Snapshot

- Archive inspected: `pandoc-main.zip`
- Top-level repository entries counted: 2996
- Haskell source modules inventoried across included package roots: 280
- Included package roots with Haskell source:
  - main core tree: `237` modules
  - CLI package: `1` module
  - Lua engine package: `41` modules
  - server package: `1` module
- Test tree entries present: `2062`
- Data tree entries present: `275`

## Top-level repository distribution

| Top area | Entry count |
|---|---:|
| `test` | 2062 |
| `data` | 275 |
| `src` | 270 |
| `pandoc-lua-engine` | 111 |
| `wasm` | 75 |
| `citeproc` | 51 |
| `pandoc-cli` | 24 |
| `tools` | 23 |
| `doc` | 21 |
| `.github` | 16 |
| `xml-light` | 9 |
| `pandoc-server` | 8 |
| `windows` | 6 |
| `macos` | 5 |
| `man` | 4 |

## Haskell module distribution by subsystem

| Subsystem | Module count |
|---|---:|
| `app` | 5 |
| `citeproc` | 7 |
| `cli` | 1 |
| `core_support` | 45 |
| `lua` | 41 |
| `parsing` | 9 |
| `reader` | 96 |
| `runtime_class` | 7 |
| `server` | 1 |
| `writer` | 68 |

## High-value source families surfaced

### Readers

The archive contains **43** top-level reader families and **53** nested reader-support modules.

Top-level reader families:
`AsciiDoc, BibTeX, CSV, CommonMark, Creole, CslJson, Djot, DocBook, Docx, DokuWiki, EPUB, EndNote, FB2, HTML, Haddock, Ipynb, JATS, Jira, LaTeX, Man, Markdown, Mdoc, MediaWiki, Metadata, Muse, Native, ODT, OPML, Org, Pod, Pptx, RIS, RST, RTF, Roff, TWiki, Textile, TikiWiki, Txt2Tags, Typst, Vimwiki, XML, Xlsx`

### Writers

The archive contains **49** top-level writer families and **19** nested writer-support modules.

Top-level writer families:
`ANSI, AnnotatedTable, AsciiDoc, BBCode, BibTeX, Blaze, ChunkedHTML, CommonMark, ConTeXt, CslJson, Djot, DocBook, Docx, DokuWiki, EPUB, FB2, GridTable, HTML, Haddock, ICML, Ipynb, JATS, Jira, LaTeX, Man, Markdown, Math, MediaWiki, Ms, Muse, Native, ODT, OOXML, OPML, OpenDocument, Org, Powerpoint, RST, RTF, Roff, Shared, TEI, Texinfo, Textile, Typst, Vimdoc, XML, XWiki, ZimWiki`

### Parsing and orchestration

- Shared parsing modules: `9`
- App/orchestration modules: `5`
- Runtime/class/state modules: `7`
- Core support modules outside those buckets: `45`

### Additional package roots in this archive

- Lua engine package modules: `41`
- Server package modules: `1`
- CLI package modules: `1`

## Test surface cues

This archive has a very large test tree, heavily weighted toward command tests and rich container-format tests.

| Test area | Entry count |
|---|---:|
| `test/command` | 1157 |
| `test/docx` | 235 |
| `test/pptx` | 213 |
| `test/odt` | 103 |

## Operational consequence

The repository is not just a single library tree. It is a multi-package program surface with:
- the main conversion core,
- a separate CLI package,
- a separate Lua engine package,
- a separate server package,
- and a substantial test and data corpus.

That means the port-control system must track **package-root provenance** as well as module mapping. A Python port that only mirrors `src/Text/Pandoc/*` will miss real behavior living in the ancillary package roots.

## Generated machine assets

- `trackers/HASKELL_MODULE_INVENTORY.csv`
- `trackers/HASKELL_CAPABILITY_SEED.csv`
- `trackers/HASKELL_REPO_SUMMARY.json`
- `scripts/extract_haskell_inventory.py`
