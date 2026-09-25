# Zero-Trust API Gateway with Context-Aware Behavioral Anomaly Detection

**Implementation plan for a 100-person senior engineering organization**  
**Program scope:** a production-oriented, multi-tenant API security platform delivered in controlled releases, with a demonstrable initial slice and a staged path to high availability and scale.  
**Important:** thresholds and performance goals are hypotheses until validated against representative traffic and an explicit service-level objective (SLO).

## 1. Project Overview

Build an API security platform that checks each authenticated request against identity controls and the caller's recent behavior. It extracts context-aware features, evaluates configurable domain policies and shared anomaly models, converts the results into a transparent risk decision, and allows, challenges, rate-limits, blocks, or revokes accordingly. A React security operations console shows request activity, risk decisions, alerts, investigations, and revocation state.

The first release proves the core path: valid token, normal activity, behavioral change, anomaly and risk increase, block, token revocation, rejected token reuse, and dashboard evidence. The 100-person organization delivers this through product, platform, security, data/ML, SRE, quality, and governance workstreams; it should not put 100 people on one codebase or one undifferentiated backlog.

## 2. Problem Statement

A signed, unexpired token proves that a credential was issued; it does not prove that each later request is expected. A stolen token may be replayed by someone who can pass ordinary JWT validation. Static rate limits can catch volume but miss meaningful changes such as a payment-heavy sequence after ordinary browsing, repeated route changes in travel searches, or a sudden burst of ride requests.

The initial release addresses this gap by reevaluating behavior after authentication and interpreting activity in the context of the API domain. Subsequent releases must validate detection quality, resilience, privacy, operational processes, and safe enforcement before broad production rollout.

## 3. Proposed Solution

Place an edge/gateway enforcement tier in front of protected APIs. Validate identity and authorization, map requests to an API/domain policy, obtain bounded behavioral features, evaluate policy rules and shared anomaly services, and apply a versioned risk policy. Separate the synchronous decision path from durable event streaming and analytics, while defining what happens under partial dependency failure. Begin in shadow/monitor mode, compare decisions against labeled and analyst-reviewed outcomes, and graduate policies through canary enforcement. High-risk requests may be blocked; critical-risk requests may be blocked and credentials revoked according to approved policy. Step-up challenges and tenant-specific controls are production capabilities, not assumed behavior from the initial demo.

Keep interfaces explicit and versioned. The inline path should have a hard latency budget and bounded dependencies; event ingestion, historical analytics, dashboards, and training should be asynchronous. Platform architects must own failure modes, backpressure, idempotency, and compatibility from the first design review.

## 4. Innovation

**Innovation statement:** “A context-aware Zero-Trust API Gateway that continuously evaluates authenticated users based on domain-specific behavioral patterns and combines rule-based detection with ML-based anomaly detection to dynamically adjust API access.”

The product contribution is the integration of domain-aware profiles with reusable detection, explainable risk decisions, graduated enforcement, and an operator feedback loop. JWT validation, Isolation Forest, behavioral analytics, dashboards, and revocation are established techniques; differentiation is in safe integration, policy tuning, domain extensibility, and operational evidence. Do not claim a new ML algorithm.

## 5. System Architecture

```text
Client / demo script
        |
        v
FastAPI gateway ── JWT + revocation check ── domain/route mapping
        |                                      |
        |                                  protected API
        v
Recent request history ── feature extraction ── domain rules
                                                   |
                                       shared Isolation Forest
                                                   |
                                      risk score + policy decision
                                         /         |          \
                                      allow      monitor    block/revoke
                                         \         |          /
                                       MongoDB: requests, features,
                                       scores, events, alerts, tokens
                                                   |
                                          React dashboard API
```

**Request sequence:** (1) validate JWT and check `jti` revocation; (2) resolve configured domain and endpoint label; (3) obtain bounded rolling-window features; (4) run rules and model within the inline decision budget; (5) calculate risk and select action; (6) durably enqueue the decision event with an idempotency key; (7) execute the endpoint only if policy permits. If identity, feature, model, or event dependencies fail, apply an explicitly approved route/tenant fallback policy and emit an operational signal; never silently skip evaluation. Health and login routes have separately defined controls.

## 6. Domain-Specific Behavioral Profiles

Use a governed common feature contract and shared model families, with domain profiles supplying route labels, feature transforms, policy thresholds, and calibrations. Prefer pooled models with domain context; authorize separate models only when evaluation shows a material benefit and sufficient data. Feature and model owners publish compatibility/version policy.

