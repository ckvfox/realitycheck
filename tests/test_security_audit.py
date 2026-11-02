"""Keep hosting responses out of project security scores."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import security_audit as audit

PAGE = '<link rel="canonical" href="https://realitycheck.great-site.net/">' \
       '<script src="scripts/core.js?v=test"></script>'


class SecurityAuditTests(unittest.TestCase):
    def test_hoster_challenge_takes_precedence_over_headers(self):
        result = audit.classify(200, {"X-RealityCheck-Policy": "apache-v1"},
                                '<script src="/aes.js"></script>slowAES' + PAGE)
        self.assertEqual(result["kind"], "hoster_js_challenge")
        self.assertIsNone(result["project_header_evaluation"])

    def test_unknown_policy_cannot_be_scored_as_project(self):
        result = audit.classify(200, {}, PAGE)
        self.assertEqual(result["kind"], "application")
        self.assertIsNone(result["project_header_evaluation"])

    def test_denials_require_ownership_evidence(self):
        self.assertEqual(audit.classify(403, {}, "")["kind"], "access_denied_unknown_source")
        result = audit.classify(403, {"X-RealityCheck-Denial": "hidden-path"}, "")
        self.assertEqual(result["kind"], "project_htaccess_denial")
        self.assertIsNone(result["project_header_evaluation"])

    def test_application_checks_use_only_identified_project_response(self):
        result = audit.classify(200, {"X-RealityCheck-Policy": "apache-v1"}, PAGE)
        self.assertTrue(result["project_header_evaluation"]["canonical_matches"])
        self.assertIn("content-security-policy", result["project_header_evaluation"]["missing"])
        redirected = audit.classify(200, {"X-RealityCheck-Policy": "apache-v1"},
                                    PAGE + '<script>location.replace("/")</script>')
        self.assertTrue(redirected["project_header_evaluation"]["client_redirect_detected"])

    def test_ua_difference_does_not_imply_comparable_application(self):
        result = {"terminal": "hoster_js_challenge", "hops": []}
        comparison = audit.compare_profiles({"root": {"audit": result, "browser": result}})
        self.assertFalse(comparison["root"]["application_comparable"])
        self.assertFalse(comparison["root"]["user_agent_difference_observed"])

    def test_redirect_loop_and_external_target_are_not_followed(self):
        class Response:
            code = 301
            headers = {"Location": "https://other.example/"}
            def read(self, limit): return b""
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch.object(audit, "build_opener") as opener:
            opener.return_value.open.return_value = Response()
            result = audit.probe(audit.ORIGIN + "/", "test")
            self.assertEqual(result["terminal"], "external_or_unsafe_redirect")
            opener.return_value.open.assert_called_once()
            Response.headers = {"Location": "/"}
            result = audit.probe(audit.ORIGIN + "/", "test")
            self.assertEqual(result["terminal"], "redirect_loop")
