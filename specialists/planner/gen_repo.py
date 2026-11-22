"""Repo builders for the planner task factory (stdlib only, deterministic given rng)."""

DOMAINS = [
    ("order", "orders", "Order", [("gift_message", "TEXT", "gift message"), ("priority", "INTEGER", "priority"), ("delivery_date", "DATE", "delivery date")]),
    ("invoice", "invoices", "Invoice", [("po_number", "VARCHAR(40)", "PO number"), ("tax_rate", "NUMERIC(5,2)", "tax rate"), ("paid_at", "TIMESTAMP", "paid-at timestamp")]),
    ("ticket", "tickets", "Ticket", [("severity", "INTEGER", "severity"), ("assignee_team", "VARCHAR(60)", "assignee team"), ("sla_hours", "INTEGER", "SLA hours")]),
    ("booking", "bookings", "Booking", [("party_size", "INTEGER", "party size"), ("notes", "TEXT", "notes"), ("deposit_cents", "INTEGER", "deposit amount")]),
    ("product", "products", "Product", [("weight_grams", "INTEGER", "weight"), ("is_fragile", "BOOLEAN", "fragile flag"), ("brand", "VARCHAR(80)", "brand")]),
    ("subscription", "subscriptions", "Subscription", [("trial_days", "INTEGER", "trial length"), ("coupon_code", "VARCHAR(32)", "coupon code"), ("paused_until", "DATE", "paused-until date")]),
    ("review", "reviews", "Review", [("helpful_votes", "INTEGER", "helpful votes"), ("reviewer_country", "VARCHAR(2)", "reviewer country"), ("spoiler_flag", "BOOLEAN", "spoiler flag")]),
    ("shipment", "shipments", "Shipment", [("carrier", "VARCHAR(40)", "carrier"), ("tracking_url", "VARCHAR(255)", "tracking URL"), ("insured_value", "INTEGER", "insured value")]),
    ("appointment", "appointments", "Appointment", [("room", "VARCHAR(20)", "room"), ("reminder_sent", "BOOLEAN", "reminder-sent flag"), ("duration_min", "INTEGER", "duration")]),
    ("course", "courses", "Course", [("difficulty", "VARCHAR(20)", "difficulty"), ("language", "VARCHAR(8)", "language"), ("prerequisite_id", "INTEGER", "prerequisite course")]),
    ("playlist", "playlists", "Playlist", [("is_collaborative", "BOOLEAN", "collaborative flag"), ("cover_url", "VARCHAR(255)", "cover image URL"), ("mood", "VARCHAR(30)", "mood tag")]),
    ("task", "tasks", "Task", [("estimate_hours", "NUMERIC(5,1)", "estimate"), ("blocked_reason", "TEXT", "blocked reason"), ("parent_task_id", "INTEGER", "parent task")]),
    ("device", "devices", "Device", [("firmware_version", "VARCHAR(20)", "firmware version"), ("last_seen_at", "TIMESTAMP", "last-seen time"), ("location", "VARCHAR(80)", "location")]),
    ("coupon", "coupons", "Coupon", [("max_uses", "INTEGER", "max uses"), ("min_spend_cents", "INTEGER", "minimum spend"), ("stackable", "BOOLEAN", "stackable flag")]),
    ("member", "members", "Member", [("tier", "VARCHAR(20)", "tier"), ("birthday", "DATE", "birthday"), ("referral_code", "VARCHAR(16)", "referral code")]),
    ("listing", "listings", "Listing", [("bedrooms", "INTEGER", "bedroom count"), ("pet_friendly", "BOOLEAN", "pet-friendly flag"), ("virtual_tour_url", "VARCHAR(255)", "virtual tour URL")]),
    ("expense", "expenses", "Expense", [("receipt_url", "VARCHAR(255)", "receipt URL"), ("category_code", "VARCHAR(12)", "category code"), ("reimbursable", "BOOLEAN", "reimbursable flag")]),
    ("vehicle", "vehicles", "Vehicle", [("odometer_km", "INTEGER", "odometer"), ("vin_last6", "VARCHAR(6)", "VIN suffix"), ("fuel_type", "VARCHAR(16)", "fuel type")]),
    ("recipe", "recipes", "Recipe", [("prep_minutes", "INTEGER", "prep time"), ("spice_level", "INTEGER", "spice level"), ("source_url", "VARCHAR(255)", "source URL")]),
    ("donation", "donations", "Donation", [("campaign_code", "VARCHAR(24)", "campaign code"), ("anonymous", "BOOLEAN", "anonymous flag"), ("matched_cents", "INTEGER", "matched amount")]),
]