| Domain | Typical route sequence | Context features / suspicious change |
|---|---|---|
| E-commerce/payment | `product_view → cart_add → checkout → payment` | payment attempts per 5 min, failed-payment ratio, checkout-after-browse ratio, repeated payment endpoint, unusual sequence |
| Travel | `flight_search → result_view → select → booking` | searches per 5 min, distinct origin/destination pairs, route-change ratio, bookings per 30 min, sequence deviation |
| Ride sharing | `location_update → ride_search → ride_request → payment` | ride requests per 5 min, location jump indicator (synthetic coordinates only), search-to-request ratio, payment failures |
| Authentication | `login → token_issue → refresh → API use` | failed logins, token issues/refreshes per window, token changes per user, endpoint mix immediately after login |

Profiles are configuration (JSON/YAML or Python settings) with versioned thresholds. Route labels are explicit; do not infer semantics from arbitrary user-provided paths. Include a neutral `general` profile for unknown configured routes.

## 7. 100-Person Organization and Workstream Ownership

| Workstream | Approx. staffing | Accountable scope and interfaces |
|---|---:|---|
| Product, program, architecture | 8 | Product management, program management, enterprise/security architecture, domain owners; roadmap, requirements, architecture decision records, dependency and risk management |
| Gateway and API integrations | 14 | Gateway data plane, control plane integration, adapters/SDK, identity integration, route/domain registry, policy enforcement |
| Identity and access security | 8 | OIDC/JWT validation, authorization, key rotation, session/token revocation, step-up integration, abuse controls |
| Behavioral data and feature platform | 12 | Event contracts, ingestion, stream/window processing, feature registry, profile lifecycle, data quality and retention |
| Detection science and ML engineering | 12 | Synthetic and approved real-data pipelines, model training/evaluation, model serving, drift/quality monitoring, model governance |
| Risk policy and response | 8 | Rule authoring, score calibration, policy simulation, enforcement modes, response orchestration and auditability |
| Console and analyst workflows | 10 | React console, investigation views, alert triage, policy operations, role-based access and accessibility |
| Platform, SRE, and cloud infrastructure | 12 | CI/CD, runtime platform, capacity, observability, SLOs, disaster recovery, cloud/network/IaC and cost controls |
| Quality engineering and performance | 8 | Contract/integration suites, load/fault testing, release qualification, test environments and evidence |
| Privacy, threat modeling, governance | 8 | Privacy impact, data minimization, threat modeling, secure SDLC, compliance mapping, red-team and release gates |
| **Total** | **100** | Named workstream leads report through a program leadership group; squads of 5–10 own bounded services and outcomes. |

Establish a small architecture council (gateway, identity, data, ML, SRE, product/security) that approves cross-cutting contracts and exceptions. Each workstream has a technical lead, product/requirements counterpart, on-call owner where applicable, and measurable exit criteria. Keep teams autonomous behind versioned APIs and schemas; avoid a 100-person shared sprint team.

Member 1 owns the gateway skeleton; all members agree on shared schemas in week 1. Member 2 and 3 define feature names together before model training. Member 4 defines the decision contract with Member 1 before automatic revocation is wired. Member 5 integrates against mocked JSON early, then switches to the real API.

## 8. Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | Issue a short-lived signed JWT after demo login; include `sub`, `jti`, `iat`, `exp`, and configured `iss`/`aud`. |
| FR-02 | Validate token signature and claims on protected routes; reject expired, malformed, wrong-issuer/audience, and revoked tokens. |
| FR-03 | Intercept protected requests and assign domain and stable endpoint labels from gateway configuration. |
| FR-04 | Record request metadata and outcome without storing authorization headers, secrets, or raw payment credentials. |
| FR-05 | Calculate rolling behavioral features using user/token/domain history and current request. |
| FR-06 | Run configurable domain rules and the shared Isolation Forest; retain separate outputs and reasons. |
| FR-07 | Calculate bounded risk score and choose allow, monitor, block, or revoke-and-block from configurable policy. |
| FR-08 | Persist security events, alerts, revoked credential identifiers, and model/policy versions; provide idempotent event ingestion and audit history. |
| FR-09 | Provide authenticated dashboard endpoints for aggregate counts, time-series activity, alerts, requests, risk, and revocations. |
| FR-10 | Display current activity, filters by domain/time/action, event detail, and revoked-token status in React. |
| FR-11 | Provide a deterministic script to reproduce normal and suspicious demo scenarios. |
| FR-12 | Support shadow, monitor, canary-enforce, and enforce policy modes with auditable rollbacks. |
| FR-13 | Support tenant/API policy configuration, role-scoped administration, version approval, and policy simulation. |
| FR-14 | Provide service health, model/policy readiness, dependency status, operational metrics, and trace correlation. |

## 9. Acceptance Criteria

