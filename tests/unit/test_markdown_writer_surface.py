from __future__ import annotations

import json
import subprocess

from pandoc_py.app import convert_text


def _reparse_markdown_to_json(markdown_text: str) -> dict[str, object]:
    proc = subprocess.run(
        ['/usr/bin/pandoc', '-f', 'markdown', '-t', 'json', '--wrap=none'],
        input=markdown_text,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_markdown_writer_places_heading_attrs_after_a_space() -> None:
    markdown = convert_text('# Head {#x .c key="val"}\n', 'markdown', 'markdown')
    assert markdown.startswith('# Head {#x .c key="val"}')


def test_json_heading_with_code_roundtrips_semantically_on_markdown_route() -> None:
    source = '{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[{"t":"Header","c":[1,["alpha-beta-gamma",[],[]],[{"t":"Str","c":"Alpha"},{"t":"Space"},{"t":"Code","c":[["",[],[]],"beta gamma"]}]]}]}'
    markdown = convert_text(source, 'json', 'markdown')
    reparsed = _reparse_markdown_to_json(markdown)
    assert reparsed['blocks'][0]['c'][0] == 1
    assert reparsed['blocks'][0]['c'][1] == ['alpha-beta-gamma', [], []]


def test_json_heading_with_link_roundtrips_semantically_on_markdown_route() -> None:
    source = '{"pandoc-api-version":[1,23,1],"meta":{},"blocks":[{"t":"Header","c":[1,["alpha-beta",[],[]],[{"t":"Str","c":"Alpha"},{"t":"Space"},{"t":"Link","c":[["",[],[]],[{"t":"Str","c":"beta"}],["https://example.com",""]]}]]}]}'
    markdown = convert_text(source, 'json', 'markdown')
    reparsed = _reparse_markdown_to_json(markdown)
    assert reparsed['blocks'][0]['c'][1] == ['alpha-beta', [], []]
    assert reparsed['blocks'][0]['c'][2][2]['c'][2][0] == 'https://example.com'
