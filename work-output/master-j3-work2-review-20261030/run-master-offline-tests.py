"""MASTER offline test runner. Dependency import shims only; network/processes denied.
Requests/google-auth are absent in this host. They are not functionality under test.
No repository source or test body is modified. Real credentials are never loaded.
"""
import contextlib
import io
import json
import socket
import subprocess
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
blocked = []

def deny(*args, **kwargs):
    blocked.append("unmocked external effect")
    raise AssertionError("Offline review: unmocked network/provider/subprocess forbidden")

requests = types.ModuleType("requests")
requests.RequestException = type("RequestException", (Exception,), {})
for key in ("get", "post", "put", "delete", "request", "Session"):
    setattr(requests, key, deny)
sys.modules["requests"] = requests
for name in ("google", "google.auth", "google.auth.transport", "google.auth.transport.requests"):
    module = types.ModuleType(name)
    module.__path__ = []
    sys.modules[name] = module
sys.modules["google.auth"].default = deny
sys.modules["google.auth.transport.requests"].Request = deny
socket.socket.connect = deny
socket.create_connection = deny
subprocess.run = deny
subprocess.Popen = deny

suite = unittest.defaultTestLoader.loadTestsFromNames([
    "test_facebook_signoff_integration",
    "test_facebook_global_audio",
    "test_facebook_global_visuals",
])
log = io.StringIO()
stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
payload = {
    "kind": "offline_fixture_tests_with_explicit_import_shims",
    "code_ref": "8e4d5451737e816fc4c2c91badbb9f0f6af625e8",
    "python": sys.version.split()[0],
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "passed": result.wasSuccessful(),
    "dependency_shims": ["requests", "google.auth"],
    "external_effect_guard_hits": blocked,
    "real_media_auth_provider_windows_acceptance": False,
    "log": log.getvalue(),
    "fixture_stdout": stdout.getvalue(),
}
(ROOT / "master-offline-tests.json").write_text(json.dumps(payload, indent=2)+"\n")
print(log.getvalue())
print(json.dumps({k:v for k,v in payload.items() if k not in ("log","fixture_stdout")}, indent=2))
sys.exit(0 if result.wasSuccessful() and not blocked else 1)
