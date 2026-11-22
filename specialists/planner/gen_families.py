"""Scenario families. Each family returns a Scenario: request text, kind, step specs, ranges."""
import os

SPECIALISTS = ["python", "java", "ui", "data", "devops", "ops", "qa", "debugger", "reviewer"]


class Ctx:
    def __init__(self, rng, r, lang, dom, field):
        self.rng, self.r, self.lang, self.dom, self.field = rng, r, lang, dom, field
        self.d, self.dp, self.D = dom[0], dom[1], dom[2]
        self.f, self.ft, self.fl = field
        self.L = lang  # specialist name for lang roles
        slug = f"add_{self.f}_to_{self.dp}"
        self.mig = None
        if lang in ("python", "java"):
            from gen_repo import new_migration_path
            self.mig = new_migration_path(r, lang, self.dp, slug)
        elif lang == "mixed":
            self.mig = f"db/migrations/V2__{slug}.sql"
        if lang == "etl":
            self.mig = None

    def p(self, role):
        return self.r.roles[role]

    def tc(self, role):
        path = self.p(role)
        base = os.path.basename(path)
        if path.endswith(".py"):
            return f"pytest {path} -q"
        if path.endswith(".java"):
            return f"mvn -q test -Dtest={base[:-5]}"
        return f"npm --prefix web test -- {base.split('.')[0]}"


def S(key, spec, roles, goal, deps, acc, accept=None, refs=()):
    return dict(key=key, spec=spec, roles=list(roles), goal=goal, deps=list(deps), acc=acc,
                accept=list(accept or [spec]), refs=list(refs))


def Sc(kind, request, steps, lo=None, hi=None, extra=2, tag=""):
    n = len(steps)
    return dict(kind=kind, request=request, steps=steps, lo=lo if lo is not None else max(1, n - 1),
                hi=hi if hi is not None else n + 2, extra=extra, tag=tag)


def migacc(c, what=None):
    if c.lang == "java":
        return f"`mvn -q flyway:migrate` exits 0 on an empty database and the {c.dp} table has column `{c.f}`"
    if c.lang == "mixed":
        return f"applying `{c.mig}` with `psql -f` on a fresh database exits 0 and `\\d {c.dp}` lists `{c.f}`"
    return f"`python -m app.db migrate` exits 0 on an empty database and `PRAGMA table_info({c.dp})` lists `{c.f}`"


def ui_acc(c, what):
    return f"`npm --prefix web run build` exits 0 and the {c.D} page displays {what}"


def pick(rng, xs):
    return xs[rng.randrange(len(xs))]


def noise(rng):
    return pick(rng, ["", "", "", " This is blocking the next release.", " Product wants it this sprint.",
                      " Keep the change small and backwards compatible.", " Support escalated this twice already."])


# ---------------------------------------------------------------- web families
def f_add_field_full(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature request: let users record a {c.fl} (`{c.f}`, {c.ft}) on each {c.d}. It must be stored, returned by the API, editable in the form and shown in the list.",
        f"We need a new optional field `{c.f}` ({c.fl}) on {c.dp}: persisted in the database, accepted/returned by the REST API, editable on the {c.D} form and visible in the {c.D} table.",
        f"Add `{c.f}` ({c.fl}) to {c.dp} end to end: DB column, API, UI form and list column, with tests.",
    ]) + noise(rng)
    split = rng.random() < 0.5
    mig = S("mig", "data", ["new_migration"], f"Add nullable column `{c.f}` {c.ft} to table `{c.dp}` in a new migration; existing rows keep NULL.", [], migacc(c))
    mdl = S("mdl", c.L, ["model", "repo"], f"Add `{c.f}` to the {c.D} model and to the insert/select/update queries in the repository.", ["mig"],
            f"`{c.tc('test_service')}` passes with a test that saves and reloads a {c.d} with `{c.f}` set")
    if not split:
        svc = S("svc", c.L, ["service", "dto", "api"], f"Accept and validate `{c.f}` in the service, expose it in the request/response schema and the /{c.dp} routes.", ["mdl"],
                f"POST then GET /{c.dp}/<id> returns `{c.f}` with HTTP 200 (`{c.tc('test_api')}`)")
        ui = S("ui", "ui", ["api_client", "ui_form", "ui_list"], f"Add `{c.f}` to the TypeScript {c.D} type, the form input and a column in the list.", ["svc"], ui_acc(c, f"a {c.fl} column"))
        qa = S("qa", "qa", ["test_api", "test_service"], f"Extend API and service tests to cover creating and reading `{c.f}`, including the null default.", ["svc"],
               f"`{c.tc('test_api')}` and `{c.tc('test_service')}` pass and include a case where `{c.f}` is omitted")
        steps = [mig, mdl, svc, ui, qa]
    else:
        svc = S("svc", c.L, ["service", "dto"], f"Validate `{c.f}` in the service and add it to the request/response schema.", ["mdl"],
                f"`{c.tc('test_service')}` passes with a case where invalid `{c.f}` raises a validation error")
        api = S("api", c.L, ["api"], f"Pass `{c.f}` through the /{c.dp} routes on create, update and read.", ["svc"],
                f"POST then GET /{c.dp}/<id> returns `{c.f}` with HTTP 200")
        ui = S("ui", "ui", ["api_client", "ui_form", "ui_list"], f"Add `{c.f}` to the TypeScript {c.D} type, the form input and a list column.", ["api"], ui_acc(c, f"a {c.fl} column"))
        qs = S("qs", "qa", ["test_service"], f"Add service tests for `{c.f}` including the null default and invalid values.", ["svc"], f"`{c.tc('test_service')}` passes with new cases for `{c.f}`")
        qa = S("qa", "qa", ["test_api"], f"Add API tests that create, read and update a {c.d} with `{c.f}`.", ["api"], f"`{c.tc('test_api')}` passes and asserts `{c.f}` round-trips")
        steps = [mig, mdl, svc, api, ui, qs, qa]
    return Sc("feature", req, steps)


def f_add_field_backend(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature request (API only, the web team will do the UI later): add an optional `{c.f}` ({c.fl}) to {c.dp}, stored and returned by the REST API.",
        f"The mobile app needs `{c.f}` ({c.fl}) on every {c.d} from the API. Backend change only; do not touch the web UI.",
    ]) + noise(rng)
    mig = S("mig", "data", ["new_migration"], f"Add nullable column `{c.f}` {c.ft} to `{c.dp}` in a new migration.", [], migacc(c))
    if rng.random() < 0.5:
        be = S("be", c.L, ["model", "repo", "service", "dto", "api"], f"Add `{c.f}` to model, queries, validation, schema and routes.", ["mig"],
               f"POST then GET /{c.dp}/<id> returns `{c.f}` and HTTP 200")
        qa = S("qa", "qa", ["test_api"], f"Add an API test creating a {c.d} with and without `{c.f}`.", ["be"], f"`{c.tc('test_api')}` passes with both cases")
        return Sc("feature", req, [mig, be, qa])
    mdl = S("mdl", c.L, ["model", "repo", "service", "dto"], f"Add `{c.f}` to the model, SQL, validation and response schema.", ["mig"],
            f"`{c.tc('test_service')}` passes when saving and reloading `{c.f}`")
    api = S("api", c.L, ["api"], f"Expose `{c.f}` on create/update/read in the /{c.dp} routes.", ["mdl"], f"GET /{c.dp}/<id> returns `{c.f}` and HTTP 200")
    qs = S("qs", "qa", ["test_service"], f"Add service tests for `{c.f}` defaults and validation.", ["mdl"], f"`{c.tc('test_service')}` passes with a new test for the default value")
    qa = S("qa", "qa", ["test_api"], f"Add API round-trip tests for `{c.f}`.", ["api"], f"`{c.tc('test_api')}` passes and asserts `{c.f}` in the response JSON")
    return Sc("feature", req, [mig, mdl, api, qs, qa])


