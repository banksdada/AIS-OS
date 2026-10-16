#!/usr/bin/env python3
"""
Dashboard server for the AI OS.

Serves scripts/dashboard/index.html and the generated data/dashboard.json.
Regenerates the data file on each request so the page always reflects the
latest connection check, without needing a separate cron job.

Usage:
  python3 scripts/dashboard/serve.py            # http://localhost:8080
  python3 scripts/dashboard/serve.py --port 9000
"""
import argparse
import http.server
import json
import os
import socketserver
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_REPO_ROOT, 'scripts'))

# Load .env so the pipeline works without exporting every var into the shell.
_ENV = os.path.join(_REPO_ROOT, '.env')
if os.path.exists(_ENV):
    with open(_ENV) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
DATA = os.path.join(_REPO_ROOT, 'data', 'dashboard.json')


def regenerate():
    """Re-run the data pipeline and write data/dashboard.json."""
    import dashboard.generate as gen
    payload = {
        'generatedAt': __import__('datetime').datetime.now().isoformat(timespec='seconds'),
        'domains': gen._domains(),
        'leads': gen._leads(),
        'drafts': gen._drafts(),
        'wordpress': gen._wordpress(),
    }
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, 'w') as f:
        json.dump(payload, f, indent=2)
    return payload


class Handler(http.server.SimpleHTTPRequestHandler):
    # Serve the dashboard directory as the document root.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(PAGE), **kwargs)

    def _serve_file(self, file_path, content_type):
        try:
            with open(file_path, 'rb') as fh:
                content = fh.read()
        except OSError as exc:
            self.send_error(404, f'File not found: {file_path} ({exc})')
            return

        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        requested = self.path.split('?', 1)[0]
        if requested in ('/', '/index.html'):
            self._serve_file(PAGE, 'text/html; charset=utf-8')
        elif requested in ('/data', '/data/dashboard.json'):
            try:
                payload = regenerate()
            except Exception as e:
                self.send_error(500, f'data pipeline failed: {e}')
                return
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        print(f"[dashboard] {args[0]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    args = ap.parse_args()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('', args.port), Handler) as httpd:
        print(f"Dashboard running at http://localhost:{args.port}")
        print(f"  page : http://localhost:{args.port}/")
        print(f"  data : http://localhost:{args.port}/data")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")


if __name__ == '__main__':
    main()