LANG_SPEC = {"python": "python", "java": "java"}


class Repo:
    def __init__(self, name, stack):
        self.name, self.stack = name, stack
        self.files = {}   # path -> summary
        self.roles = {}   # role -> path

    def add(self, role, path, summary):
        if role:
            self.roles[role] = path
        self.files[path] = summary
        return path

    def text(self):
        out = [f"Repository: {self.name}  ({self.stack})", "", "File tree and summaries:"]
        for p in sorted(self.files):
            out.append(f"  {p} - {self.files[p]}")
        return "\n".join(out)


def _common_ops(r, lang, dom_dp, extra_ci=""):
    r.add("dockerfile", "Dockerfile", "Container image build for the service; base image, install, entrypoint, no HEALTHCHECK yet.")
    r.add("ci", ".github/workflows/ci.yml", "CI pipeline: lint, unit tests, image build; runs on pull requests.")
    r.add("k8s", "deploy/k8s/deployment.yaml", "Kubernetes Deployment and Service: replicas, env vars, resource limits, probes.")
    r.add("runbook", "docs/runbook.md", "On-call runbook: common failures, dashboards, rollback steps.")
    r.add("alerts", "ops/alerts.yaml", "Alerting rules (error rate, latency, queue depth) with thresholds and routing.")
    r.add("readme", "README.md", "Project overview, setup, how to run tests.")