def f_filter(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature request: GET /{c.dp} should accept `?created_after=<ISO date>` and return only {c.dp} created after that date. Combine it with the existing paging.",
        f"Customers want to filter the {c.d} list by creation date: add a `created_after` query parameter to GET /{c.dp}.",
    ]) + noise(rng)
    v = rng.randrange(3)
    if v == 0:
        a = S("a", c.L, ["repo", "service", "api"], "Add a created_after condition to the list query, pass it through the service and parse/validate it in the route (400 on bad date).", [],
              f"GET /{c.dp}?created_after=2024-01-01 returns only newer rows and HTTP 200; a bad date returns 400")
        b = S("b", "qa", ["test_api"], "Add API tests for created_after: filter hit, filter miss, invalid date.", ["a"], f"`{c.tc('test_api')}` passes with three new cases")
        return Sc("feature", req, [a, b])
    if v == 1:
        a = S("a", c.L, ["repo", "service"], "Add created_after to the repository query and service list method.", [], f"`{c.tc('test_service')}` passes with a created_after case")
        b = S("b", c.L, ["api", "dto"], "Parse and validate the created_after query parameter in the route and pass it to the service.", ["a"], f"GET /{c.dp}?created_after=bad returns HTTP 400")
        q = S("q", "qa", ["test_api", "test_service"], "Add tests for the filter, the empty result and the invalid date.", ["b"], f"`{c.tc('test_api')}` and `{c.tc('test_service')}` pass")
        return Sc("feature", req, [a, b, q])
    a = S("a", c.L, ["repo", "service"], "Add created_after to the repository query and service list method.", [], f"`{c.tc('test_service')}` passes with a created_after case")
    b = S("b", c.L, ["api"], "Parse and validate the created_after query parameter in the route.", ["a"], f"GET /{c.dp}?created_after=bad returns HTTP 400")
    q1 = S("q1", "qa", ["test_service"], "Add service tests for the date filter.", ["a"], f"`{c.tc('test_service')}` passes with new date-filter cases")
    q2 = S("q2", "qa", ["test_api"], "Add API tests for the filter and the 400 on a bad date.", ["b"], f"`{c.tc('test_api')}` passes with the new cases")
    return Sc("feature", req, [a, b, q1, q2])


BUGS = [
    ("page 2 of the {dp} list repeats the last row of page 1", "the pagination offset is computed as page*size-1", "paginat"),
    ("a {d} total with several lines is off by one cent", "float arithmetic in the total calculation is rounded inconsistently", "rounding"),
    ("searching {dp} by name is case-sensitive, so 'ABC' does not find 'abc'", "the name comparison lowercases only one side", "search"),
    ("archived {dp} still show up in the default list", "the default status filter in the list rule is missing", "archive filter"),
    ("creating a {d} with an empty title returns 500 instead of 422", "the validation rule in the service raises the wrong exception", "validation"),
    ("deleting a {d} twice returns 200 the second time instead of 404", "the delete rule does not check the row exists", "delete"),
]


def f_bug_backend(c):
    rng = c.rng
    sym, cause, tag = pick(rng, BUGS)
    sym = sym.format(d=c.d, dp=c.dp)
    req = pick(rng, [f"Bug ticket: {sym}. Reproduces every time in production and staging.", f"Bug report from support: {sym}. A stack trace/log excerpt points into the {c.D} business-rule code ({cause})."]) + noise(rng)
    a = S("fix", "debugger", ["service"], f"Reproduce the bug ({tag}) and fix the service rule so that the behavior is correct.", [], f"`{c.tc('test_service')}` passes and the reproduction case no longer fails", accept=["debugger", c.L])
    b = S("reg", "qa", ["test_service"], f"Add a regression test for the {tag} bug.", ["fix"], f"`{c.tc('test_service')}` passes and fails when the fix is reverted")
    return Sc("bug", req, [a, b])


def f_bug_cross(c):
    rng = c.rng
    req = pick(rng, [
        f"Bug ticket: amounts on the {c.d} page look wrong. The list shows 1250 instead of $12.50, and the totals returned by the API are off by a cent for some {c.dp}. Both the server calculation and the table formatting contribute.",
        f"Bug: {c.d} money values are displayed 100x too large in the table and the API total is rounded down instead of half-up. Fix both sides.",
    ]) + noise(rng)
    a = S("fix", "debugger", ["service"], "Fix the total calculation to round half-up in cents.", [], f"`{c.tc('test_service')}` passes with a case totalling 12.505 to 12.51", accept=["debugger", c.L])
    b = S("ui", "ui", ["ui_list"], "Format the money column by dividing cents by 100 and showing two decimals with a currency symbol.", [], ui_acc(c, "$12.50 for a value of 1250 cents"), accept=["ui", "debugger"])
    q = S("qa", "qa", ["test_service"], "Add regression tests for the rounding cases.", ["fix"], f"`{c.tc('test_service')}` passes and covers half-up rounding")
    return Sc("bug", req, [a, b, q])


def f_index(c):
    rng = c.rng
    req = pick(rng, [
        f"Performance ticket: GET /{c.dp}?status=open takes 4s on production (full scan on the {c.dp} table). Add an index and make sure the service uses a single query instead of one query per row.",
        f"The {c.d} list endpoint is slow for large accounts: sequential scan on {c.dp} and an N+1 pattern in the service. Fix both.",
    ]) + noise(rng)
    a = S("idx", "data", ["new_migration"], f"Create an index on {c.dp}(status, created_at) in a new migration.", [], f"the migration exits 0 on an empty database and `EXPLAIN` on the list query mentions the new index" if c.lang != "python" else "`python -m app.db migrate` exits 0 and `EXPLAIN QUERY PLAN` for the list query mentions the new index")
    b = S("q", c.L, ["service", "repo"], "Replace the per-row lookups with a single joined/batched query in the repository and service.", [], f"`{c.tc('test_service')}` passes and the list issues at most 2 SQL statements")
    t = S("t", "qa", ["test_service"], "Add a test that counts SQL statements for listing 20 rows.", ["q"], f"`{c.tc('test_service')}` passes with a statement-count assertion of <= 2")
    return Sc("feature", req, [a, b, t])


