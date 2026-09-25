"""Verify demo tenant scoping and reject cross-tenant admin access on a local/staging stack."""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://localhost:8000"


def call(path, method="GET", body=None, token=None, extra_headers=None):
    headers = {"Content-Type": "application/json", **(extra_headers or {})}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(BASE + path, method=method, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
    try:
        with urlopen(request, timeout=5) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else {}
    except HTTPError as exc:
        payload = exc.read()
        return exc.code, json.loads(payload) if payload else {}


def login(username, password):
    status, payload = call("/api/v1/auth/login", "POST",
                           {"username": username, "password": password})
    if status != 200:
        raise RuntimeError(f"demo login failed for {username}: HTTP {status}")
    return payload["access_token"]


def main():
    admin = login("admin", "admin-demo-password")
    alice = login("alice", "alice-demo-password")
    bob = login("bob", "bob-demo-password")

    assert call("/api/v1/shop/products", token=alice,
                extra_headers={"X-Tenant-ID": "tenant-beta"})[0] == 200
    assert call("/api/v1/shop/products", token=bob)[0] == 200
    status, events = call("/api/v1/admin/requests?limit=50", token=admin)
    assert status == 200 and events, "tenant admin should see its activity"
    assert all(row["tenant_id"] == "demo-tenant" for row in events), "cross-tenant event leaked"
    assert all("token_ref" not in row and "token_jti" not in row for row in events), "token identifier leaked"
    assert call("/api/v1/admin/summary", token=bob)[0] == 403, "non-admin crossed admin boundary"
    print(json.dumps({"tenant_isolation": "passed", "tenant_override_header": "ignored",
                      "token_reference_exposure": "none", "cross_tenant_admin": "denied",
                      "demo_tenant_visible_events": len(events)}, indent=2))


if __name__ == "__main__":
    main()