1. A valid, unexpired token can call a protected endpoint; malformed, expired, wrong-audience, and revoked tokens receive 401 without reaching the endpoint.
2. At least four domain profiles map routes to correct domain and labels; unknown configured labels use the general profile.
3. Every protected decision stores timestamp, pseudonymous/user ID, `jti` or safe token reference, domain, route label, method, status, features, rule result, model version/score, risk, action, and reason codes.
4. Replaying the same scripted inputs against a clean database yields the same rule decisions and policy actions. ML results are repeatable for the same saved model and preprocessing version.
5. A configured high-risk example is blocked; a critical-risk example is blocked and revoked; reuse of its token is rejected on the next request.
6. Dashboard totals reconcile with stored events for the selected time range, and a newly persisted event appears within the chosen polling interval (initially 3 seconds).
7. A clean, reproducible demonstration can be completed in 5–7 minutes using Docker Compose or approved local services; this is a developer/demo setup criterion, not a production capacity criterion.
8. Synthetic training and evaluation partitions are disjoint; reports label all data as synthetic and do not claim real-world accuracy.

## 10. Non-Functional Requirements

- **Security:** managed secret storage, key rotation, least privilege, scoped service identity, least-data logging, authenticated/admin-role console, WAF/network controls, secure defaults, dependency scanning, and tested incident response.
- **Explainability:** each decision records score components, rule IDs, model version, and policy version.
- **Reliability:** explicit timeout, retry, circuit-breaker, backpressure, and fallback policies; multi-zone service deployment; durable event delivery; defined RTO/RPO and tested recovery. Fail-open/fail-closed behavior is risk-tiered and approved per route.
- **Performance:** define SLOs with product/API owners before rollout. Candidate initial objective: inline decision p99 under 50 ms at agreed peak load, excluding external client/network latency; validate using representative traffic and publish capacity curves, not just a single concurrency number.
- **Maintainability:** typed request/decision schemas, configuration outside logic, API contract in OpenAPI, pinned dependencies, README setup.
- **Privacy:** minimize and classify behavioral data, pseudonymize identifiers where feasible, avoid secrets/payment credentials, enforce retention/deletion and access audit, complete privacy impact assessment, and govern use of training data.
- **Usability:** dashboard labels explain risk and action in plain language; charts have time ranges and empty/error states.

## 11. Technology Stack

| Layer | Choice |
|---|---|
| Backend/gateway | Python 3, FastAPI, Uvicorn, PyJWT, Pydantic |
| Gateway | FastAPI remains suitable for the initial demonstrator; production gateway data plane may use an established high-throughput gateway/runtime, with FastAPI control APIs and Python model services where justified |
| Identity | Standards-based OIDC provider, asymmetric JWT keys, managed key lifecycle, centralized revocation/introspection strategy |
| Event/data | MongoDB may hold operational entities and event metadata; add a durable streaming platform and analytical store only after throughput/retention requirements are quantified |
| ML | scikit-learn Isolation Forest baseline, pandas/NumPy/joblib; managed model registry and reproducible pipeline for governed deployments |
| Frontend | React/TypeScript, accessible component system, chart library, typed API client |
| Platform | Container platform, Kubernetes or managed equivalent if multi-service scale requires it, infrastructure as code, secrets manager, CI/CD, OpenTelemetry-compatible telemetry |
| Cloud | Choose based on security, residency, availability, latency, cost, and existing organizational standards; Cloud Run can host an initial stateless service but is not a platform decision by default |

Avoid Kafka, Kubernetes, microservices, a separate model server, and deep learning for this scope. Keep model inference as an in-process Python service behind an interface.

## 12. Database Design

MongoDB is a document store; these are collection/document designs rather than relational tables. Use UTC timestamps and schema versions. Never persist raw JWTs: store `jti` plus a keyed hash if a lookup reference is needed.

| Collection | Main fields | Indexes / notes |
|---|---|---|
| `users` | `_id`, `role`, `created_at`, demo metadata | unique demo username; do not store plaintext passwords |
| `api_requests` | `event_id`, `user_id`, `token_jti`, `domain`, `endpoint_label`, `method`, `timestamp`, `payload_bytes`, `status_code`, `features`, `rule_ids`, `ml_score`, `risk_score`, `action`, `reason_codes`, versions | `{timestamp:-1}`, `{user_id:1,timestamp:-1}`, `{domain:1,timestamp:-1}`; TTL on `timestamp` for configured retention |
| `behavioral_features` | `user_id`, `token_jti`, `domain`, `window_end`, `window_seconds`, feature map, `schema_version` | `{user_id:1,domain:1,window_end:-1}`; optional in prototype if features live in `api_requests` |
| `security_events` | `event_id`, `timestamp`, `user_id`, `token_jti`, `event_type`, `severity`, `risk_score`, `reason_codes`, `status` | `{timestamp:-1}`, `{severity:1,timestamp:-1}` |
| `revoked_tokens` | `token_jti`, `user_id`, `revoked_at`, `expires_at`, `reason`, `source_event_id` | unique `token_jti`; TTL at `expires_at` (reject still requires correct JWT expiry semantics) |
| `alerts` | `alert_id`, `event_id`, `timestamp`, `severity`, `title`, `summary`, `acknowledged_at` | `{timestamp:-1}`, `{acknowledged_at:1,timestamp:-1}` |
| `risk_scores` | optional materialized latest score: `user_id`, `domain`, `score`, `action`, `updated_at` | `{user_id:1,domain:1}` unique; derive from request records if scope/time permits |

