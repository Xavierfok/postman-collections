"""Stand-in API for CI: answers every request with a JSON 401, like the real
APIs do without a key. Lets newman run every request in the collections
without touching production."""

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def _reply(self):
        length = int(self.headers.get("content-length") or 0)
        if length:
            self.rfile.read(length)
        body = json.dumps({"detail": {"message": "API key is invalid."}, "mock": True}).encode()
        self.send_response(401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _reply

    def log_message(self, fmt, *args):
        sys.stderr.write("mock: " + fmt % args + "\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
