"""Bounded authenticated gateway load smoke; run only in an authorized test tenant."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(url, method="GET", body=None, token=None, timeout=5):
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, method=method, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
    start = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
            return response.status, time.perf_counter() - start
    except HTTPError as error:
        error.read()
        return error.code, time.perf_counter() - start
    except (URLError, TimeoutError, OSError):
        return 0, time.perf_counter() - start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--rate", type=float, default=2, help="aggregate request starts per second")
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 1800 or not 0 < args.rate <= 100 or not 1 <= args.concurrency <= 100:
        parser.error("use 1–1800 seconds, 0–100 requests/sec, and 1–100 concurrent workers")

    token = os.getenv("GATEWAY_ACCESS_TOKEN")
    if not token:
        user = os.getenv("DEMO_USER", "alice")
        password = os.getenv("DEMO_PASSWORD", "alice-demo-password")
        req = Request(args.base_url + "/api/v1/auth/login", method="POST",
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({"username": user, "password": password}).encode())
        try:
            with urlopen(req, timeout=5) as response:
                token = json.loads(response.read())["access_token"]
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise SystemExit("Login failed. Set GATEWAY_ACCESS_TOKEN for an authorized test identity.") from exc

    count = int(args.seconds * args.rate)
    started = time.perf_counter()
    results, lock = [], threading.Lock()

    def hit(index):
        target = started + index / args.rate
        wait = target - time.perf_counter()
        if wait > 0:
            time.sleep(wait)
        result = request_json(args.base_url + "/api/v1/shop/products", token=token)
        with lock:
            results.append(result)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        list(pool.map(hit, range(count)))
    elapsed = time.perf_counter() - started
    statuses = Counter(status for status, _ in results)
    latencies = sorted(latency for _, latency in results)
    percentile = lambda p: round(latencies[min(len(latencies) - 1, int((len(latencies) - 1) * p))] * 1000, 2)
    print(json.dumps({"requests": len(results), "elapsed_seconds": round(elapsed, 2),
                      "achieved_rps": round(len(results) / elapsed, 2),
                      "status_counts": dict(statuses), "latency_ms": {
                          "p50": percentile(.50), "p95": percentile(.95),
                          "p99": percentile(.99), "max": round(max(latencies) * 1000, 2)},
                      "timeouts_or_transport_errors": statuses.get(0, 0)}, indent=2))


if __name__ == "__main__":
    main()