Create indexes through controlled migrations, not on each request. Request documents should include only the selected bounded feature snapshot, not unbounded history. Define versioned event schemas with compatibility checks and a published contract for gateway, data, analytics, and console consumers.

## 13. API Design

Prefix backend and dashboard routes with `/api/v1`. Example routes (all times UTC):

| Method + path | Auth | Purpose |
|---|---|---|
| `POST /api/v1/auth/login` | Public, demo rate rule | Verify seeded/demo account and issue JWT |
| `POST /api/v1/auth/refresh` | Bearer token | Rotate token if refresh is in scope; otherwise omit and document |
| `GET /api/v1/shop/products` | Bearer | Simulated e-commerce browse request |
| `POST /api/v1/shop/cart` | Bearer | Simulated cart action |
| `POST /api/v1/payments/charge` | Bearer | Synthetic payment attempt only; never handle real card data |
| `GET /api/v1/travel/search` | Bearer | Synthetic travel search with route fields |
| `POST /api/v1/travel/bookings` | Bearer | Synthetic booking |
| `POST /api/v1/rides/request` | Bearer | Synthetic ride request |
| `GET /api/v1/admin/summary` | Admin bearer | Counts and aggregate metrics by range/domain/action |
| `GET /api/v1/admin/requests` | Admin bearer | Paginated/filterable request list |
| `GET /api/v1/admin/events` | Admin bearer | Paginated security events/alerts |
| `GET /api/v1/admin/revoked-tokens` | Admin bearer | Revocation metadata only, never token values |
| `GET /health/live`, `GET /health/ready` | Public/internal | Process health and dependency readiness |

**Decision interface:** gateway passes a versioned `RequestContext` plus bounded `FeatureVector` to a decision service. Return `{risk_score: 0..100, action, reasons, rule_score, ml_score, policy_version, model_version, decision_id, expires_at}` with explicit timeout and fallback semantics. Do not return internal model features or other tenants' data to ordinary clients. Define backward-compatible schema evolution and request idempotency.

**Error behavior:** 401 for invalid/expired/revoked credentials; 403 for authenticated blocked request; 422 for invalid domain input; 503 when security dependencies prevent a protected decision. Use consistent JSON `{code, message, request_id}`.

## 14. ML Pipeline

1. Freeze a versioned feature schema with Member 2; exclude user IDs, token IDs, labels, and direct identifiers from training inputs.
2. Generate synthetic session-level records with domain label, feature values, and scenario label kept outside the model vector.
3. Split by synthetic session/user seed into train, validation, and test partitions (for example 60/20/20) to reduce leakage between near-duplicate sessions.
4. Train one shared Isolation Forest on predominantly normal training vectors. One-hot encode the small domain label; standardize or transform skewed numeric features with a fitted preprocessing pipeline. Persist the complete pipeline and model version together.
5. Convert `decision_function` to a normalized anomaly score in `[0,1]` using a documented calibration from validation data; larger means more anomalous. Do not treat the raw score as a probability.
6. Evaluate per-domain precision, recall, false-positive and false-negative rates at the selected threshold, plus confusion matrix and detection latency. Keep scenario labels for evaluation only.
7. Load a known model artifact at startup; readiness fails if configured model is missing. Expose a deterministic `predict(features, domain)` wrapper and log model version.
8. Retrain offline when the feature schema, data distribution, or model objective changes; require data governance and model-risk approval before any production model promotion. Never auto-train from unreviewed live traffic.

Isolation Forest is a baseline for tabular anomaly detection. It may rank unusual synthetic records without understanding attack intent or event ordering; rules and explicit sequence features provide context.

## 15. Dataset Generation

Generate approximately **10,000 synthetic behavior records** (preferably session-level records, each containing a bounded set of aggregate features) with fixed seeds and reproducible configuration. Suggested composition: 7,000 normal records, 3,000 anomalous records distributed among high-frequency behavior, credential abuse, endpoint/sequence deviation, and suspicious transaction/search/booking/ride activity. The class mix is for demonstration and does not represent real attack prevalence.

