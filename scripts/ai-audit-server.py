#!/usr/bin/env python3
"""AI Adoption Audit web tool — standalone server for ai-audit.webawesome.co.uk.

Stdlib only. Endpoints: GET / (tool page), GET /healthz, POST /render
({"kind": "onepager"|"full", "spec": {...}} -> rendered HTML).
"""
import argparse
import os
import socketserver
import sys
from http.server import SimpleHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dashboard import audit_page  # noqa: E402


class Handler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _send(self, code, body, ctype='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/healthz':
            self._send(200, b'ok', 'text/plain')
        elif path in ('/', '/index.html'):
            self._send(200, audit_page.page_html().encode('utf-8'))
        else:
            self._send(404, b'Not found', 'text/plain')

    def do_POST(self):
        if self.path.split('?', 1)[0] != '/render':
            self._send(404, b'Not found', 'text/plain')
            return
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            html = audit_page.handle_render(raw)
            self._send(200, html.encode('utf-8'))
        except Exception as e:
            self._send(400, str(e).encode('utf-8'), 'text/plain; charset=utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8080)))
    args = ap.parse_args()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', args.port), Handler) as httpd:
        print(f'AI audit tool at http://localhost:{args.port}', flush=True)
        httpd.serve_forever()


if __name__ == '__main__':
    main()
