"""Pytest configuration and fixtures for functional tests."""

import json
import logging
import os
import time

import pytest
import requests

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTP call capture
# ---------------------------------------------------------------------------

class _HttpCall:
    """Record of a single HTTP request/response pair."""

    def __init__(self, method: str, url: str, kwargs: dict, response: requests.Response):
        self.method = method
        self.url = url
        self.kwargs = kwargs
        self.response = response

    def _fmt_headers(self, headers: dict, indent: str = "    ") -> str:
        return "\n".join(f"{indent}{k}: {v}" for k, v in headers.items())

    def _fmt_body(self, body, indent: str = "    ") -> str:
        if body is None:
            return f"{indent}(none)"
        if isinstance(body, (dict, list)):
            return "\n".join(
                f"{indent}{line}" for line in json.dumps(body, indent=2).splitlines()
            )
        text = str(body)
        if len(text) > 2000:
            text = text[:2000] + "… (truncated)"
        return "\n".join(f"{indent}{line}" for line in text.splitlines())

    def _response_body(self) -> str:
        try:
            return self.response.json()
        except Exception:
            return self.response.text or "(empty)"

    def format(self) -> str:
        req_headers = dict(self.response.request.headers) if self.response.request else {}
        req_body_raw = self.response.request.body if self.response.request else None
        try:
            req_body = json.loads(req_body_raw) if isinstance(req_body_raw, (str, bytes)) and req_body_raw else req_body_raw
        except Exception:
            req_body = req_body_raw

        lines = [
            "─" * 60,
            f"  {self.method.upper()} {self.url}",
            "─" * 60,
            "  REQUEST HEADERS",
            self._fmt_headers(req_headers),
            "  REQUEST BODY",
            self._fmt_body(req_body),
            "",
            f"  RESPONSE  HTTP {self.response.status_code}",
            "  RESPONSE HEADERS",
            self._fmt_headers(dict(self.response.headers)),
            "  RESPONSE BODY",
            self._fmt_body(self._response_body()),
            "─" * 60,
        ]
        return "\n".join(lines)


# Per-test call log — populated by the instrumented clients
_current_calls: list[_HttpCall] = []


def _record(method: str, url: str, kwargs: dict, response: requests.Response) -> requests.Response:
    call = _HttpCall(method, url, kwargs, response)
    _current_calls.append(call)
    log.info("%s %s → HTTP %s", method.upper(), url, response.status_code)
    return response


# ---------------------------------------------------------------------------
# Pytest hooks
# ---------------------------------------------------------------------------

def pytest_runtest_setup(item):
    _current_calls.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed and _current_calls:
        sections = []
        for i, http_call in enumerate(_current_calls, 1):
            sections.append(f"HTTP call #{i}\n{http_call.format()}")
        report.sections.append(("HTTP traffic", "\n\n".join(sections)))


# ---------------------------------------------------------------------------
# URL fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def root_app_url() -> str:
    return os.environ.get("ROOT_APP_URL", "http://localhost:5001")


@pytest.fixture(scope="session")
def leaf_api_url() -> str:
    return os.environ.get("LEAF_API_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def mock_anthropic_url() -> str:
    return os.environ.get("MOCK_ANTHROPIC_URL", "http://localhost:8082")


# ---------------------------------------------------------------------------
# Service readiness
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def wait_for_services(root_app_url: str, leaf_api_url: str, mock_anthropic_url: str) -> None:
    services = [
        ("Root App", root_app_url),
        ("Leaf API", leaf_api_url),
        ("Mock Anthropic", mock_anthropic_url),
    ]

    for name, url in services:
        for attempt in range(30):
            try:
                resp = requests.get(f"{url}/health", timeout=2)
                if resp.status_code == 200:
                    log.info("✓ %s is ready", name)
                    break
            except requests.RequestException:
                if attempt < 29:
                    time.sleep(1)
                else:
                    raise RuntimeError(f"{name} ({url}) failed to start")

    try:
        routes_resp = requests.get(f"{root_app_url}/_routes", timeout=2)
        if routes_resp.status_code == 200:
            routes = routes_resp.json()
            log.info("Root App routes: %s", [r["rule"] for r in routes])
    except Exception as exc:
        log.warning("Could not fetch route list: %s", exc)


# ---------------------------------------------------------------------------
# Instrumented HTTP clients
# ---------------------------------------------------------------------------

class RootAppClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("GET", url, kwargs, requests.get(url, **kwargs))

    def post(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("POST", url, kwargs, requests.post(url, **kwargs))

    def head(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("HEAD", url, kwargs, requests.head(url, **kwargs))


class LeafApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("GET", url, kwargs, requests.get(url, **kwargs))

    def post(self, path: str, data=None, json=None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("POST", url, {"data": data, "json": json, **kwargs},
                       requests.post(url, data=data, json=json, **kwargs))

    def head(self, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        return _record("HEAD", url, kwargs, requests.head(url, **kwargs))


@pytest.fixture(scope="session")
def root_client(root_app_url: str, wait_for_services: None) -> RootAppClient:
    return RootAppClient(root_app_url)


@pytest.fixture(scope="session")
def leaf_client(leaf_api_url: str, wait_for_services: None) -> LeafApiClient:
    return LeafApiClient(leaf_api_url)
