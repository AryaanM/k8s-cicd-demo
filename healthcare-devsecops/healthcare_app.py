import hmac
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

APP_VERSION = os.getenv("APP_VERSION", "v1.0-secure")

PATIENT_RECORDS = [
    {
        "patient_id": "MED-9041",
        "full_name": "Rohan Verma",
        "ssn_masked": "***-**-4821",
        "diagnosis_code": "I10 (Hypertension)",
        "ward": "Cardiology-B",
    },
    {
        "patient_id": "MED-9042",
        "full_name": "Ananya Nair",
        "ssn_masked": "***-**-7390",
        "diagnosis_code": "J45 (Asthma)",
        "ward": "Pulmonology-A",
    },
]

class HealthcareEHRHandler(BaseHTTPRequestHandler):
    def _send_secure_json(self, status_code, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_authorized(self):
        configured_token = os.getenv("EHR_API_TOKEN", "")
        provided_token = self.headers.get("X-API-Key", "")
        if not configured_token or not provided_token:
            return False
        return hmac.compare_digest(configured_token, provided_token)

    def do_GET(self):
        if self.path == "/health":
            self._send_secure_json(200, {
                "service": "healthcare-ehr-api",
                "status": "HEALTHY",
                "version": APP_VERSION,
                "compliance_mode": "HIPAA-RBAC-PHI-MASKED",
                "pod_hostname": socket.gethostname(),
            })
        elif self.path == "/api/ehr/patients":
            if not self._is_authorized():
                self._send_secure_json(401, {
                    "error": "Unauthorized",
                    "detail": "Valid X-API-Key clinical credential required to access PHI records.",
                })
                return
            self._send_secure_json(200, {
                "version": APP_VERSION,
                "phi_redaction": "ENFORCED",
                "records": PATIENT_RECORDS,
            })
        else:
            self._send_secure_json(404, {"error": "Endpoint Not Found"})

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5000), HealthcareEHRHandler).serve_forever()
