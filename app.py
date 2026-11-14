import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

APP_VERSION = os.getenv("APP_VERSION", "v1.0")

class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            payload = {"status": "UP", "version": APP_VERSION}
        else:
            payload = {
                "application": "Task1-Kubernetes-CICD-Demo",
                "version": APP_VERSION,
                "pod_hostname": socket.gethostname(),
            }
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5000), AppHandler).serve_forever()
