"""Read-only, cookie-free HTTP audit. Never execute a hosting challenge.

Only derived observations are reported: no bodies, cookies, raw headers or
redirect query strings. This helper is intentionally outside the upload set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

HOST = "realitycheck.great-site.net"
ORIGIN = f"https://{HOST}"
POLICY_HEADERS = (
    "content-security-policy", "referrer-policy", "x-content-type-options",
    "x-frame-options", "strict-transport-security", "permissions-policy",
)
PROFILES = {
    "audit": "RealityCheck-Webcheck/1.0",
    "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
MAX_BODY = 512 * 1024


class PageIdentity(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = False
        self.canonicals = []
        self.application = False
        self.refresh = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical |= attrs.get("href", "").startswith(ORIGIN + "/")
            self.canonicals.append(attrs.get("href"))
        if tag == "script":
            self.application |= attrs.get("src", "").split("?")[0] == "scripts/core.js"
        if tag == "meta":
            self.refresh |= attrs.get("http-equiv", "").lower() == "refresh"


def classify(status, headers, body, expected_canonical=ORIGIN + "/"):
    """Ownership needs evidence; an ordinary 403 never proves an own rule."""
    headers = {key.lower(): value for key, value in headers.items()}
    lower = body.lower()
    identity = PageIdentity()
    identity.feed(body)
    if "/aes.js" in lower and "slowaes" in lower:
        kind = "hoster_js_challenge"
    elif status == 403 and headers.get("x-realitycheck-denial") == "hidden-path":
        kind = "project_htaccess_denial"
    elif status in (301, 302, 303, 307, 308):
        kind = "http_redirect"
    elif status == 200 and identity.canonical and identity.application:
        kind = "application"
    elif status in (401, 403, 429):
        kind = "access_denied_unknown_source"
    else:
        kind = "unexpected_response"
    result = {
        "kind": kind,
        "status": status,
        "project_policy_observed": headers.get("x-realitycheck-policy") == "apache-v1",
        "project_header_evaluation": None,
    }
    if kind == "application" and result["project_policy_observed"]:
        csp = headers.get("content-security-policy", "")
        directives = {}
        for directive in csp.split(";"):
            parts = directive.split()
            if parts:
                directives.setdefault(parts[0], parts[1:])
        result["project_header_evaluation"] = {
            "policy_fingerprint": hashlib.sha256(json.dumps(
                {key: " ".join(headers.get(key, "").split()) for key in POLICY_HEADERS},
                sort_keys=True,
            ).encode()).hexdigest(),
            "missing": [key for key in POLICY_HEADERS if not headers.get(key)],
            "referrer_compatible": headers.get("referrer-policy", "").strip() in ("same-origin", "strict-origin-when-cross-origin"),
            "inline_handlers_blocked": directives.get("script-src-attr") == ["'none'"],
            "frames_scoped": directives.get("frame-src") == ["'self'", "https://translate.google.com"],
            "canonical_matches": identity.canonicals == [expected_canonical],
            "client_redirect_detected": identity.refresh or bool(re.search(
                r"(?:window\.|document\.)?location\s*(?:\.\s*(?:href\s*=|replace\s*\(|assign\s*\()|=)",
                body, re.I)),
        }
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(url, user_agent, max_redirects=5):
    # No cookie processor, credentials, JavaScript or challenge bypass.
    opener = build_opener(NoRedirect())
    hops = []
    visited = set()
    for _ in range(max_redirects + 1):
        if url in visited:
            return {"hops": hops, "terminal": "redirect_loop"}
        visited.add(url)
        request = Request(url, headers={"User-Agent": user_agent, "Accept": "text/html"})
        try:
            try:
                response = opener.open(request, timeout=15)
            except HTTPError as error:
                response = error
            with response:
                headers = {key.lower(): value for key, value in response.headers.items()}
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    return {"hops": hops, "terminal": "response_too_large"}
                observation = classify(response.code, headers, body.decode("utf-8", "replace"),
                                       ORIGIN + urlsplit(url).path)
        except (URLError, TimeoutError, OSError, ValueError):
            # Exceptions may contain private proxy/network details; never print them.
            return {"hops": hops, "terminal": "network_error"}
        hops.append(observation)
        if observation["kind"] != "http_redirect":
            return {"hops": hops, "terminal": observation["kind"]}
        location = headers.get("location")
        if not location:
            return {"hops": hops, "terminal": "missing_redirect_location"}
        target = urljoin(url, location)
        try:
            parsed = urlsplit(target)
            port = parsed.port
        except ValueError:
            return {"hops": hops, "terminal": "external_or_unsafe_redirect"}
        # Do not contact third parties or follow unexpected credential-bearing URLs.
        if (parsed.scheme not in ("http", "https") or parsed.hostname != HOST
                or parsed.username or parsed.password or port not in (None, 80, 443)):
            return {"hops": hops, "terminal": "external_or_unsafe_redirect"}
        if urlsplit(url).scheme == "https" and parsed.scheme == "http":
            return {"hops": hops, "terminal": "https_downgrade"}
        observation["redirect_to_canonical_root"] = target == ORIGIN + "/"
        url = target
    return {"hops": hops, "terminal": "redirect_limit"}


def compare_profiles(results):
    """Observed differences suggest UA sensitivity; they do not prove causality."""
    return {
        path: {
            "user_agent_difference_observed": profiles["audit"] != profiles["browser"],
            "application_comparable": all(
                result["terminal"] == "application" and bool(result["hops"][-1]["project_header_evaluation"])
                for result in profiles.values()
            ),
        }
        for path, profiles in results.items()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-user-agent", default=PROFILES["audit"],
                        help="Use the exact central Webcheck UA; never include credentials.")
    args = parser.parse_args()
    profiles = {**PROFILES, "audit": args.audit_user_agent}
    targets = {"https_root": ORIGIN + "/", "https_index": ORIGIN + "/index.html",
               "http_root": f"http://{HOST}/",
               "http_index": f"http://{HOST}/index.html",
               "https_countries": ORIGIN + "/countries.html",
               "http_countries": f"http://{HOST}/countries.html"}
    for page in ("world.html", "overall_ranking_countries.html", "analysis.html",
                 "about.html", "data_glossary.html", "impressum.html", "privacy.html"):
        targets[page] = ORIGIN + "/" + page
    results = {
        name: {profile: probe(url, ua) for profile, ua in profiles.items()}
        for name, url in targets.items()
    }
    report = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "comparison": compare_profiles(results),
        "interpretation": "Only identified application replies with the project policy marker evaluate project headers. Hoster challenges, denials and unknown policy sources remain inconclusive. "
                          "UA differences are observations, not proof of a UA rule.",
    }
    print(json.dumps(report, indent=2))
    if not all(item["application_comparable"] for item in report["comparison"].values()):
        return 2  # Inconclusive must never become a green security report.
    for target_name, profiles_for_target in results.items():
        for result in profiles_for_target.values():
            expected_hops = 2 if target_name in {"http_root", "http_index", "https_index", "http_countries", "https_countries"} else 1
            evaluation = result["hops"][-1]["project_header_evaluation"]
            if (not evaluation["canonical_matches"] or evaluation["missing"] or not evaluation["referrer_compatible"]
                    or not evaluation["inline_handlers_blocked"]
                    or not evaluation["frames_scoped"] or evaluation["client_redirect_detected"]
                    or len(result["hops"]) != expected_hops
                    or (expected_hops == 2 and not result["hops"][0].get("redirect_to_canonical_root"))):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
