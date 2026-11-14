import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from healthcare_app import HealthcareEHRHandler

class TestHealthcareDevSecOps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["EHR_API_TOKEN"] = "ci-ephemeral-clinical-token"
        cls.server = HTTPServer(("127.0.0.1", 0), HealthcareEHRHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_unauthenticated_phi_access_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/ehr/patients")
        self.assertEqual(ctx.exception.code, 401)
        ctx.exception.close()

    def test_authorized_phi_redaction_and_security_headers(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/ehr/patients",
            headers={"X-API-Key": "ci-ephemeral-clinical-token"},
        )
        with urllib.request.urlopen(req) as res:
            self.assertEqual(res.status, 200)
            self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
            self.assertIn("no-store", res.headers.get("Cache-Control", ""))
            data = json.loads(res.read().decode())
            self.assertEqual(data["phi_redaction"], "ENFORCED")
            self.assertTrue(data["records"][0]["ssn_masked"].startswith("***-**-"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
