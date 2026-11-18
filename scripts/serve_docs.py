#!/usr/bin/env python3
"""Serve Swagger locally and proxy API requests only to loopback clinic hosts."""

import argparse
import ipaddress
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY = 16 * 1024 * 1024
FORWARDED_HEADERS = {
    "accept", "content-type", "authorization", "x-rest-api-key", "x-rest-time-zone",
    "x-service-name", "x-service-rest-api-key", "x-user-token", "x-token", "x-mobile-app", "clinic-id",
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


class DocsHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format_string, *args):
        # API paths and query strings can contain personal data.
        pass

    def do_GET(self):
        if self.path.startswith("/__local_api/"):
            return self.proxy_api()
        if urlsplit(self.path).path in ("/", "/index.html"):
            body = (ROOT / "index.html").read_bytes().replace(
                b"<head>", b"<head><script>window.VETMANAGER_LOCAL_PROXY = true;</script>", 1
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        self.proxy_api()

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST
    do_OPTIONS = do_POST

    def proxy_api(self):
        if not self.path.startswith("/__local_api/"):
            return self.send_error(404)
        host, separator, suffix = self.path[len("/__local_api/"):].partition("/")
        try:
            target = urlsplit("http://" + unquote(host))
            name = target.hostname or ""
            local = name in ("localhost", "127.0.0.1", "::1") or name.endswith(".localhost")
            if not local or target.username or target.password or target.path or target.query or target.fragment:
                raise ValueError("Only local clinic hosts are allowed")
            if not separator or not suffix.startswith("rest/api/"):
                raise ValueError("Only /rest/api/ paths are allowed")
            addresses = socket.getaddrinfo(name, target.port or 80, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(row[4][0]).is_loopback for row in addresses):
                raise ValueError("Clinic host must resolve to loopback")
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > MAX_BODY:
                return self.send_error(413)
        except (ValueError, OSError):
            return self.send_error(400, "Use a local clinic host, for example one.localhost:8080")
        body = self.rfile.read(size) if size else None
        headers = {k: v for k, v in self.headers.items() if k.lower() in FORWARDED_HEADERS}
        request = Request("http://" + target.netloc + "/" + suffix, data=body, headers=headers, method=self.command)
        try:
            opener = build_opener(ProxyHandler({}), NoRedirect())
            try:
                response = opener.open(request, timeout=20)
            except HTTPError as error:
                response = error
            with response:
                content = response.read(MAX_BODY + 1)
                if len(content) > MAX_BODY:
                    return self.send_error(502, "Local API response is too large")
                self.send_response(response.code)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/octet-stream"))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except (URLError, TimeoutError, OSError):
            self.send_error(502, "Local API unavailable. Check the Docker stack and clinic port.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    print(f"Swagger preview: http://localhost:{args.port}/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), DocsHandler).serve_forever()
