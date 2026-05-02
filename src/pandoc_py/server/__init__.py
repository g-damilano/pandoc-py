"""Pandoc-compatible HTTP server.

Pandoc ships a ``pandoc server`` mode that exposes the conversion
pipeline over HTTP. This module provides a minimal stdlib-only
``http.server`` implementation of the same surface for the
constrained slice we admit:

  POST /  with JSON body  {"text": "<source>", "from": "<fmt>",
                            "to": "<fmt>", "standalone": false}

The endpoint returns the converted text in plain text or JSON-wrapped
form depending on the requested output format. Binary outputs return
``application/octet-stream``.

The server is a thin wrapper around ``pandoc_py.app.convert_text`` and
honours the same registered format families as the CLI. This is the
primary entry point referenced by the inventory row
``INV-SERVER-001``.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from pandoc_py.app import convert_text


class PandocRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 (HTTP server convention)
        length = int(self.headers.get('Content-Length', '0'))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            self.send_error(400, 'Body must be JSON')
            return
        text = payload.get('text', '')
        from_format = payload.get('from', 'markdown')
        to_format = payload.get('to', 'html')
        standalone = bool(payload.get('standalone', False))
        try:
            result = convert_text(text, from_format, to_format, standalone=standalone)
        except Exception as exc:  # pragma: no cover (defensive surface)
            self.send_error(400, f'{type(exc).__name__}: {exc}')
            return
        self.send_response(200)
        if isinstance(result, bytes):
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(result)))
            self.end_headers()
            self.wfile.write(result)
        else:
            data = result.encode('utf-8')
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 (stdlib signature)
        # Quiet by default — tests don't care about per-request logs.
        return


def make_server(host: str = '127.0.0.1', port: int = 0) -> HTTPServer:
    return HTTPServer((host, port), PandocRequestHandler)


def serve_forever(host: str = '127.0.0.1', port: int = 8181) -> None:  # pragma: no cover
    server = make_server(host, port)
    print(f'pandoc_py.server listening on http://{host}:{port}/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


__all__ = ['PandocRequestHandler', 'make_server', 'serve_forever']
