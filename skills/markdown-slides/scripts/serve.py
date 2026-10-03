#!/usr/bin/env python3
"""Serve the deck root with Cache-Control: no-store headers."""

from __future__ import annotations

import http.server
import os
import socketserver

import config


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    root = config.deck_root()
    port = config.serve_port(root)
    os.chdir(root)
    with socketserver.TCPServer(("", port), NoCacheHandler) as httpd:
        print(f"Serving {root} at http://localhost:{port}/")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