def f_health(c):
    rng = c.rng
    req = pick(rng, [
        f"Ops request: the {c.dp} service needs a real readiness check. /healthz currently always returns ok even when the database is down, so Kubernetes keeps routing traffic. Make it check the DB, wire it as a probe and a container healthcheck, and alert when it fails.",
        "Add a dependency-aware health endpoint (DB ping), wire it into the Docker image and k8s probes, add a test, and add an alert plus runbook entry for failing health.",
    ]) + noise(rng)
    a = S("h", c.L, ["health"], "Make the health endpoint ping the database and return 503 with a JSON body when it fails.", [], "GET /healthz returns 200 with the DB up and 503 when the DB connection is closed")
    d = S("d", "devops", ["dockerfile", "k8s"], "Add a HEALTHCHECK to the Dockerfile and readiness/liveness probes to the Deployment pointing at /healthz.", ["h"], "`docker build .` succeeds and deployment.yaml contains readinessProbe with path /healthz")
    q = S("q", "qa", ["test_api"], "Add tests for the healthy and failing-database cases.", ["h"], f"`{c.tc('test_api')}` passes with a 200 and a 503 case")
    o = S("o", "ops", ["alerts", "runbook"], "Add an alert on sustained readiness failures and a runbook section for it.", ["h"], "ops/alerts.yaml contains a rule on healthz failures and docs/runbook.md has a matching section")
    return Sc("feature", req, [a, d, q, o])


def f_flag(c):
    rng = c.rng
    req = pick(rng, [
        f"Rollout request: we are adding a bulk-archive option for {c.dp}. Put it behind a feature flag `bulk_archive_{c.d}` (off by default), enforce it in the service and the API, hide the button in the UI when off, test both states, and document how to turn it on and roll back.",
        f"Ship the new {c.d} archive-all action behind a flag defaulting to off: flag config, server-side check, UI gating, tests, and a rollback note for on-call.",
    ]) + noise(rng)
    a = S("cfg", c.L, ["config", "flags"], f"Define the `bulk_archive_{c.d}` flag (default false) in settings and the flag helper.", [], f"unit check: the flag helper returns False by default and True when env var is set (`{c.tc('test_service')}`)")
    b = S("svc", c.L, ["service", "api"], "Reject bulk archive with 403 when the flag is off; implement the action when on.", ["cfg"], f"POST /{c.dp}/archive-all returns 403 with the flag off and 200 with it on")
    u = S("ui", "ui", ["ui_list", "api_client"], "Show the Archive all button only when the server reports the flag as enabled.", ["svc"], ui_acc(c, "the Archive all button only when the flag is on"))
    q = S("qa", "qa", ["test_service"], "Test both flag states in the service.", ["svc"], f"`{c.tc('test_service')}` passes with flag-on and flag-off cases")
    o = S("ops", "ops", ["runbook"], "Document how to enable the flag and how to roll back.", ["cfg"], "docs/runbook.md contains a section naming the flag and the rollback steps")
    return Sc("feature", req, [a, b, u, q, o])


def f_ratelimit(c):
    rng = c.rng
    req = pick(rng, [
        f"Security ticket: POST /{c.dp} can be hammered by one client. Add a per-IP rate limit (60 requests/minute, configurable), return 429 with Retry-After, test it, add an alert on sustained 429s with a runbook note, and have the change security-reviewed before merge.",
        f"Add rate limiting to the {c.d} create endpoint (configurable limit), tests, an alert for abuse, and a security review of the limiter.",
    ]) + noise(rng)
    a = S("rl", c.L, ["middleware", "config"], "Implement a per-IP token-bucket limiter and add the limit setting to the configuration.", [], "unit check: the 61st request in a minute is rejected by the limiter")
    b = S("api", c.L, ["api"], f"Apply the limiter to POST /{c.dp} and return 429 with a Retry-After header.", ["rl"], f"the 61st POST /{c.dp} within a minute returns HTTP 429 with Retry-After")
    t = S("t", "qa", ["test_api"], "Add API tests for under-limit, over-limit and reset.", ["api"], f"`{c.tc('test_api')}` passes with a 429 case")
    o = S("o", "ops", ["alerts", "runbook"], "Add an alert for sustained 429s and a runbook note on tuning the limit.", ["rl"], "ops/alerts.yaml has a 429 rate rule and docs/runbook.md explains the limit setting")
    r = S("rev", "reviewer", [], "Security-review the limiter for bypass via X-Forwarded-For, memory growth and race conditions.", ["api", "t", "o"], "review comments list any bypass or unbounded-memory issue, or state explicitly that none were found", refs=["middleware", "api", "config"])
    return Sc("feature", req, [a, b, t, o, r])


def f_depupgrade(c):
    rng = c.rng
    lib = "pydantic 1.x to 2.x" if c.lang == "python" else "Spring Boot 2.7 to 3.2"
    req = pick(rng, [
        f"Maintenance: upgrade {lib}. Bump the dependency, fix the code that breaks (validation/serialization of {c.D}), make sure tests pass and update CI so the new version is exercised.",
        f"Security advisory: we must move from {lib} this week. Update the build file, adapt the {c.D} service and schemas, verify tests, and update the CI workflow.",
    ]) + noise(rng)
    a = S("dep", "devops", ["deps"], "Bump the dependency version in the build file.", [], "the dependency install step (`pip install -r requirements.txt` / `mvn -q dependency:resolve`) exits 0 with the new version")
    b = S("fix", c.L, ["service", "dto"], f"Adapt the {c.D} service and schemas to the new major version API.", ["dep"], f"`{c.tc('test_service')}` passes with the new version")
    t = S("t", "qa", ["test_service"], "Update and extend tests for the changed validation/serialization behavior.", ["fix"], f"`{c.tc('test_service')}` passes and covers serialization of a {c.d}")
    ci = S("ci", "devops", ["ci"], "Update the CI workflow to build/test with the new version and cache dependencies.", ["dep"], "ci.yml contains the new version and the workflow file passes `actionlint`")
    return Sc("feature", req, [a, b, t, ci])


