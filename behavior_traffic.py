#!/usr/bin/env python3
"""Generate authorized demo API traffic through the gateway for telemetry demos.

Uses the gateway's login endpoint to mint short-lived demo JWTs; it never
constructs tokens itself and never prints credentials or bearer tokens.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


ROUTES = [
    ("GET", "/api/v1/shop/products", "normal"),
    ("POST", "/api/v1/shop/cart", "normal"),
    ("GET", "/api/v1/travel/search", "normal"),
    ("POST", "/api/v1/travel/bookings", "normal"),
    ("POST", "/api/v1/rides/request", "normal"),
    ("POST", "/api/v1/rides/location", "normal"),
    ("POST", "/api/v1/payments/charge", "normal"),
]


@dataclass
class GatewayClient:
    base_url: str
    token: str

    def request(self, method: str, path: str) -> tuple[int, dict[str, str]]:
        url = self.base_url + path
        request = urllib.request.Request(
            url,
            data=b"" if method == "POST" else None,
            method=method,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response.read()
                return response.status, dict(response.headers.items())
        except urllib.error.HTTPError as error:
            error.read()
            return error.code, dict(error.headers.items())


def login(base_url: str, username: str, password: str) -> GatewayClient:
    payload = json.dumps({"username": username, "password": password}).encode()
    request = urllib.request.Request(
        base_url + "/api/v1/auth/login",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Gateway login failed ({type(error).__name__}); check URL and demo credentials") from None
    token = data.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Gateway login response did not contain an access token")
    return GatewayClient(base_url, token)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="gateway base URL (default: local gateway)")
    parser.add_argument("--requests", type=int, default=200, help="number of API events to send (1-5000)")
    parser.add_argument("--profile", choices=("normal", "burst", "mixed"), default="normal",
                        help="normal varied use, rapid repeated calls, or mostly normal with brief bursts")
    parser.add_argument("--delay-ms", type=int, default=80,
                        help="normal-profile delay between calls; mixed bursts ignore delay briefly")
    parser.add_argument("--user", default=os.getenv("DEMO_USER", "alice"), help="demo user to log in as")
    parser.add_argument("--allow-remote", action="store_true",
                        help="allow sending traffic to a non-local host; use only on an authorized staging gateway")
    args = parser.parse_args()

    if not 1 <= args.requests <= 5000:
        parser.error("--requests must be between 1 and 5000")
    if not 0 <= args.delay_ms <= 5000:
        parser.error("--delay-ms must be between 0 and 5000")
    parsed = urllib.parse.urlparse(args.url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        parser.error("--url must be an http(s) URL")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.hostname not in local_hosts and not args.allow_remote:
        parser.error("remote targets require --allow-remote and explicit authorization")
    base_url = args.url.rstrip("/")

    try:
        password = os.getenv("DEMO_PASSWORD", "alice-demo-password")
        client = login(base_url, args.user, password)
        print(f"Authenticated to {base_url} as demo user {args.user}; token omitted.")
        started = time.monotonic()
        counts: dict[int, int] = {}
        actions: dict[str, int] = {}
        model_states: dict[str, int] = {}
        selected_route: tuple[str, str] | None = None
        burst_length = 0
        for index in range(args.requests):
            if args.profile == "burst":
                # Repeating one endpoint creates concentrated history for this token session.
                selected_route = selected_route or ("GET", "/api/v1/shop/products")
                method, path = selected_route
            elif args.profile == "mixed" and (index % 40) >= 32:
                method, path = "GET", "/api/v1/shop/products"
                burst_length += 1
            else:
                method, path, _ = random.choice(ROUTES)
                burst_length = 0

            status, headers = client.request(method, path)
            counts[status] = counts.get(status, 0) + 1
            action = next((value for key, value in headers.items() if key.lower() == "x-security-action"), None)
            model_state = next((value for key, value in headers.items() if key.lower() == "x-behavior-model"), None)
            if action:
                actions[action] = actions.get(action, 0) + 1
            if model_state:
                model_states[model_state] = model_states.get(model_state, 0) + 1
            if status in (401, 403):
                print(f"Stopped at request {index + 1}: gateway returned HTTP {status}; token may be blocked/revoked.")
                break
            if status >= 500:
                print(f"Stopped at request {index + 1}: gateway returned HTTP {status}.")
                break
            if args.delay_ms and args.profile != "burst" and not (args.profile == "mixed" and burst_length):
                time.sleep(args.delay_ms / 1000)

        elapsed = max(time.monotonic() - started, 0.001)
        total = sum(counts.values())
        print(f"Sent {total} gateway requests in {elapsed:.1f}s ({total / elapsed:.1f} req/s).")
        print("HTTP statuses: " + ", ".join(f"{code}: {count}" for code, count in sorted(counts.items())))
        if actions:
            print("Gateway actions: " + ", ".join(f"{name}: {count}" for name, count in sorted(actions.items())))
        if model_states:
            print("Behavior model: " + ", ".join(f"{name}: {count}" for name, count in sorted(model_states.items())))
        print("Inspect the gateway_telemetry.api_requests collection for these events.")
        return 0 if total == args.requests else 1
    except (RuntimeError, urllib.error.URLError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
