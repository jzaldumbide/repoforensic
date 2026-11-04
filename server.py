import os
import json
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).parent.resolve()
PUBLIC_DIR = BASE_DIR / "public"
RESULTS_FILE = BASE_DIR / "analysis_results.json"
CACHE_DIR = BASE_DIR / "repos_cache"


def get_empty_results():
    from datetime import datetime
    return {
        "generated_at": datetime.now().isoformat(),
        "nodes": [],
        "edges": [],
        "all_comparisons": []
    }


class GraphAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def _send_json(self, status_code: int, payload: dict):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/results":
            if RESULTS_FILE.exists():
                data = RESULTS_FILE.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_json(200, get_empty_results())
            return
        if parsed.path == "/api/health":
            self._send_json(200, {"status": "ok"})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"

        if parsed.path == "/api/reanalyze":
            try:
                payload = json.loads(body)
                urls = payload.get("urls", [])
                if not urls:
                    empty = get_empty_results()
                    RESULTS_FILE.write_text(json.dumps(empty, indent=2, ensure_ascii=False), encoding="utf-8")
                    self._send_json(200, empty)
                    return
                from analyzer import compare_all_repos
                data = compare_all_repos(CACHE_DIR, urls)
                RESULTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                self._send_json(200, data)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if parsed.path == "/api/clear-repos":
            try:
                payload = json.loads(body) if body.strip() else {}
                delete_cache = payload.get("delete_cache", True)
                if delete_cache and CACHE_DIR.exists():
                    shutil.rmtree(CACHE_DIR, ignore_errors=True)
                    CACHE_DIR.mkdir(parents=True, exist_ok=True)
                empty = get_empty_results()
                RESULTS_FILE.write_text(json.dumps(empty, indent=2, ensure_ascii=False), encoding="utf-8")
                self._send_json(200, empty)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if parsed.path == "/api/delete-repo":
            try:
                payload = json.loads(body)
                repo_id = payload.get("id")
                if not RESULTS_FILE.exists():
                    self._send_json(200, get_empty_results())
                    return
                current = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
                nodes = [n for n in current.get("nodes", []) if n.get("id") != repo_id]
                edges = [
                    e for e in current.get("edges", [])
                    if e.get("source") != repo_id and e.get("target") != repo_id
                ]
                comparisons = [
                    c for c in current.get("all_comparisons", [])
                    if c.get("source") != repo_id and c.get("target") != repo_id
                ]
                current["nodes"] = nodes
                current["edges"] = edges
                current["all_comparisons"] = comparisons
                RESULTS_FILE.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
                self._send_json(200, current)
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8765))
    server = HTTPServer((host, port), GraphAppHandler)
    print(f"Server listening on http://{host}:{port}")
    server.serve_forever()
