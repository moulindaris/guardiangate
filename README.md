# Context-Aware Zero-Trust API Gateway

Runnable local MVP for the project plan. It evaluates protected requests using JWT validation, recent behavioral features, domain-aware rules, a shared Isolation Forest, a configurable risk action, MongoDB events, and a React security console.

> **Demo only:** synthetic identities and API behavior; payment endpoint accepts no payment data. The default credentials and compose secret are development-only. Do not expose this setup to the internet or use it for production enforcement.

## Start locally with Docker Compose

1. Install Docker Desktop with Compose enabled.
2. From the project root, run:

   ```powershell
   docker compose up --build
   ```

   The first backend image build installs Python dependencies, creates the 10,000-row synthetic dataset in the image build context, and trains the demo Isolation Forest. This can take a few minutes.
3. Open [http://localhost:5173](http://localhost:5173) for the dashboard and [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.
4. In the dashboard choose **Connect demo console**. It logs in with the local admin account.
5. Click **Run normal activity**, then **Simulate payment abuse**. The payment burst creates a critical event and revokes Alice's token. Click **Replay revoked token** to see the next request rejected.

Stop with `Ctrl+C`; `docker compose down` stops the services. Use `docker compose down -v` only when you intentionally want to delete the local demo database.

## Demo accounts

| Username | Default local password | Role |
|---|---|---|
| `admin` | `admin-demo-password` | Security dashboard |
| `alice` | `alice-demo-password` | Protected API calls |

Passwords can be changed with environment variables. Copy `.env.example` to `.env` before starting to override them. Set a long random `JWT_SECRET` for any shared environment. Never commit `.env`.

## Endpoints

- `POST /api/v1/auth/login` — JSON `{"username":"alice","password":"alice-demo-password"}`; returns a bearer token.
- Protected examples: `GET /api/v1/shop/products`, `POST /api/v1/shop/cart`, `POST /api/v1/payments/charge?simulate_failure=true`, `GET /api/v1/travel/search`, `POST /api/v1/travel/bookings`, `POST /api/v1/rides/request`.
- Admin endpoints (admin bearer token): `GET /api/v1/admin/summary`, `/requests`, `/events`, `/revoked-tokens`.
- `GET /health/live` and `/health/ready` provide liveness and Mongo readiness.

The synthetic payment route can simulate a decline with `simulate_failure=true`; it never reads or stores a card number or other payment credential.

## Generate gateway behavior telemetry

With the local stack running, use `python scripts/behavior_traffic.py --requests 300 --profile mixed --delay-ms 20` to sign in through the demo login endpoint and send authenticated, varied API traffic through the gateway. The script uses gateway-issued short-lived JWTs (it does not fabricate or print tokens), and the events are recorded in the configured `gateway_telemetry.api_requests` collection. Use `--profile normal` for varied activity or `--profile burst` for rapid repeated calls. If your demo password differs from the default, set `DEMO_PASSWORD` in the shell before running it. The default target is localhost; non-local targets require `--allow-remote` and must be an authorized staging system. This creates telemetry, not labeled ground-truth training data. In the current Compose setup, enforcement may block or revoke a token during burst traffic; use a shadow policy for classifier observation.

The generated training dataset is at [`ml/dataset/synthetic_sessions.csv`](ml/dataset/synthetic_sessions.csv) after running `python scripts/generate_dataset.py`; it contains 10,000 synthetic behavior sessions. It is ignored by Git so it can be regenerated and uploaded separately to Colab. For training, use the eight behavior feature columns; exclude `session_id`, `label_anomaly`, and `synthetic_scenario` from model inputs. Keep labels for evaluation only.

## Project layout

- `backend/app/` — gateway middleware, JWT auth, MongoDB, behavior features, rules, risk and APIs.
- `ml/training/` — Isolation Forest training pipeline.
- `scripts/generate_dataset.py` — deterministic synthetic dataset generator.
- `frontend/` — React security operations console.
- `docker-compose.yml` — local API, dashboard and MongoDB services.
- `PROJECT_PLAN.md` — larger 100-person program plan, rollout gates and production-oriented target architecture.

## Detection behavior

The current demo uses a five-minute, tenant-scoped behavioral window, a shared Isolation Forest, general velocity/repeated-endpoint rules, and payment/travel/ride rules. Payment abuse is deliberately deterministic: four repeated declined payment attempts trigger `payment_critical_burst`, block the current request, create an alert, and revoke a keyed reference to that JWT `jti`. User identities and token identifiers are pseudonymized before activity storage. The score thresholds and anomaly-score mapping are demonstration configuration; the anomaly score is not a probability and no real-world accuracy is claimed.

The ML generator outputs 10,000 synthetic session rows, with labels kept separate from model features. The model is trained using synthetic normal rows. The container generates its own copy at image build; the workspace CSV can be generated separately for Colab.

## Important implementation boundaries

The local stack still uses one API process and a single Mongo container. The repository now includes tenant-scoped storage, OIDC/JWKS validation, second-person policy approval, shadow/canary modes, privacy retention, metrics, and a Kubernetes high-availability template. Durable event streaming, provider-specific secret/KMS and ingress integration, managed database failover, a full console approval workflow, and measured production load/resilience evidence still require the target environment. See [Production Readiness](docs/PRODUCTION_READINESS.md).

The system applies Zero Trust principles to continuous behavioral evaluation; it is not a complete implementation of the NIST Zero Trust Architecture.