def f_hard_full(c):
    rng = c.rng
    variant = rng.randrange(3)
    req = pick(rng, [
        f"Epic: add `{c.f}` ({c.fl}) to {c.dp} across the stack and ship it safely. Needs a DB migration, model/repo/service/API changes, UI form and list changes, API and service tests, a new env var `{c.d.upper()}_{c.f.upper()}_DEFAULT` wired in the k8s Deployment and read from config, an alert for validation-error spikes with a runbook entry" + (", and a final code review before merge." if variant < 2 else "."),
        f"Large feature: track `{c.f}` ({c.fl}) on every {c.d}. Include migration, backend, frontend, tests, deployment env var `{c.d.upper()}_{c.f.upper()}_DEFAULT`, ops alerting and runbook" + (" and a reviewer pass." if variant < 2 else "."),
    ]) + noise(rng)
    mig = S("mig", "data", ["new_migration"], f"Add column `{c.f}` {c.ft} with a default to `{c.dp}` in a new migration.", [], migacc(c))
    mdl = S("mdl", c.L, ["model", "repo"], f"Add `{c.f}` to the model and repository queries.", ["mig"], f"`{c.tc('test_service')}` passes when saving and reloading `{c.f}`")
    svc = S("svc", c.L, ["service", "dto", "config"], f"Validate `{c.f}`, apply the default from the `{c.d.upper()}_{c.f.upper()}_DEFAULT` setting and expose it in the schema.", ["mdl"], f"`{c.tc('test_service')}` passes and a {c.d} created without `{c.f}` gets the configured default")
    api = S("api", c.L, ["api"], f"Pass `{c.f}` through create/update/read in the /{c.dp} routes.", ["svc"], f"GET /{c.dp}/<id> returns `{c.f}` and HTTP 200")
    steps = [mig, mdl, svc, api]
    rev_deps = ["svc", "api"]
    if variant != 2:
        pass
    ui = S("ui", "ui", ["api_client", "ui_form", "ui_list"], f"Add `{c.f}` to the type, form and list.", ["api"], ui_acc(c, f"a {c.fl} column"))
    qs = S("qs", "qa", ["test_service"], f"Add service tests for `{c.f}` validation and default.", ["svc"], f"`{c.tc('test_service')}` passes with validation and default cases")
    qa = S("qa", "qa", ["test_api"], f"Add API round-trip tests for `{c.f}`.", ["api"], f"`{c.tc('test_api')}` passes and asserts `{c.f}` is returned")
    dv = S("dv", "devops", ["k8s"], f"Add the `{c.d.upper()}_{c.f.upper()}_DEFAULT` env var to the Deployment.", ["svc"], f"deployment.yaml sets `{c.d.upper()}_{c.f.upper()}_DEFAULT` in the container env")
    op = S("op", "ops", ["alerts", "runbook"], f"Add an alert for validation-error spikes on `{c.f}` and a runbook entry.", ["api"], f"ops/alerts.yaml contains a rule for `{c.f}` validation errors and docs/runbook.md documents it")
    steps += [ui, qs, qa, dv, op]
    if variant < 2:
        steps.append(S("rev", "reviewer", [], f"Review the full change for migration safety, validation gaps and config defaults.", ["ui", "qs", "qa", "dv", "op"], "review lists blocking issues or states that migration, validation and config defaults were checked", refs=["service", "api", "repo", "k8s"]))
    return Sc("feature", req, steps, hi=len(steps) + 2, extra=3)


def f_export(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature request: add a CSV export for {c.dp}: GET /{c.dp}/export.csv with the current filters, an Export button on the list page, tests, and a runbook note about large exports (timeouts).",
        f"Finance needs to download {c.dp} as CSV. Add the endpoint, reuse the CSV helper, add a button in the UI and tests; note limits in the runbook.",
    ]) + noise(rng)
    a = S("q", c.L, ["repo", "service"], "Add a streaming query and service method that yields filtered rows for export.", [], f"`{c.tc('test_service')}` passes with an export case returning all filtered rows")
    b = S("api", c.L, ["export", "api"], f"Add GET /{c.dp}/export.csv using the shared CSV helper with proper headers.", ["q"], f"GET /{c.dp}/export.csv returns HTTP 200 with Content-Type text/csv and a header row")
    u = S("ui", "ui", ["api_client", "ui_list"], "Add an Export button on the list page that downloads the CSV with current filters.", ["api"], ui_acc(c, "an Export button that links to the CSV endpoint"))
    t1 = S("t1", "qa", ["test_service"], "Add service tests for the export query.", ["q"], f"`{c.tc('test_service')}` passes")
    t2 = S("t2", "qa", ["test_api"], "Add API tests for the CSV content type, header row and quoting of commas.", ["api"], f"`{c.tc('test_api')}` passes and checks Content-Type text/csv")
    steps = [a, b, u, t1, t2]
    if rng.random() < 0.5:
        steps.append(S("o", "ops", ["runbook"], "Document export limits and what to do when exports time out.", ["api"], "docs/runbook.md contains an Exports section with the timeout and the row limit"))
    return Sc("feature", req, steps)


def f_softdelete(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature request: deleting a {c.d} must be reversible. Make delete a soft delete (deleted_at timestamp), hide deleted rows from lists, add a Restore action in the UI, test it, and document the restore procedure for support.",
        f"Replace hard deletes of {c.dp} with soft deletes: DB column, repository/service/API behavior, a restore button in the list, tests, and a support runbook entry.",
    ]) + noise(rng)
    a = S("mig", "data", ["new_migration"], f"Add nullable `deleted_at` TIMESTAMP to `{c.dp}` in a new migration.", [], migacc(c).replace(f"`{c.f}`", "`deleted_at`"))
    b = S("mdl", c.L, ["model", "repo"], "Add deleted_at to the model; make delete set it and queries exclude deleted rows by default.", ["mig"], f"`{c.tc('test_service')}` passes with a test that deleted rows are not listed")
    s = S("svc", c.L, ["service", "api"], f"Add restore to the service and POST /{c.dp}/<id>/restore; DELETE becomes a soft delete.", ["mdl"], f"DELETE then GET /{c.dp}/<id> returns 404 and POST /{c.dp}/<id>/restore returns 200")
    u = S("ui", "ui", ["ui_list", "api_client"], "Add a Restore action for deleted rows and a Show deleted toggle in the list.", ["svc"], ui_acc(c, "a Restore button for deleted rows"))
    q = S("qa", "qa", ["test_service", "test_api"], "Add tests for soft delete, restore and the default exclusion.", ["svc"], f"`{c.tc('test_service')}` and `{c.tc('test_api')}` pass")
    o = S("ops", "ops", ["runbook"], "Document the support procedure to restore an accidentally deleted record.", ["svc"], "docs/runbook.md has a Restore deleted records section with the endpoint call")
    return Sc("feature", req, [a, b, s, u, q, o])