def web_repo(rng, lang, dom, others):
    d, dp, D = dom[0], dom[1], dom[2]
    r = Repo(f"{dp}-service", "python-fastapi + react-ts" if lang == "python" else "java-spring-boot + react-ts")
    if lang == "python":
        r.add("config", "app/config.py", "Settings read from environment: database URL, page size, feature flags, CORS origins.")
        r.add("db", "app/db.py", "Database connection helper and migration runner (applies migrations/*.sql in order).")
        r.add("middleware", "app/middleware.py", "Request middleware: request-id, access logging, error envelope.")
        r.add("health", "app/api/health.py", "Liveness endpoint /healthz returning {status: ok}; no dependency checks.")
        r.add("flags", "app/flags.py", "Feature-flag lookup helper reading flags from settings.")
        r.add("export", "app/services/export.py", "CSV export helpers shared by report endpoints.")
        r.add("migration0", "migrations/0001_init.sql", f"Initial schema: tables for {', '.join(o[1] for o in others)} and {dp}.")
        r.add("model", f"app/models/{d}.py", f"{D} dataclass/ORM model: columns and defaults for table {dp}.")
        r.add("repo", f"app/repositories/{d}_repo.py", f"Raw SQL for {dp}: insert, select by id, list with filters and paging, update, delete.")
        r.add("service", f"app/services/{d}_service.py", f"{D} business rules: validation, totals, status transitions, pagination, calls the repository.")
        r.add("dto", f"app/schemas/{d}_schema.py", f"Pydantic request/response schemas for {D}; whitelist of fields exposed over the API.")
        r.add("api", f"app/api/{d}_routes.py", f"HTTP routes for /{dp}: list, create, get, update, delete; maps schemas to the service.")
        r.add("test_service", f"tests/test_{d}_service.py", f"pytest unit tests for {D} service rules using an in-memory database.")
        r.add("test_api", f"tests/test_{d}_api.py", f"pytest API tests for /{dp} endpoints using the test client.")
        r.add("deps", "requirements.txt", "Pinned Python dependencies (fastapi, pydantic, uvicorn, pytest).")
        r.add("", "tests/conftest.py", "Shared pytest fixtures: test client, temporary database.")
        for o in others:
            r.add("", f"app/models/{o[0]}.py", f"{o[2]} model for table {o[1]}.")
            r.add("", f"app/services/{o[0]}_service.py", f"{o[2]} business rules.")
            r.add("", f"app/api/{o[0]}_routes.py", f"HTTP routes for /{o[1]}.")
            r.add("", f"tests/test_{o[0]}_api.py", f"API tests for /{o[1]}.")
        r.roles["new_migration_dir"] = "migrations/"
    else:
        base = f"src/main/java/com/acme/app/{d}"
        tbase = f"src/test/java/com/acme/app/{d}"
        r.add("config", "src/main/resources/application.yml", "Spring configuration: datasource, page size, feature flags, server port, management endpoints.")
        r.add("db", "src/main/java/com/acme/app/common/FlywayConfig.java", "Flyway setup; runs db/migration scripts on startup.")
        r.add("middleware", "src/main/java/com/acme/app/common/RequestFilter.java", "Servlet filter: request-id, access logging.")
        r.add("health", "src/main/java/com/acme/app/common/HealthController.java", "GET /healthz returning {status: ok}; no dependency checks.")
        r.add("flags", "src/main/java/com/acme/app/common/FeatureFlags.java", "Feature-flag lookup bound to application.yml.")
        r.add("export", "src/main/java/com/acme/app/common/CsvExporter.java", "CSV writer helpers shared by report endpoints.")
        r.add("migration0", "src/main/resources/db/migration/V1__init.sql", f"Initial schema: tables for {', '.join(o[1] for o in others)} and {dp}.")
        r.add("model", f"{base}/{D}.java", f"JPA entity for table {dp}: columns, getters, defaults.")
        r.add("repo", f"{base}/{D}Repository.java", f"Spring Data repository for {D} with custom JPQL queries for filtering and paging.")
        r.add("service", f"{base}/{D}Service.java", f"{D} business rules: validation, totals, status transitions, pagination.")
        r.add("dto", f"{base}/{D}Dto.java", f"Request/response DTO for {D}; fields exposed over the API and mapping from the entity.")
        r.add("api", f"{base}/{D}Controller.java", f"REST controller for /{dp}: list, create, get, update, delete.")
        r.add("test_service", f"{tbase}/{D}ServiceTest.java", f"JUnit 5 unit tests for {D}Service.")
        r.add("test_api", f"{tbase}/{D}ControllerTest.java", f"MockMvc tests for /{dp} endpoints.")
        r.add("deps", "pom.xml", "Maven build: Spring Boot parent, dependencies, plugins, Java version.")
        for o in others:
            ob, ot = f"src/main/java/com/acme/app/{o[0]}", f"src/test/java/com/acme/app/{o[0]}"
            r.add("", f"{ob}/{o[2]}.java", f"JPA entity for {o[1]}.")
            r.add("", f"{ob}/{o[2]}Service.java", f"{o[2]} business rules.")
            r.add("", f"{ob}/{o[2]}Controller.java", f"REST controller for /{o[1]}.")
            r.add("", f"{ot}/{o[2]}ControllerTest.java", f"MockMvc tests for /{o[1]}.")
        r.roles["new_migration_dir"] = "src/main/resources/db/migration/"
    r.add("api_client", f"web/src/api/{d}.ts", f"Typed fetch client for /{dp} and the TypeScript {D} interface.")
    r.add("ui_list", f"web/src/pages/{D}List.tsx", f"Table page listing {dp} with sorting, paging and row formatting (dates, money).")
    r.add("ui_form", f"web/src/pages/{D}Form.tsx", f"Create/edit form for a {d}: inputs, client-side validation, submit handler.")
    r.add("ui_css", "web/src/styles/app.css", "Global styles: layout, table, form, button classes.")
    r.add("", "web/package.json", "Frontend scripts and dependencies (vite, react, vitest).")
    for o in others[:2]:
        r.add("", f"web/src/pages/{o[2]}List.tsx", f"Table page for {o[1]}.")
    _common_ops(r, lang, dp)
    return r