Generator requirements: sample per-domain normal patterns; produce correlated feature combinations (e.g. payment burst plus failures); inject realistic ranges and limited noise; include cold-start and low-volume sessions; write CSV/Parquet plus a data dictionary and generator version; validate feature ranges and missing values; split by session seed before model fitting. Store labels such as `normal`, `velocity_abuse`, `credential_abuse`, `sequence_deviation`, `domain_abuse` separately from model input. README must state synthetic data is not equivalent to production traffic and cannot establish field detection performance.

## 16. Risk Scoring

Normalize three independent inputs to `[0,100]`: rule severity `R`, calibrated anomaly score `M × 100`, and behavioral indicator score `B`. A clear initial formula is:

```text
Risk = clamp(round(0.40 × R + 0.35 × (100 × M) + 0.25 × B), 0, 100)
```

Use configurable profile weights that sum to 1.0; record each input and config version. The bands `0–29 allow`, `30–59 monitor`, `60–84 block`, `85–100 revoke and block` are sample starting values only. Apply hard rules before score bands for invalid credentials (401), explicit deny conditions, and severe abuse. Revocation policy must require a critical score or explicitly configured critical rule; avoid revoking solely on one noisy ML prediction. Keep a deterministic scenario in the demo profile and independently calibrate production thresholds on approved data. Document that score is prioritization, not probability.

## 17. Detection Rules

Implement a small set of explainable, domain-configurable rules. These example values are starting values for scripted demonstrations only:

| Rule | Example trigger in rolling window | Example severity contribution |
|---|---|---:|
| `velocity_general` | more than 60 protected calls / 60 sec | 35 |
| `failed_auth_burst` | 5 failed logins / 5 min per account | 55 and auth alert |
| `payment_burst` | 4 payment attempts / 2 min | 55 |
| `payment_failures` | failed payment ratio > 0.5 with at least 4 attempts | 50 |
| `travel_route_churn` | at least 8 searches / 5 min and 6 distinct route pairs | 35 |
| `ride_request_burst` | more than 5 ride requests / 5 min | 45 |
| `sequence_deviation` | configured forbidden/unexpected transition | 25–50 by domain |
| `payload_size` | bytes above route-specific cap | 20 plus validation/rejection as applicable |

Combine triggered rule severities by a documented max-plus-increment or capped sum (e.g. capped sum at 100); do not accidentally double-count correlated rules without review. Each decision includes rule IDs and observed values. Ordinary rate limits remain a supporting control, not the project's innovation.

## 18. Attack/Demo Scenarios

All calls use synthetic accounts and payloads. Exact scores depend on the chosen model artifact; use the same saved model/config during a demo. Expected score ranges below are configuration goals for demonstration, not model guarantees.

| Scenario / calls | Features and detections | Expected decision / dashboard |
|---|---|---|
| 1. Normal shop: login, 3 product views, cart, then stop | Low velocity, low failure ratio, normal sequence; no material rule; low ML anomaly | Risk <30, allow; normal count and domain activity rise |
| 2. Rapid general calls: repeat browse endpoint >60 times in 60 sec | High requests/minute and short inter-arrival; `velocity_general` | Configure to risk 60–84; blocked request and high-risk event; dashboard shows burst |
| 3. Failed authentication: submit 5 invalid demo logins in 5 min | Failed login count/rate; `failed_auth_burst`; login may not have an authenticated token | High risk, block/rate-control login and alert; no token to revoke |
| 4. Compromised valid token: after normal browse, make 4 synthetic payments quickly, including failures | Payment frequency/failure ratio, endpoint mix/sequence, anomaly score; payment rules | Configure aggregate to ≥85; request blocked, `jti` revoked, critical alert; next reuse gets 401 |
| 5. Travel abuse: search 8+ times across 6 routes then book repeatedly | search velocity, distinct routes, booking frequency, route churn | High risk and block; revoke only if configured critical composite reaches threshold |
| 6. Reuse revoked token: repeat any protected call with scenario 4 bearer token | Revocation lookup catches before feature/model processing | 401 `token_revoked`; rejected count/event visible without exposing token |

For each replay capture request ID, feature snapshot, matching rules, model score/version, risk components, action, response status, and dashboard row. The dashboard labels ML as a signal and displays reasons so judges can follow the decision.

## 19. Dashboard Design

Single-page React security console with role-protected data access, 3-second polling, and time-range/domain/action filters:

- Summary cards: total, allowed/normal, monitored/suspicious, blocked, active synthetic users, revoked tokens.
- Activity chart: request volume and risk over time, filterable by domain/action.
- Recent request table: time, user alias, domain, route label, status, risk, action, reason chips; detail drawer shows feature values and rule/model components.
- Alert timeline: severity, reason, event time, acknowledgement state.
- Revoked-token view: user alias, revocation time, expiry, reason/event link; never display bearer token or secret.
- Domain chart: requests and suspicious/blocked share by domain.