# singles for web stack: (request, role, spec, accept, goal, acc)
def singles_web(c):
    d, dp, D, L = c.d, c.dp, c.D, c.L
    tcs, tca = c.tc("test_service"), c.tc("test_api")
    return [
        (f"Change the default page size of GET /{dp} from 20 to 50. Nothing else.", "config", L, [L], "Change the default page size setting from 20 to 50.", f"GET /{dp} without a size parameter returns up to 50 items (`{tca}`)"),
        (f"Add an info log line when a {d} is deleted (id and actor). One-line change.", "service", L, [L], "Log the deleted id and actor at INFO in the delete path.", f"deleting a {d} writes a log line containing the id (`{tcs}` passes)"),
        (f"We have no test for rejecting an empty title in the {D} service. Add one.", "test_service", "qa", ["qa"], "Add a test that creating a record with an empty title is rejected.", f"`{tcs}` passes with the new case"),
        (f"UI nit: right-align the amount column in the {d} table.", "ui_list", "ui", ["ui"], "Right-align the amount column cells and header.", ui_acc(c, "the amount column right-aligned")),
        (f"UI copy change: the {d} form label 'Title' should read 'Name'.", "ui_form", "ui", ["ui"], "Rename the Title label to Name in the form.", ui_acc(c, "a label reading Name")),
        (f"DB: add an index on {dp}(created_at). Nothing else.", "new_migration", "data", ["data"], f"Create an index on {dp}(created_at) in a new migration.", "the migration applies cleanly on an empty database and the index exists in the schema"),
        ("Security hygiene: the container runs as root. Make the Dockerfile use a non-root user.", "dockerfile", "devops", ["devops"], "Add a non-root USER to the Dockerfile.", "`docker run --rm <image> id -u` prints a non-zero uid"),
        ("CI is slow: cache the dependency install step in the CI workflow.", "ci", "devops", ["devops"], "Add dependency caching to the CI workflow.", "ci.yml contains an actions/cache step keyed on the lockfile and passes `actionlint`"),
        ("On-call asks for a runbook section: how to drain and replay stuck jobs.", "runbook", "ops", ["ops"], "Write the drain-and-replay section in the runbook.", "docs/runbook.md contains a Drain and replay section with the exact commands"),
        ("The p95 latency alert is too noisy. Raise its threshold from 500ms to 800ms.", "alerts", "ops", ["ops"], "Raise the p95 latency threshold to 800ms.", "ops/alerts.yaml shows threshold 800ms for the latency rule"),
        (f"Please review {D}Service/the {d} service for race conditions and N+1 queries and report findings. No code changes requested.", "service", "reviewer", ["reviewer"], f"Review the {d} service for races and N+1 queries and list findings.", "review output lists each finding with file and line, or states none were found"),
        (f"Bug: listing {dp} with page=0 throws an exception. The stack trace points to the pagination helper in the service. Fix it; tests already exist and just need to be run.", "service", "debugger", ["debugger", L], "Treat page=0 as page 1 in the pagination helper.", f"GET /{dp}?page=0 returns HTTP 200 and `{tcs}` passes"),
        (f"UI bug: dates in the {d} table render one day early for users west of UTC. Parsing in the list page treats date-only strings as UTC.", "ui_list", "ui", ["ui", "debugger"], "Parse date-only strings as local dates when rendering the table.", ui_acc(c, "2024-03-05 as Mar 5 in a UTC-8 browser")),
        (f"UI bug: double-clicking Save on the {d} form creates two {dp}. Disable the submit button while the request is pending.", "ui_form", "ui", ["ui", "debugger"], "Disable the submit button while saving.", ui_acc(c, "a disabled Save button during the request")),
        ("Dependabot: pin the vulnerable library to the patched version in the build file.", "deps", "devops", ["devops"], "Pin the vulnerable dependency to the patched release.", "the dependency resolution command exits 0 and lists the patched version"),
        ("The pods get OOM-killed. Raise the memory limit in the Deployment from 256Mi to 512Mi.", "k8s", "devops", ["devops"], "Raise the memory limit to 512Mi.", "deployment.yaml shows limits.memory 512Mi"),
        ("Allow the new admin site https://admin.example.com in the CORS origins setting.", "config", L, [L], "Add the admin origin to the CORS allow-list.", "a request with that Origin header gets Access-Control-Allow-Origin in the response"),
        ("Accessibility: the focus ring is invisible on buttons. Fix the global CSS.", "ui_css", "ui", ["ui"], "Add a visible :focus-visible outline for buttons.", ui_acc(c, "a visible focus outline on buttons")),
    ]


WEB_FAMILIES = [
    ("add_field_full", f_add_field_full, 14), ("add_field_backend", f_add_field_backend, 10), ("filter", f_filter, 10),
    ("bug_backend", f_bug_backend, 10), ("bug_cross", f_bug_cross, 6), ("index", f_index, 7),
    ("health", f_health, 8), ("flag", f_flag, 8), ("ratelimit", f_ratelimit, 6), ("depupgrade", f_depupgrade, 6),
    ("hard_full", f_hard_full, 12), ("export", f_export, 8), ("softdelete", f_softdelete, 6),
]


# ---------------------------------------------------------------- ETL families
def e_add_column(c):
    rng = c.rng
    req = pick(rng, [
        f"Data request: the source now sends `{c.f}` ({c.fl}). Land it in raw_{c.dp}, carry it through ingest and transform, and add per-day counts of it to the {c.d}_daily model. Update the data dictionary and cover each stage with tests.",
        f"Analytics needs `{c.f}` in {c.d}_daily. Add it to the raw table, ingest, transform and the daily SQL model, document it and test all stages.",
    ]) + noise(rng)
    a = S("raw", "data", ["raw_schema"], f"Add column `{c.f}` {c.ft} to the raw_{c.dp} DDL.", [], f"loading `{c.p('raw_schema')}` into SQLite exits 0 and the table has column `{c.f}`")
    b = S("ing", "python", ["ingest"], f"Read `{c.f}` from the source rows, validate it and load it into raw_{c.dp}.", ["raw"], f"`pytest {c.p('test_ingest')} -q` passes with a row containing `{c.f}`")
    t = S("tr", "python", ["transform"], f"Carry `{c.f}` into staging_{c.dp} in the transform step.", ["raw"], f"`pytest {c.p('test_transform')} -q` passes and staging rows contain `{c.f}`")
    m = S("m", "data", ["model_sql"], f"Add per-day aggregation of `{c.f}` to {c.d}_daily.sql.", ["tr"], f"`pytest {c.p('test_sql')} -q` passes and {c.d}_daily has a column derived from `{c.f}`")
    t1 = S("t1", "qa", ["test_ingest"], f"Add ingest tests for rows with and without `{c.f}`.", ["ing"], f"`pytest {c.p('test_ingest')} -q` passes with both cases")
    t2 = S("t2", "qa", ["test_transform", "test_sql"], f"Add transform and SQL model tests for `{c.f}`.", ["tr", "m"], f"`pytest {c.p('test_transform')} {c.p('test_sql')} -q` passes")
    dd = S("dd", "data", ["dict"], f"Document `{c.f}` for raw, staging and {c.d}_daily in the data dictionary.", ["m"], f"docs/data_dictionary.md contains an entry for `{c.f}` in each table", accept=["data", "ops"])
    return Sc("feature", req, [a, b, t, m, t1, t2, dd])


def e_new_metric(c):
    rng = c.rng
    req = pick(rng, [
        f"Add a weekly rollup metric to the {c.d} daily model: 7-day rolling count per day. Test it, add it to the dashboard and the data dictionary, and make the DAG refresh it after the model builds.",
        f"New KPI: rolling 7-day total of {c.dp}. Implement in SQL, test, show on the dashboard, document, and schedule in the DAG.",
    ]) + noise(rng)
    a = S("m", "data", ["model_sql"], "Add a rolling 7-day window column to the daily SQL model.", [], f"`pytest {c.p('test_sql')} -q` passes and the new column equals the sum of the last 7 days on the fixture")
    t = S("t", "qa", ["test_sql"], "Add SQL model tests for the rolling window, including the first six days.", ["m"], f"`pytest {c.p('test_sql')} -q` passes with window edge cases")
    db = S("db", "data", ["dashboard"], "Add a dashboard tile querying the rolling column.", ["m"], "dashboards JSON is valid (`python -m json.tool`) and contains a tile querying the rolling column", accept=["data", "ui"])
    dd = S("dd", "data", ["dict"], "Document the rolling metric definition in the data dictionary.", ["m"], "docs/data_dictionary.md contains the rolling metric with its window definition", accept=["data", "ops"])
    dg = S("dg", "python", ["dag"], "Add a task to the DAG that refreshes the rolling metric after the model build.", ["m"], f"`python -c 'import airflow.dags.{c.d}_dag'` imports without error and the DAG lists the new task", accept=["python", "data"])
    return Sc("feature", req, [a, t, db, dd, dg])


