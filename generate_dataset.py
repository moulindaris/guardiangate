"""Generate a reproducible, clearly synthetic session dataset."""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
FEATURES = ["requests_per_minute", "endpoint_frequency", "unique_endpoints",
            "payload_bytes", "failed_ratio", "mean_interarrival_seconds",
            "session_duration_seconds", "domain_intensity"]
DOMAINS = np.array([0.5, 0.8, 1.0, 1.1, 1.3])


def generate(rows: int = 10_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    anomaly_count = int(rows * 0.30)
    normal_count = rows - anomaly_count

    def sample(n, anomalous=False):
        domain = rng.choice(DOMAINS, n)
        if anomalous:
            kind = rng.integers(0, 4, n)
            rpm = np.where(kind == 0, rng.uniform(65, 180, n), rng.poisson(8, n))
            endpoint = np.where(kind == 1, rng.integers(15, 60, n), rng.poisson(2.5, n))
            unique = np.where(kind == 2, rng.integers(10, 30, n), rng.integers(1, 7, n))
            payload = rng.lognormal(6, 1.1, n)
            failure = np.where(kind == 3, rng.uniform(.55, 1, n), rng.beta(2, 8, n))
            interval = np.where(kind == 0, rng.uniform(.1, .8, n), rng.lognormal(2.1, .9, n))
            duration = rng.lognormal(3.2, 1, n)
        else:
            rpm = rng.poisson(4, n)
            endpoint = rng.poisson(2, n) + 1
            unique = rng.integers(1, 5, n)
            payload = rng.lognormal(5, .8, n)
            failure = rng.beta(1, 20, n)
            interval = rng.lognormal(2.7, .7, n)
            duration = rng.lognormal(3.2, .9, n)
        data = np.column_stack([rpm, endpoint, unique, payload, failure,
                                interval, duration, domain])
        return data

    values = np.vstack([sample(normal_count), sample(anomaly_count, True)])
    labels = np.r_[np.zeros(normal_count, dtype=int), np.ones(anomaly_count, dtype=int)]
    scenarios = np.r_[np.full(normal_count, "normal"),
                      rng.choice(["velocity_abuse", "credential_abuse",
                                  "sequence_deviation", "domain_abuse"], anomaly_count)]
    permutation = rng.permutation(rows)
    result = pd.DataFrame(values[permutation], columns=FEATURES)
    result.insert(0, "synthetic_scenario", scenarios[permutation])
    result.insert(0, "label_anomaly", labels[permutation])
    result.insert(0, "session_id", [f"synthetic-{i:05d}" for i in range(rows)])
    return result


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "ml" / "dataset" / "synthetic_sessions.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate().to_csv(out, index=False)
    print(f"Wrote 10,000 synthetic records to {out}")
