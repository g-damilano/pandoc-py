from __future__ import annotations
import csv, re
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFINITION = REPO_ROOT / 'third_party' / 'pandoc-types' / 'src' / 'Text' / 'Pandoc' / 'Definition.hs'
SYMBOLS_CSV = REPO_ROOT / 'trackers' / 'PANDOC_TYPES_SYMBOLS.csv'
COVERAGE_CSV = REPO_ROOT / 'trackers' / 'AST_SOURCE_COVERAGE.csv'
PYTHON_AST_MAP = {
    'Document': 'Pandoc', 'Attr': 'Attr', 'Paragraph': 'Para', 'Heading': 'Header',
    'BulletList': 'BulletList', 'OrderedList': 'OrderedList', 'BlockQuote': 'BlockQuote',
    'ThematicBreak': 'HorizontalRule', 'CodeBlock': 'CodeBlock', 'RawBlock': 'RawBlock',
    'Div': 'Div', 'DefinitionList': 'DefinitionList', 'Figure': 'Figure', 'Table': 'Table',
    'Str': 'Str', 'Space': 'Space', 'SoftBreak': 'SoftBreak', 'HardBreak': 'LineBreak',
    'Emph': 'Emph', 'Strong': 'Strong', 'Strikeout': 'Strikeout', 'Subscript': 'Subscript',
    'Superscript': 'Superscript', 'Math': 'Math', 'Code': 'Code', 'Span': 'Span',
    'Link': 'Link', 'Image': 'Image', 'RawInline': 'RawInline', 'Note': 'Note',
    'Cite': 'Cite', 'Citation': 'Citation',
}
TYPE_NAMES = ['Pandoc','Meta','MetaValue','ListNumberStyle','ListNumberDelim','Format','Attr','RowHeadColumns','Alignment','ColWidth','Row','TableHead','TableBody','TableFoot','Caption','Cell','RowSpan','ColSpan','Block','QuoteType','MathType','Inline','Citation','CitationMode']
CONSTRUCTOR_PATTERNS = {
    'Block': ['Plain','Para','LineBlock','CodeBlock','RawBlock','BlockQuote','OrderedList','BulletList','DefinitionList','Header','HorizontalRule','Table','Figure','Div'],
    'Inline': ['Str','Emph','Underline','Strong','Strikeout','Superscript','Subscript','SmallCaps','Quoted','Cite','Code','Space','SoftBreak','LineBreak','Math','RawInline','Link','Image','Note','Span'],
    'MetaValue': ['MetaMap','MetaList','MetaBool','MetaString','MetaInlines','MetaBlocks'],
    'ListNumberStyle': ['DefaultStyle','Example','Decimal','LowerRoman','UpperRoman','LowerAlpha','UpperAlpha'],
    'ListNumberDelim': ['DefaultDelim','Period','OneParen','TwoParens'],
    'Alignment': ['AlignLeft','AlignRight','AlignCenter','AlignDefault'],
    'ColWidth': ['ColWidth','ColWidthDefault'],
    'QuoteType': ['SingleQuote','DoubleQuote'],
    'MathType': ['DisplayMath','InlineMath'],
    'CitationMode': ['AuthorInText','SuppressAuthor','NormalCitation'],
}
def detect(text: str, symbol: str) -> str:
    for kind, pat in [('data', rf'\bdata\s+{re.escape(symbol)}\b'), ('newtype', rf'\bnewtype\s+{re.escape(symbol)}\b'), ('type_alias', rf'\btype\s+{re.escape(symbol)}\b'), ('pattern', rf'\bpattern\s+{re.escape(symbol)}\b')]:
        if re.search(pat, text):
            return kind
    return 'referenced' if re.search(rf'\b{re.escape(symbol)}\b', text) else 'missing'

def main():
    text=DEFINITION.read_text(encoding='utf-8')
    rows=[]
    for name in TYPE_NAMES:
        rows.append({'Kind':'type','Name':name,'Status':detect(text,name),'Source':str(DEFINITION.relative_to(REPO_ROOT))})
    for parent,names in CONSTRUCTOR_PATTERNS.items():
        for name in names:
            rows.append({'Kind':f'{parent}_constructor','Name':name,'Status':detect(text,name),'Source':str(DEFINITION.relative_to(REPO_ROOT))})
    with SYMBOLS_CSV.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=['Kind','Name','Status','Source']); w.writeheader(); w.writerows(rows)
    names={r['Name'] for r in rows if r['Status']!='missing'}
    cov=[]
    for py, hs in PYTHON_AST_MAP.items():
        cov.append({'Python AST symbol':py,'Haskell anchor symbol':hs,'Coverage status':'anchored' if hs in names else 'missing_anchor','Source':str(DEFINITION.relative_to(REPO_ROOT))})
    with COVERAGE_CSV.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=['Python AST symbol','Haskell anchor symbol','Coverage status','Source']); w.writeheader(); w.writerows(cov)
    anchored=sum(1 for r in cov if r['Coverage status']=='anchored')
    print(f'Anchored current AST symbols: {anchored}/{len(cov)}')
if __name__=='__main__': main()