def e_bug(c):
    rng = c.rng
    req = pick(rng, [
        f"Bug ticket: re-running the {c.d} ingest for the same day duplicates rows in staging_{c.dp}, so {c.d}_daily counts double. The dedupe in the transform step compares the wrong key. Fix it, add a test, and write the backfill/cleanup procedure in the runbook.",
        f"Data quality bug: {c.d}_daily doubles after a retry. Root cause is in the transform dedupe. Fix it, add a regression test, and document how to clean up affected days.",
    ]) + noise(rng)
    a = S("fix", "debugger", ["transform"], "Fix the dedupe key in the transform so reruns are idempotent.", [], f"`pytest {c.p('test_transform')} -q` passes and running the transform twice yields the same row count", accept=["debugger", "python"])
    t = S("t", "qa", ["test_transform"], "Add a regression test that runs the transform twice and asserts no duplicates.", ["fix"], f"`pytest {c.p('test_transform')} -q` passes and fails without the fix")
    o = S("o", "ops", ["runbook"], "Document how to clean up and backfill days affected by duplicated rows.", ["fix"], "docs/runbook.md contains a Duplicate rows cleanup section with the SQL and the DAG backfill command")
    return Sc("bug", req, [a, t, o])


def e_late(c):
    rng = c.rng
    req = pick(rng, [
        f"Late-arriving {c.dp} data currently gets dropped. Add a configurable lookback window (days) so ingest and transform reprocess the window, update the model to restate affected days, make the DAG pass the window, test ingest and transform, add a freshness alert and runbook notes, and get a reviewer to check idempotency.",
        f"Handle late {c.d} events: lookback setting, ingest + transform reprocessing, restated daily model, DAG wiring, tests, alerting/runbook, and a final idempotency review.",
    ]) + noise(rng)
    a = S("cfg", "python", ["config"], "Add LOOKBACK_DAYS (default 3) to the pipeline config.", [], "unit check: the config exposes LOOKBACK_DAYS == 3 by default and honors an env override")
    b = S("ing", "python", ["ingest"], "Make ingest reprocess source files within the lookback window.", ["cfg"], f"`pytest {c.p('test_ingest')} -q` passes with a late file inside the window")
    t = S("tr", "python", ["transform"], "Make the transform restate staging rows for days inside the window.", ["cfg"], f"`pytest {c.p('test_transform')} -q` passes with a restated day")
    m = S("m", "data", ["model_sql"], f"Make {c.d}_daily recompute days inside the lookback window.", ["tr"], f"`pytest {c.p('test_sql')} -q` passes with a restated day")
    dg = S("dg", "python", ["dag"], "Pass the lookback window to the DAG tasks and raise retries.", ["cfg"], f"the DAG file imports without error and tasks receive LOOKBACK_DAYS (`pytest tests -q` passes)", accept=["python", "data"])
    q1 = S("q1", "qa", ["test_ingest"], "Add ingest tests for late files inside and outside the window.", ["ing"], f"`pytest {c.p('test_ingest')} -q` passes")
    q2 = S("q2", "qa", ["test_transform", "test_sql"], "Add transform and model tests for restated days and idempotency.", ["tr", "m"], f"`pytest {c.p('test_transform')} {c.p('test_sql')} -q` passes")
    o = S("o", "ops", ["alerts", "runbook"], "Add a freshness alert and runbook notes for the lookback window.", ["dg"], "ops/alerts.yaml has a freshness rule and docs/runbook.md explains the lookback window")
    r = S("rev", "reviewer", [], "Review the change for idempotency and double counting on reprocessing.", ["q1", "q2", "o"], "review states whether reprocessing is idempotent and lists any double-counting risk", refs=["ingest", "transform", "model_sql"])
    return Sc("feature", req, [a, b, t, m, dg, q1, q2, o, r], extra=3)


def singles_etl(c):
    return [
        (f"The {c.d} DAG should run hourly instead of daily. Change the schedule only.", "dag", "python", ["python", "data"], "Change the DAG schedule to hourly.", "the DAG file imports without error and its schedule is `@hourly`"),
        (f"Add a dedicated freshness alert: page when {c.d}_daily is more than 6 hours stale.", "alerts", "ops", ["ops"], "Add a 6-hour freshness alert for the daily model.", "ops/alerts.yaml contains a freshness rule with threshold 6h"),
        (f"Add a column `row_count_7d` to the {c.d}_daily SQL model. Nothing else changes.", "model_sql", "data", ["data"], "Add the 7-day row count column to the daily model.", f"`pytest {c.p('test_sql')} -q` passes"),
        ("Pin the base image of the pipeline Dockerfile to python:3.12-slim.", "dockerfile", "devops", ["devops"], "Pin the base image tag.", "Dockerfile FROM line equals python:3.12-slim"),
    ]


# ---------------------------------------------------------------- mixed
def m_event(c):
    rng = c.rng
    variant = rng.randrange(2)
    ui_txt = ", show the processing status badge in the UI" if variant == 0 else ""
    ops_txt = ", add alerts, a dashboard panel and a runbook entry for the queue" if variant == 0 else ""
    req = pick(rng, [
        f"Epic: when a {c.d} is created, the API must publish a `{c.d}.created` event to a new queue (with DLQ) and a Python worker must process it (status becomes processed). Needs infra for the queue, a status column, the event contract, the Java service/API, the worker, tests for both, k8s deployment updates{ui_txt}{ops_txt}.",
        f"Build async processing for new {c.dp}: terraform queue + DLQ, DB status column, shared event contract, Java producer, Python consumer, tests, k8s wiring{ui_txt}{ops_txt}.",
    ]) + noise(rng)
    tf = S("tf", "devops", ["tf_main", "tf_vars"], f"Add the {c.d} queue and its dead-letter queue to Terraform with variables for retention.", [], "`terraform validate` exits 0 and the plan shows two new queues")
    mg = S("mg", "data", ["new_migration"], f"Add a `status` column (default 'pending') to `{c.dp}` in a new migration.", [], migacc(c).replace(f"`{c.f}`", "`status`"))
    be = S("be", "java", ["j_model", "j_repo", "j_service", "j_dto", "contract"], f"Add status to the entity/DTO, define the `{c.d}.created` event in the contract and publish it from the service after create.", ["mg"], f"`mvn -q test -Dtest={c.D}ServiceTest` passes and verifies an event is published on create")
    api = S("api", "java", ["j_api", "j_cfg"], "Expose status on the REST API and configure the queue name.", ["be", "tf"], f"GET /{c.dp}/<id> returns status and `mvn -q test -Dtest={c.D}ControllerTest` passes")
    wk = S("wk", "python", ["w_handler", "w_cfg"], "Consume the event per the contract, mark the record processed, retry with backoff and send failures to the DLQ.", ["be", "tf"], f"`pytest {c.p('w_test')} -q` passes with a valid and a malformed message")
    qj = S("qj", "qa", ["j_test_service", "j_test_api"], "Add Java tests for event publishing and the status field.", ["api"], f"`mvn -q test -Dtest={c.D}ControllerTest` passes with a status assertion")
    qw = S("qw", "qa", ["w_test"], "Add worker tests: success, retry, poison message to DLQ.", ["wk"], f"`pytest {c.p('w_test')} -q` passes with three cases")
    dv = S("dv", "devops", ["k8s_worker", "k8s_api"], "Add the worker Deployment and the queue env vars to the API Deployment.", ["wk"], "deploy/k8s/worker.yaml contains QUEUE_NAME and `kubectl apply --dry-run=client` exits 0")
    steps = [tf, mg, be, api, wk, qj, qw, dv]
    if variant == 0:
        ui = S("ui", "ui", ["api_client", "ui_list"], "Show a status badge per row.", ["api"], ui_acc(c, "a status badge"))
        op = S("op", "ops", ["alerts", "runbook", "dashboard"], "Add alerts on queue depth and DLQ size, a dashboard panel and a DLQ replay runbook section.", ["tf"], "ops/alerts.yaml has DLQ and queue depth rules and the runbook has a replay section")
        steps += [ui, op]
    return Sc("feature", req, steps, extra=3)


