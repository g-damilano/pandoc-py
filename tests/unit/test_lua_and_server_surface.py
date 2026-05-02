"""Surface tests for the Lua engine and pandoc server modules."""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / 'src'
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pandoc_py.app import convert_text
from pandoc_py.ast import Document, Heading, Str
from pandoc_py.lua import LuaEngine, apply_filter
from pandoc_py.server import make_server


def test_lua_engine_reports_availability_consistently():
    """``is_available`` and the runtime engine agree on whether lupa is
    importable in this environment."""
    engine = LuaEngine()
    assert LuaEngine.is_available() == (engine._lupa is not None)


def test_lua_apply_filter_returns_document_when_engine_unavailable(tmp_path: Path):
    """When lupa isn't available, ``apply_filter`` must return the
    document unchanged rather than raising."""
    document = Document(blocks=[Heading(level=1, inlines=[Str('Heading')])])
    lua_file = tmp_path / 'noop.lua'
    lua_file.write_text('-- noop', encoding='utf-8')
    out = apply_filter(document, lua_file)
    assert isinstance(out, Document)
    assert out.blocks == document.blocks


def test_pandoc_server_converts_markdown_to_html_via_http():
    """The HTTP server exposes ``convert_text`` end-to-end."""
    server = make_server('127.0.0.1', 0)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        body = json.dumps({
            'text': '# Heading\n\nA paragraph.\n',
            'from': 'markdown', 'to': 'html', 'standalone': False,
        }).encode('utf-8')
        req = urllib.request.Request(
            f'http://127.0.0.1:{port}/', data=body,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            text = resp.read().decode('utf-8')
        assert '<h1' in text
        assert 'Heading' in text
        # Sanity check: server result matches the in-process call.
        assert text == convert_text('# Heading\n\nA paragraph.\n', 'markdown', 'html')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