Use pagination and time filters to avoid loading all MongoDB events. Include loading, empty, stale-data, and API-error states. For a minimum viable build, implement summary, recent events, risk chart, and revoked list before visual polish.

## 20. Repository and Service Structure

```text
platform/
├── gateway-data-plane/      # enforcement runtime, adapters, route policies
├── identity-adapter/        # OIDC/JWT validation, keys, revocation contracts
├── policy-control-plane/    # versioned domain profiles, simulation, approvals
├── decision-service/        # rules, risk fusion, bounded model invocation
├── event-ingestion/         # durable events, schema validation, backpressure
├── feature-services/        # online windows and offline feature pipelines
├── model-training-serving/  # reproducible pipelines, registry, serving
├── security-console/        # React/TypeScript UI and BFF/admin APIs
├── shared-contracts/        # versioned OpenAPI, event and feature schemas
├── infra/                   # IaC, environments, policies, dashboards
├── tests/                   # contract, integration, performance, resilience
├── docs/                    # ADRs, threat model, runbooks, SLOs, data governance
└── local-demo/              # Compose profile, synthetic data, demo scenarios
```

Do not commit real `.env` secrets or generated personal data. Keep model artifacts small and document whether they are checked in or generated by setup.

## 21. Development Phases

Suggested schedule: 9–12 months to a controlled production rollout, with a 10–12 week demonstrator and shadow-mode milestone. Workstreams run in parallel only after architecture and schema gates. Dates are planning estimates; size based on dependencies, environments, and organizational release controls.

| Phase | Indicative timing | Lead workstreams / dependencies | Exit evidence |
|---|---|---|---|
| 1 — Discovery, threat model, SLOs | M0–1 | Product, architecture, security, SRE; stakeholders and API inventory | approved scope, abuse cases, data classification, SLO/error budget, ADRs |
| 2 — Contracts and platform foundations | M1–2 | Architecture, platform, gateway, data; Phase 1 | versioned contracts, environments, CI/CD, identity and telemetry integration |
| 3 — Gateway and identity vertical slice | M2–3 | Gateway, identity, QA | protected routes, revocation, policy hooks, traceable test path |
| 4 — Event and feature foundations | M2–4 | Data platform, gateway, privacy | validated event stream, online/offline feature parity, retention/access controls |
| 5 — Synthetic and approved-data baselines | M3–5 | ML, data, security | generator, evaluation set strategy, data lineage, baseline model and model card |
| 6 — Policy/risk and simulation | M4–6 | Risk, product, gateway, QA | explainable decisions, shadow mode, simulation and canary controls |
| 7 — Console and analyst operations | M4–7 | Console, security operations, platform | triage workflows, audit, role controls, alert and case lifecycle |
| 8 — Resilience, scale, threat validation | M6–8 | SRE, performance QA, security | load/fault/red-team evidence, recovery tests, capacity model, runbooks |
| 9 — Shadow and limited canary | M8–10 | Product, risk, SRE, operations | reviewed false-positive outcomes, rollback evidence, approved enforcement scope |
| 10 — Controlled rollout and tuning | M10–12+ | Program leadership and all owners | staged API/tenant rollout, SLO tracking, incident process, roadmap based on measured results |

Use short weekly integration checkpoints. Each member should merge a small working vertical slice early rather than waiting for their entire subsystem.

## 22. Testing Strategy

Run tests against synthetic inputs and, when approved, privacy-reviewed representative datasets; record environment, sample coverage, confidence intervals where appropriate, and actual outputs. Gate releases on documented evidence and owners, not only pass/fail counts.

| Type | Test / measurable check |
|---|---|
| Unit — auth | valid signature accepted; expired/wrong issuer/wrong audience/malformed JWT rejected; revocation lookup enforced; 100% of these deterministic cases pass |
| Unit — features | known request sequence yields exact count/rate/failure ratio/unique-endpoint values; windows exclude out-of-range events; domain feature tests cover each profile |
| Unit — risk | boundary values at 29/30/59/60/84/85 map to configured action; score remains 0–100; weights sum validation rejects invalid config |
| Unit — response | critical decision writes revocation and event; repeated revocation is idempotent; revoked token rejected on next call |
| Integration | scripted request traverses gateway → Mongo history → features → rules/model → risk → event; assert response, persisted fields, and dashboard API representation |
| Security | invalid/expired/revoked tokens; auth failures; large payload; unknown route/domain; injection-shaped strings; dashboard access by non-admin; ensure logs do not contain JWT or secrets |
| ML | holdout evaluation by domain/scenario; report confusion matrix, precision/recall/FPR/FNR; check reproducibility and schema mismatch behavior |
| Performance | model production peak and burst traffic; report throughput, p50/p95/p99, saturation, dependency cost, errors, CPU/memory, and headroom across scale points |
| Resilience | inject model/data/identity dependency timeouts, event-store outage, zone loss, queue lag, and recovery; verify approved fallback mode, no duplicate revocation side effects, and SLO impact |
| Dashboard | verify counts reconcile, authorization is tenant-scoped, pagination and filters work, and freshness meets the dashboard SLO under load |