def m_bug(c):
    rng = c.rng
    req = pick(rng, [
        f"Incident: some {c.d} events are being dead-lettered. The worker crashes when `amount` is null, and the API service sends null because the entity-to-DTO mapping drops the default. Fix both sides, add regression tests for each, and add DLQ replay steps to the runbook.",
        f"Bug: worker rejects {c.d}.created events with null `amount`; the Java service emits them since the default is not applied. Fix the worker and the service, test both, document replay.",
    ]) + noise(rng)
    a = S("w", "debugger", ["w_handler"], "Make the handler tolerate a null amount (treat as 0) instead of raising.", [], f"`pytest {c.p('w_test')} -q` passes with a null-amount message", accept=["debugger", "python"])
    b = S("j", "debugger", ["j_service"], "Apply the default amount before publishing the event.", [], f"`mvn -q test -Dtest={c.D}ServiceTest` passes and the published event has a non-null amount", accept=["debugger", "java"])
    qa = S("qw", "qa", ["w_test"], "Add a worker regression test for a null amount.", ["w"], f"`pytest {c.p('w_test')} -q` passes")
    qb = S("qj", "qa", ["j_test_service"], "Add a service regression test asserting the event amount is never null.", ["j"], f"`mvn -q test -Dtest={c.D}ServiceTest` passes")
    o = S("o", "ops", ["runbook"], "Add the steps to replay dead-lettered messages after the fix.", ["w", "j"], "ops/runbooks file contains a Replay DLQ section with the command")
    return Sc("bug", req, [a, b, qa, qb, o])


def m_region(c):
    rng = c.rng
    req = pick(rng, [
        f"Ops project: launch the {c.dp} platform in eu-west-1. Terraform needs region variables and resources, k8s manifests need region env, CI should deploy to the new region, the API and worker configs need the regional endpoints, and ops needs alerts, a dashboard and a runbook section for the new region.",
        f"Add a second region (eu-west-1): infra variables and resources, deployments, CI matrix, service config for the regional queue endpoint, and alerts/runbook.",
    ]) + noise(rng)
    a = S("tf", "devops", ["tf_vars", "tf_main"], "Parameterize the region and add the eu-west-1 resources.", [], "`terraform validate` exits 0 and `terraform plan -var region=eu-west-1` shows the new resources")
    b = S("k", "devops", ["k8s_api", "k8s_worker"], "Add region env vars and a regional overlay to the Deployments.", ["tf"], "`kubectl apply --dry-run=client -f deploy/k8s` exits 0")
    ci = S("ci", "devops", ["ci"], "Add a region matrix to the CI deploy job.", [], "ci.yml contains the eu-west-1 matrix entry and passes `actionlint`")
    jc = S("jc", "java", ["j_cfg"], "Add the regional queue endpoint setting to the API config.", ["tf"], "the API starts with SPRING_PROFILES_ACTIVE=eu and `mvn -q test` passes")
    wc = S("wc", "python", ["w_cfg"], "Add the regional queue endpoint setting to the worker settings.", ["tf"], "`python -c 'import settings'` succeeds and the endpoint is read from the REGION env var")
    op = S("op", "ops", ["alerts", "dashboard", "runbook"], "Add region-labelled alerts, a dashboard variable and a failover runbook section.", ["tf"], "ops/alerts.yaml has region labels, the dashboard JSON validates, and the runbook has a Failover section")
    return Sc("feature", req, [a, b, ci, jc, wc, op], extra=2)


def m_obs(c):
    rng = c.rng
    req = pick(rng, [
        f"Add observability to {c.dp}: Prometheus metrics (request count/latency) in the Java API and processed/failed counters in the worker, scrape annotations in k8s, alert rules, a dashboard, tests for the metrics, and a reviewer sign-off on label cardinality.",
        f"We lack metrics for {c.dp}. Instrument API and worker, expose them to Prometheus via k8s annotations, add alerts and a dashboard, test, and have the cardinality reviewed.",
    ]) + noise(rng)
    a = S("ja", "java", ["j_service", "j_api"], "Add request counter and latency timer metrics on the API.", [], f"GET /actuator/prometheus lists http_requests_total for /{c.dp} (`mvn -q test -Dtest={c.D}ControllerTest`)")
    b = S("wa", "python", ["w_handler"], "Add processed and failed counters to the worker.", [], f"`pytest {c.p('w_test')} -q` passes and the counters increment")
    d = S("d", "devops", ["k8s_api", "k8s_worker"], "Add Prometheus scrape annotations and a metrics port to both Deployments.", ["ja", "wa"], "both manifests contain prometheus.io/scrape: 'true' and `kubectl apply --dry-run=client` exits 0")
    o1 = S("o1", "ops", ["alerts"], "Add alerts on error ratio and worker failures.", ["ja", "wa"], "ops/alerts.yaml contains rules referencing the new metric names")
    o2 = S("o2", "ops", ["dashboard"], "Add dashboard panels for request rate, latency and worker throughput.", ["ja", "wa"], "dashboard JSON validates with `python -m json.tool` and has panels for the new metrics")
    q1 = S("q1", "qa", ["j_test_api"], "Test that the metrics endpoint exposes the new series.", ["ja"], f"`mvn -q test -Dtest={c.D}ControllerTest` passes")
    q2 = S("q2", "qa", ["w_test"], "Test that worker counters increment on success and failure.", ["wa"], f"`pytest {c.p('w_test')} -q` passes")
    r = S("rev", "reviewer", [], "Review metric label cardinality (no ids as labels) and naming.", ["d", "o1", "o2", "q1", "q2"], "review confirms no unbounded label values or lists the offending labels", refs=["j_service", "w_handler"])
    return Sc("feature", req, [a, b, d, o1, o2, q1, q2, r], extra=3)