def new_migration_path(r, lang, dp, slug):
    if lang == "python":
        return f"migrations/0002_{slug}.sql"
    return f"src/main/resources/db/migration/V2__{slug}.sql"


def etl_repo(rng, dom, others):
    d, dp, D = dom[0], dom[1], dom[2]
    r = Repo(f"{dp}-pipeline", "python-etl + sql models + airflow")
    r.add("config", "pipelines/config.py", "Pipeline settings: source paths, warehouse DSN, batch size, lookback window days.")
    r.add("io", "pipelines/utils/io.py", "File and warehouse IO helpers (read CSV/JSON lines, bulk insert).")
    r.add("raw_schema", f"sql/schema/{d}_raw.sql", f"DDL for raw landing table raw_{dp}.")
    r.add("ingest", f"pipelines/ingest_{d}.py", f"Reads source {d} exports, validates and normalizes rows, loads raw_{dp}.")
    r.add("transform", f"pipelines/transform_{d}.py", f"Python transform step: dedupes and enriches raw_{dp}, writes staging_{dp}.")
    r.add("model_sql", f"sql/models/{d}_daily.sql", f"Daily rollup SQL model {d}_daily built from staging_{dp}: counts and sums per day.")
    r.add("dag", f"airflow/dags/{d}_dag.py", f"Airflow DAG: ingest -> transform -> {d}_daily; schedule and retries.")
    r.add("dashboard", f"dashboards/{d}.json", f"Dashboard definition (tiles/queries) over {d}_daily.")
    r.add("dict", "docs/data_dictionary.md", "Column-level data dictionary for raw, staging and model tables.")
    r.add("test_ingest", f"tests/test_ingest_{d}.py", f"pytest tests for ingest_{d} using small fixture files.")
    r.add("test_transform", f"tests/test_transform_{d}.py", f"pytest tests for transform_{d}.")
    r.add("test_sql", f"tests/sql/test_{d}_daily.py", f"Runs {d}_daily.sql against an in-memory SQLite fixture and asserts results.")
    r.add("alerts", "ops/alerts.yaml", "Freshness and row-count alerts for pipelines.")
    r.add("runbook", "docs/runbook.md", "Pipeline on-call runbook: backfills, reruns, stuck DAGs.")
    r.add("dockerfile", "Dockerfile", "Image for the pipeline workers.")
    r.add("ci", ".github/workflows/ci.yml", "CI: pytest, sqlfluff lint, image build.")
    r.add("readme", "README.md", "Overview and how to run locally.")
    for o in others[:3]:
        r.add("", f"pipelines/ingest_{o[0]}.py", f"Ingest for {o[1]}.")
        r.add("", f"sql/models/{o[0]}_daily.sql", f"Daily rollup for {o[1]}.")
        r.add("", f"airflow/dags/{o[0]}_dag.py", f"DAG for {o[1]}.")
    r.roles["new_migration_dir"] = "sql/schema/"
    return r


