#!/usr/bin/env python3
"""Simple HTTP server to serve the generated site directory."""
import http.server
import socketserver
import argparse
from pathlib import Path
import os

DEFAULT_PORT = 8000

parser = argparse.ArgumentParser(description="Serve the generated site locally")
parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
                    help="Port to bind the HTTP server")
args = parser.parse_args()

site_dir = Path(__file__).resolve().parent / "site"
if not site_dir.is_dir():
    raise SystemExit(f"Cartella 'site' non trovata: {site_dir}")

# Change working directory so the HTTP server serves from 'site'
os.chdir(site_dir)

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    # Silence logging to keep output clean
    def log_message(self, format, *args):
        pass

handler = QuietHandler

with socketserver.TCPServer(("0.0.0.0", args.port), handler) as httpd:
    print(f"Serving '{site_dir}' at http://localhost:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