def m_idtype(c):
    rng = c.rng
    req = pick(rng, [
        f"Migration project: change {c.d} ids from integer to UUID across the platform: DB migration, Java entity/service/API, the event contract and the Python worker, TS types in the UI, tests on both sides, a rollback plan in the runbook, and a reviewer check on the migration.",
        f"Switch {c.dp} primary keys to UUIDs. Everything that touches the id must change: schema, Java, the event contract and worker, UI types. Add tests and a rollback runbook; have the migration reviewed.",
    ]) + noise(rng)
    mg = S("mg", "data", ["new_migration"], f"Migrate {c.dp}.id from integer to UUID with a backfill and keep the old id in a legacy column.", [], "the migration applies on a database with sample rows and `\\d " + c.dp + "` shows id as uuid")
    jm = S("jm", "java", ["j_model", "j_repo"], "Change the entity and repository id types to UUID.", ["mg"], f"`mvn -q test -Dtest={c.D}ServiceTest` compiles and passes with UUID ids")
    js = S("js", "java", ["j_service", "j_dto", "j_api", "contract"], "Use UUIDs in the service, DTO, controller paths and the event contract.", ["jm"], f"`mvn -q test -Dtest={c.D}ControllerTest` passes and the contract JSON schema validates a UUID id")
    wk = S("wk", "python", ["w_handler"], "Parse UUID ids from events per the updated contract.", ["js"], f"`pytest {c.p('w_test')} -q` passes with a UUID event")
    ui = S("ui", "ui", ["api_client", "ui_list"], "Change the id type to string in the TypeScript client and list keys.", ["js"], ui_acc(c, "rows keyed by UUID strings"))
    qj = S("qj", "qa", ["j_test_service", "j_test_api"], "Update the Java tests to use UUID ids.", ["js"], f"`mvn -q test -Dtest={c.D}ControllerTest` passes")
    qw = S("qw", "qa", ["w_test"], "Update worker tests to use UUID ids and add a legacy-id rejection case.", ["wk"], f"`pytest {c.p('w_test')} -q` passes")
    o = S("o", "ops", ["runbook"], "Write the rollback plan for the id migration (restore legacy id column).", ["mg"], "runbook contains a Rollback section with the exact SQL steps")
    rv = S("rev", "reviewer", [], "Review the migration for lock duration, backfill correctness and rollback.", ["ui", "qj", "qw", "o"], "review lists migration risks or states lock time and rollback were checked", refs=["j_model", "contract"])
    return Sc("feature", req, [mg, jm, js, wk, ui, qj, qw, o, rv], extra=3)


def singles_mixed(c):
    return [
        ("Raise the worker retry count from 3 to 5.", "w_cfg", "python", ["python"], "Change the max retries setting to 5.", "settings shows max retries 5 and `python -c 'import settings'` succeeds"),
        ("Increase API replicas from 2 to 3 in the Deployment.", "k8s_api", "devops", ["devops"], "Set replicas to 3.", "api.yaml shows replicas: 3"),
        ("Lower the DLQ-size alert threshold from 100 to 20.", "alerts", "ops", ["ops"], "Change the DLQ alert threshold to 20.", "alerts yaml shows threshold 20 for the DLQ rule"),
        ("Terraform: raise queue message retention from 4 to 7 days.", "tf_vars", "devops", ["devops"], "Change the retention variable default to 7 days.", "`terraform validate` exits 0 and the variable default equals 604800 seconds"),
    ]


# ---------------------------------------------------------------- CLI
def c_flag(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature: `{c.d}tool list --sort <field>` should sort {c.dp} by a field (default order unchanged). Implement in the core, expose the flag in the CLI and add tests.",
        f"Add a --sort option to the list command of {c.d}tool with validation of the field name and tests.",
    ]) + noise(rng)
    a = S("core", "python", ["core"], "Add a sort_records(records, field) function that raises ValueError for unknown fields.", [], f"`pytest {c.p('test_core')} -q` passes with a sort case and an unknown-field case")
    b = S("cli", "python", ["cli"], "Add the --sort argument to the list subcommand and exit with code 2 on a bad field.", ["core"], f"`{c.d}tool list --sort nope` exits with code 2 and prints an error")
    t = S("t", "qa", ["test_core", "test_cli"], "Add tests for sorting and for the CLI flag.", ["cli"], f"`pytest {c.p('test_core')} {c.p('test_cli')} -q` passes")
    return Sc("feature", req, [a, b, t], extra=1)


def c_format(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature: add `--format csv` to {c.d}tool list. Implement the formatter, wire the CLI option, and add tests for the formatter (quoting) and the option.",
        f"{c.d}tool should print CSV with --format csv. Needs a CSV formatter, the CLI flag and tests.",
    ]) + noise(rng)
    a = S("fmt", "python", ["fmt"], "Add a csv formatter that quotes fields with commas and quotes.", [], f"`pytest {c.p('test_fmt')} -q` passes with a quoting case")
    b = S("cli", "python", ["cli"], "Add csv to the --format choices and dispatch to the formatter.", ["fmt"], f"`{c.d}tool list --format csv` exits 0 and prints a header line")
    t = S("t", "qa", ["test_fmt"], "Add formatter tests: header, quoting, empty list.", ["fmt"], f"`pytest {c.p('test_fmt')} -q` passes with three cases")
    return Sc("feature", req, [a, b, t], extra=1)


def c_bug(c):
    rng = c.rng
    req = pick(rng, [
        f"Bug: `{c.d}tool show <id>` exits with code 0 when the {c.d} does not exist, which breaks scripts. It should print an error and exit 1. The exit-code logic lives in the CLI entry point.",
        f"Bug ticket: missing id returns success exit status in {c.d}tool. Should be non-zero. Add a regression test.",
    ]) + noise(rng)
    a = S("fix", "debugger", ["cli"], "Return exit code 1 with an error message when the id is not found.", [], f"`{c.d}tool show 999` exits with code 1 and prints not found", accept=["debugger", "python"])
    t = S("t", "qa", ["test_cli"], "Add a regression test for the missing-id exit code.", ["fix"], f"`pytest {c.p('test_cli')} -q` passes")
    return Sc("bug", req, [a, t], extra=1)


def c_config(c):
    rng = c.rng
    req = pick(rng, [
        f"Feature: allow the default page size of {c.d}tool list to come from the config file and the {c.d.upper()}_PAGE_SIZE env var (env wins). Update config reading, use it in the core listing, test, and mention it in the README.",
        f"Make the list page size configurable via config file and env var in {c.d}tool, with tests.",
    ]) + noise(rng)
    a = S("cfg", "python", ["cfg"], "Read page_size from the config file and override it with the env var.", [], f"`pytest {c.p('test_core')} -q` passes with config and env precedence cases")
    b = S("core", "python", ["core"], "Use the configured page size in the listing function.", ["cfg"], f"`{c.d}tool list` prints at most the configured number of rows")
    t = S("t", "qa", ["test_core"], "Add tests for default, file and env page sizes.", ["core"], f"`pytest {c.p('test_core')} -q` passes with three cases")
    return Sc("feature", req, [a, b, t], extra=2)


def singles_cli(c):
    return [
        ("Bug: `list` prints the table header misaligned when a name has more than 20 characters. Pad using the longest value. Formatter only; tests will be updated separately.", "fmt", "python", ["python", "debugger"], "Compute column widths from the longest value instead of a fixed 20.", f"`{c.d}tool list` prints aligned columns with a 30-character name"),
        ("Add a test for formatting an empty record list.", "test_fmt", "qa", ["qa"], "Add a test that an empty list prints only the header.", f"`pytest {c.p('test_fmt')} -q` passes"),
        ("CI should also test on Python 3.13.", "ci", "devops", ["devops"], "Add 3.13 to the CI Python matrix.", "ci.yml matrix contains 3.13 and passes `actionlint`"),
        (f"The `--version` flag prints nothing. Make the CLI print the package version and exit 0.", "cli", "python", ["python", "debugger"], "Add a version action to the argparse parser.", f"`{c.d}tool --version` prints a semantic version and exits 0"),
    ]