Per developer instruction, testing should be performed only when the user requests tests or verification. This plan specifies what the team should test as part of their project; execution is a project-team phase.

## 23. Evaluation Metrics

Report definitions, observed values, confidence/uncertainty, evaluation data provenance, threshold, domain, and workload. Distinguish offline model metrics from operational policy outcomes; do not publish an accuracy target before measuring.

| Metric | Definition / why it matters |
|---|---|
| Detection recall | TP / (TP + FN) on labeled synthetic anomalies; missed abuse matters |
| Precision | TP / (TP + FP); low precision creates alert fatigue and user friction |
| False-positive rate | FP / (FP + TN); measures normal synthetic sessions incorrectly flagged |
| False-negative rate | FN / (FN + TP); share of labeled anomalies missed |
| Detection latency | time from request arrival to completed decision; report distribution and dependency breakdown |
| Revocation latency | time from critical decision to rejection across all active gateway instances/regions |
| API decision latency | gateway overhead p50/p95/p99 under agreed peak and burst loads; ties to the API SLO |
| Dashboard update latency | event time to visible, queryable state; report freshness and lag percentiles |
| Logging success rate | durable accepted security decisions / total completed decisions; pair with stream lag and loss accounting |
| Enforcement impact | block/challenge rate, analyst overturn rate, customer-impact incidents, and policy rollback rate |
| Model health | feature drift, score distribution, calibration where applicable, per-domain quality and data freshness |

Synthetic metrics describe behavior on the generator's scenarios only. They are not estimates of production effectiveness.

## 24. Feasibility

- **Technical:** a staged implementation using known gateway, identity, event-processing, ML, and web technologies is feasible. Complexity lies in measurable policy quality, dependency availability, and safe rollout rather than the Isolation Forest itself.
- **Economic:** open-source components reduce licensing costs, but 100 senior staff, cloud/data infrastructure, security review, and 24/7 operations make this a substantial program. Establish a cost model and compare build-versus-buy for gateway, identity, streaming, and SIEM capabilities.
- **Operational:** production rollout requires service ownership, on-call coverage, runbooks, policy change control, analyst capacity, incident response, and customer communication. The local demo remains reproducible via Compose.
- **Implementation:** the work is feasible when split into bounded workstreams with architecture ownership, contract testing, dependency management, and staged rollout. The main risks are organizational coordination, policy false positives, and unclear accountability.
- **Compute:** the demonstrator runs on a standard laptop; production sizing depends on measured traffic, feature windows, retention, latency SLO, tenant count, and availability targets. Lightweight inference does not require specialized hardware, but platform capacity must be load-tested.

## 25. Limitations

| Limitation | Practical effect | Future improvement |
|---|---|---|
| Synthetic data | patterns may not resemble real attackers or users | evaluate with consented, sanitized representative traffic and controlled red-team scenarios |
| Short behavioral history | limited baseline quality | longer retention with privacy and governance controls |
| False positives/negatives | legitimate unusual activity may be blocked; subtle attacks may pass | shadow mode, analyst feedback, calibrated policies, staged step-up controls |
| Cold-start users | little history to characterize a new account | cohort/domain baseline and conservative initial policy |
| Few API domains | profiles do not cover arbitrary business APIs | profile authoring and validation framework |
| Prototype revocation | one Mongo-backed lookup may not propagate across distributed instances instantly | centralized low-latency revocation store and consistency testing |
| Isolation Forest limits | tabular outlier score is not attack intent or calibrated probability; sequence understanding is limited | validated sequence models or complementary detectors when sufficient data exists |
| Sophisticated attacks | low-and-slow, mimicking, and distributed attacks may evade simple features | cross-account/graph analysis and threat-informed rules |
| Cloud constraints | cold starts, network latency, Mongo connection limits, and secrets need deployment work | load-tested managed architecture and operational monitoring |
| No step-up verification | monitor action may not distinguish a legitimate unusual user from an attacker | integrate risk-based reauthentication and recovery controls |
| Distributed ownership and policy drift | many API teams can configure inconsistent domain semantics | central schema/profile governance, policy linting, simulation, approvals, and drift reporting |
| Operational alert volume | broad rollout can overwhelm analysts even if offline metrics look acceptable | shadow-mode volume studies, deduplication, severity routing, staffing plan, and feedback loop |

## 26. Future Enhancements

