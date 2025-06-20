#!/usr/bin/env python3
"""Simple HTTP server to serve the generated site directory."""
import http.server
import socketserver
import argparse
from pathlib import Path
import yaml
import os

DEFAULT_PORT = 8000

parser = argparse.ArgumentParser(description="Serve the generated site locally")
parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
                    help="Port to bind the HTTP server")
args = parser.parse_args()

# Load configuration to determine the output directory
script_dir = Path(__file__).resolve().parent
config_path = script_dir / "config.yml"
if not config_path.exists():
    raise SystemExit("File di configurazione 'config.yml' non trovato")
with config_path.open(encoding="utf-8") as f:
    config = yaml.safe_load(f)

output_dir = Path(config.get("output_dir", "site/"))
site_dir = output_dir if output_dir.is_absolute() else script_dir / output_dir
if not site_dir.is_dir():
    raise SystemExit(f"Cartella '{output_dir}' non trovata: {site_dir}")

# Change working directory so the HTTP server serves from the configured output directory
os.chdir(site_dir)

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
