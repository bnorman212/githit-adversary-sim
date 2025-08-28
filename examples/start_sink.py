from http.server import BaseHTTPRequestHandler, HTTPServer

class Sink(BaseHTTPRequestHandler):
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', '0'))
        data = self.rfile.read(ln)
        print(f"[SINK] Received {len(data)} bytes at {self.path} from {self.client_address[0]}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    host, port = "0.0.0.0", 8080
    print(f"[SINK] Listening on http://{host}:{port}")
    HTTPServer((host, port), Sink).serve_forever()
