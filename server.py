#!/usr/bin/env python3
"""Pattern Reps local server.

Serves index.html at http://127.0.0.1:8123/ and persists app data to
data/store.json (one JSON object: {"<doc path>": <doc>, ...}), so progress
survives any browser cleanup. Standard library only.

Run:  python3 server.py
Stop: Ctrl+C
"""
import json
import os
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
DATA_FILE = os.path.join(DATA_DIR, "store.json")
PORT = 8123
LOCK = threading.Lock()


def load():
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save(store):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=1, sort_keys=True)
    os.replace(tmp, DATA_FILE)  # atomic: a crash never corrupts the file


class Handler(SimpleHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _qpath(self, u):
        return parse_qs(u.query).get("path", [None])[0]

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/ping":
            return self._json(200, {"ok": True, "app": "pattern-reps"})
        if u.path == "/api/docs":
            with LOCK:
                return self._json(200, load())
        if u.path == "/api/doc":
            p = self._qpath(u)
            with LOCK:
                store = load()
            if p is not None and p in store:
                return self._json(200, {"exists": True, "data": store[p]})
            return self._json(200, {"exists": False})
        if u.path == "/api/col":
            c = (self._qpath(u) or "").rstrip("/")
            with LOCK:
                store = load()
            docs = [v for k, v in store.items()
                    if k.startswith(c + "/") and "/" not in k[len(c) + 1:]]
            return self._json(200, {"docs": docs})
        return super().do_GET()

    def do_PUT(self):
        u = urlparse(self.path)
        if u.path == "/api/doc":
            p = self._qpath(u)
            if not p:
                return self._json(400, {"error": "missing path"})
            n = int(self.headers.get("Content-Length", 0) or 0)
            try:
                doc = json.loads(self.rfile.read(n))
            except ValueError:
                return self._json(400, {"error": "invalid JSON"})
            with LOCK:
                store = load()
                store[p] = doc
                save(store)
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "not found"})

    def do_DELETE(self):
        u = urlparse(self.path)
        if u.path == "/api/doc":
            p = self._qpath(u)
            with LOCK:
                store = load()
                store.pop(p, None)
                save(store)
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # keep the terminal quiet
        pass


def main():
    os.chdir(ROOT)  # serve index.html from the repo folder
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)  # localhost only
    url = "http://127.0.0.1:%d/" % PORT
    print("Pattern Reps running at", url)
    print("Data file:", DATA_FILE)
    print("Ctrl+C to stop.")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
