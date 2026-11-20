"""A tiny JSON API used to try replaygate on a real pull request.

Run:  PORT=3001 python3 server.py
Paths: /healthz, /users/<n>, /orders/<n>. The fields "ts" and "etag" change on
every call on purpose: replaygate should learn them as noise and ignore them.
"""
import http.server, json, os, time

PORT = int(os.environ.get("PORT", "3001"))


def user(n):
    return {"id": n, "name": f"user {n}", "age": 20 + n, "ts": time.time_ns(), "tags": ["a", "b"]}


def order(n):
    return {"id": n, "total": 10.0 * n, "etag": f"e{time.time_ns()}", "items": [{"sku": "x", "qty": 1}, {"sku": "y", "qty": 2}]}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = self.path.split("?")[0].strip("/").split("/")
        status, body = 200, None
        if parts == ["healthz"]:
            body = {"status": "ok"}
        elif len(parts) == 2 and parts[0] == "users" and parts[1].isdigit():
            body = user(int(parts[1]))
        elif len(parts) == 2 and parts[0] == "orders" and parts[1].isdigit():
            body = order(int(parts[1]))
        else:
            status, body = 404, {"error": "not found"}
        out = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


class Server(http.server.ThreadingHTTPServer):
    # The default listen backlog is 5: a burst of concurrent requests overflows
    # it and the OS retries the dropped connections after a full second.
    request_queue_size = 128


if __name__ == "__main__":
    Server(("127.0.0.1", PORT), Handler).serve_forever()