Prioritize by evidence and threat model: device and geographic context with privacy review; adaptive authentication/step-up; graph-based entity analysis; advanced sequence modeling; SIEM/SOC integration; streaming analytics; multi-region enforcement and revocation consistency; automated incident response with human approval where needed. Deep learning should be considered only when representative data and measurable gains justify its operational cost.

## 27. Standards & Industry Alignment

- **NIST SP 800-207:** Our system applies Zero Trust principles to continuous behavioral evaluation; it is not a complete implementation of the NIST Zero Trust Architecture. A formal mapping should identify applicable components, control gaps, and deployment assumptions; no certification is implied.
- **Isolation Forest:** the model family was introduced by Liu, Ting, and Zhou (ICDM 2008). This project uses the established algorithm as a baseline and does not claim algorithmic novelty.
- **UEBA:** behavioral features and user/token context align with UEBA concepts; model and analyst workflows must be validated for each deployment and are not equivalent to a commercial UEBA platform.
- **API security/gateways:** JWT validation, route policy, monitoring, rate rules, and response enforcement are common gateway practices. Do not imply official affiliation, certification, or feature equivalence to Cloudflare, Akamai, Kong, or other vendors.

References for final report: NIST SP 800-207, *Zero Trust Architecture*; F. T. Liu, K. M. Ting, and Z.-H. Zhou, “Isolation Forest,” IEEE ICDM 2008. Verify exact bibliographic and standards citations when preparing the submitted report.

## 28. Final Deliverables

- [ ] **Backend:** FastAPI gateway, JWT issue/validation, protected simulated endpoints, request interception, monitoring, feature extraction, domain profiles, rules, risk engine, block/revoke response.
- [ ] **ML:** reproducible 10,000-record synthetic generator and dataset, data dictionary, preprocessing pipeline, shared Isolation Forest, prediction wrapper, evaluation report and model card.
- [ ] **Database:** documented MongoDB collections, indexes, retention policy, request/event/alert persistence, revocation lookup.
- [ ] **Frontend:** authenticated React dashboard, summary, charts, event table/detail, alerts, risk visualization, domain filters, revoked-token list.
- [ ] **Deployment:** reproducible local demo plus production infrastructure as code, CI/CD, secret management, observability, capacity model, SLOs, disaster recovery and runbooks before enforcement rollout.
- [ ] **Documentation:** SRS, architecture diagram, data/ER-style design, OpenAPI/API guide, setup README, test/evaluation report, limitations, final presentation and demo script.

## 29. Executive and Technical Demonstration

| Time | Action and narration | Expected visible evidence |
|---|---|---|
| 0:00–0:40 | Explain that an unexpired token can still behave unexpectedly; show architecture in one sentence | Gateway, profile, rules/model, risk, response, dashboard |
| 0:40–1:20 | Log in as synthetic user and call browse endpoints normally | Valid token; normal requests and low risk on dashboard |
| 1:20–2:10 | Show recent features: low velocity, ordinary endpoint mix | Feature snapshot and allow decision |
| 2:10–3:10 | Replay a deterministic suspicious payment burst with the same valid token | Payment velocity/failure features, named rule, model anomaly signal, rising risk |
| 3:10–4:00 | Show policy response | Request blocked; critical event and token revocation appear |
| 4:00–4:40 | Reuse the same bearer token | Immediate 401 revoked-token response |
| 4:40–5:40 | Inspect dashboard alert and decision detail | Timeline, risk components, reasons, domain chart, revoked-token metadata |
| 5:40–6:30 | State scope and limits | Synthetic data, tunable thresholds, no real payment data; future work in one sentence |

The scripted walk-through remains 5–7 minutes for judges or executives. For a senior engineering review, append a 30–45 minute technical session covering SLO/error budgets, threat model, data lineage and privacy, model evaluation, failure modes, canary/rollback, capacity evidence, runbooks, and unresolved risks.

Rehearse with clean database seed and preloaded model. Keep a fallback screenshot or saved event data for dashboard network hiccups, while still demonstrating the actual API response path live.

## 30. Final Architecture Summary

```text
JWT identity check + revocation
             ↓
Route-to-domain context + recent behavioral features
             ↓
Domain-configured rules + one shared Isolation Forest
             ↓
Transparent configurable 0–100 risk policy
             ↓
Allow / monitor / block / revoke-and-block
             ↓
MongoDB audit events and React security dashboard
```

The first-release success criterion is a reproducible end-to-end story: **valid token → normal behavior → behavioral change → anomaly detection → risk increase → automatic block → token revocation → dashboard alert**. The production success criterion additionally requires evidence that policies are calibrated, enforcement is reversible, SLOs hold under failure and load, data handling is approved, and operational owners can respond. Keep the score explainable, policy changes governed, and claims proportionate to the evidence.