def mixed_repo(rng, dom, others):
    d, dp, D = dom[0], dom[1], dom[2]
    r = Repo(f"{dp}-platform", "java api + python worker + react-ts + terraform + k8s")
    ab = f"services/api/src/main/java/com/acme/{d}"
    tb = f"services/api/src/test/java/com/acme/{d}"
    r.add("migration0", "db/migrations/V1__init.sql", f"Initial schema for {dp} and related tables.")
    r.roles["new_migration_dir"] = "db/migrations/"
    r.add("j_model", f"{ab}/{D}.java", f"JPA entity for {dp}.")
    r.add("j_repo", f"{ab}/{D}Repository.java", f"Spring Data repository for {D}.")
    r.add("j_service", f"{ab}/{D}Service.java", f"{D} business rules; publishes {d} events to the queue after writes.")
    r.add("j_api", f"{ab}/{D}Controller.java", f"REST controller for /{dp}.")
    r.add("j_dto", f"{ab}/{D}Dto.java", f"API DTO for {D}.")
    r.add("j_cfg", "services/api/src/main/resources/application.yml", "API config: datasource, queue name, feature flags, metrics.")
    r.add("j_test_service", f"{tb}/{D}ServiceTest.java", f"JUnit tests for {D}Service.")
    r.add("j_test_api", f"{tb}/{D}ControllerTest.java", f"MockMvc tests for /{dp}.")
    r.add("contract", f"contracts/{d}_event.json", f"JSON schema of the {d} event shared by the API (producer) and worker (consumer).")
    r.add("w_handler", f"workers/{d}_worker/handler.py", f"Queue consumer: parses {d} events, applies side effects (email, search index), acks.")
    r.add("w_cfg", f"workers/{d}_worker/settings.py", "Worker settings: queue name, concurrency, retry/backoff, DLQ.")
    r.add("w_test", f"workers/{d}_worker/tests/test_handler.py", "pytest tests for the handler with fake queue messages.")
    r.add("w_deps", f"workers/{d}_worker/requirements.txt", "Pinned worker dependencies.")
    r.add("api_client", f"web/src/api/{d}.ts", f"Typed client for /{dp}.")
    r.add("ui_list", f"web/src/pages/{D}List.tsx", f"Table page for {dp} with status badges.")
    r.add("ui_form", f"web/src/pages/{D}Form.tsx", f"Create/edit form for {d}.")
    r.add("tf_main", "infra/terraform/main.tf", "Terraform: queue, DLQ, IAM roles, database, buckets.")
    r.add("tf_vars", "infra/terraform/variables.tf", "Terraform variables: region, sizes, queue retention.")
    r.add("k8s_api", "deploy/k8s/api.yaml", "Deployment/Service for the API: env vars, probes, resources.")
    r.add("k8s_worker", "deploy/k8s/worker.yaml", "Deployment for the worker: env vars, replicas, resources.")
    r.add("ci", ".github/workflows/ci.yml", "CI: maven tests, pytest, npm test, image builds, terraform validate.")
    r.add("runbook", f"ops/runbooks/{d}.md", f"Runbook for {d} flows: DLQ handling, replay, rollback.")
    r.add("alerts", f"ops/alerts/{d}.yaml", "Alert rules: queue depth, DLQ size, API 5xx, worker lag.")
    r.add("dashboard", f"ops/dashboards/{d}.json", "Grafana dashboard JSON for API and worker metrics.")
    r.add("readme", "README.md", "Platform overview and local dev instructions.")
    for o in others[:2]:
        r.add("", f"services/api/src/main/java/com/acme/{o[0]}/{o[2]}Service.java", f"{o[2]} business rules.")
        r.add("", f"web/src/pages/{o[2]}List.tsx", f"Table page for {o[1]}.")
    return r


def cli_repo(rng, dom):
    d, dp, D = dom[0], dom[1], dom[2]
    pkg = f"{d}tool"
    r = Repo(f"{d}tool", "python cli (argparse), single package")
    r.add("cli", f"src/{pkg}/cli.py", "Entry point: builds the argparse parser, dispatches subcommands, prints results, exit codes.")
    r.add("core", f"src/{pkg}/core.py", f"Core logic for {dp}: load, filter, sort, summarize records.")
    r.add("fmt", f"src/{pkg}/formatters.py", "Output formatters: table and JSON; column widths and alignment.")
    r.add("cfg", f"src/{pkg}/config.py", "Reads ~/.config file and environment; defaults for page size and date format.")
    r.add("store", f"src/{pkg}/store.py", f"Reads and writes the local JSON store of {dp}.")
    r.add("test_cli", "tests/test_cli.py", "pytest tests for argument parsing and exit codes.")
    r.add("test_core", "tests/test_core.py", f"pytest tests for core {d} logic.")
    r.add("test_fmt", "tests/test_formatters.py", "pytest tests for output formatting.")
    r.add("deps", "pyproject.toml", "Package metadata, dependencies, entry point, tool configs.")
    r.add("readme", "README.md", "Usage examples for each subcommand.")
    r.add("ci", ".github/workflows/ci.yml", "CI: ruff, pytest on Python 3.10-3.12.")
    r.add("", "CHANGELOG.md", "Release notes.")
    r.roles["new_migration_dir"] = "src/"
    return r
