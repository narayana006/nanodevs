from _dsl import C, Q, T, d

TASKS = []
add = TASKS.append
W = ".github/workflows/ci.yml"
GL = ".gitlab-ci.yml"
SHA_BUILDX = "0d103c3126aa41d772a8362f6aa67afac040f80c"
SHA_LOGIN = "e92390c5fb421da1463c202d546fed0ec5c39f20"
SHA_META = "8e5442c4ef9f78752691e2d8f8d19755c6f78e81"
SHA_BUILD = "ca877d9245402d1537745e0e356eab47c3520991"
SHA_RELEASE = "c95fe1489396fe8a9eb87c0abf8aa5b2ef267fda"
SHA_AWS = "e3dd6a429d7300a6a4c196c26e071d42e0343502"


def steps_any(desc, f, path, op, value=None, **kw):
    return Q(desc, f, "jobs.*.steps[*]." + path, op, value, mode="any", **kw)


def jobs_each(desc, f, path, op, value=None, **kw):
    return Q(desc, f, path, op, value, each="jobs.*", **kw)


# ----------------------------------------------------------------- write
add(T("ci-gh-node-basic", "write", "ci", "easy", """
Write `.github/workflows/ci.yml` for a Node.js project: run on pushes to `main` and on pull requests; one job `test` on `ubuntu-latest` that checks out the code, installs Node 20 with npm dependency caching
(via setup-node's built-in cache), runs `npm ci`, `npm run lint` and `npm test`. The workflow token must be read-only (`contents: read`). Use `actions/checkout@v4` and `actions/setup-node@v4`.""",
 {W: d(r"""
name: CI
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm run lint
      - run: npm test
""")},
 [C("valid", "valid YAML", file=W), Q("push to main", W, "on.push.branches", "contains", "main"), C("contains", "pull_request trigger present", file=W, regex=r"^\s+pull_request:"),
  Q("contents read", W, "permissions.contents", "eq", "read"), C("ci_job_perms", "least-privilege permissions", file=W), C("ci_uses_pinned", "uses has refs", file=W),
  steps_any("setup-node@v4 with node 20", W, "uses", "regex", r"^actions/setup-node@v4$"), steps_any("npm cache enabled", W, "with.cache", "eq", "npm"), steps_any("node-version 20", W, "with.node-version", "eq", 20),
  steps_any("npm ci", W, "run", "regex", r"^npm ci$"), steps_any("lint", W, "run", "regex", r"npm run lint"), steps_any("test", W, "run", "regex", r"^npm test$"),
  Q("checkout v4", W, "jobs.test.steps[*].uses", "eq", "actions/checkout@v4", mode="any"), Q("runs on ubuntu", W, "jobs.test.runs-on", "eq", "ubuntu-latest")]))

add(T("ci-gh-python-matrix", "write", "ci", "medium", """
Write `.github/workflows/ci.yml` for a Python library: triggers on push to `main` and pull requests, read-only token, a single job `tests` with a build matrix over Python 3.10, 3.11, 3.12 (`fail-fast: false`),
`timeout-minutes: 15`, pip caching through `actions/setup-python@v5` (`cache: pip`), `pip install -r requirements.txt` and `pytest -q`. Name the matrix variable `python`.""",
 {W: d(r"""
name: tests
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      fail-fast: false
      matrix:
        python: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest -q
""")},
 [C("valid", "valid YAML", file=W), C("ci_job_perms", "permissions", file=W), Q("matrix python versions", W, "jobs.tests.strategy.matrix.python", "eq", ["3.10", "3.11", "3.12"]),
  Q("python versions are strings (3.10 != 3.1)", W, "jobs.tests.strategy.matrix.python[*]", "type", "str"), Q("fail-fast false", W, "jobs.tests.strategy.fail-fast", "eq", False),
  Q("timeout", W, "jobs.tests.timeout-minutes", "eq", 15), steps_any("setup-python v5", W, "uses", "eq", "actions/setup-python@v5"), steps_any("pip cache", W, "with.cache", "eq", "pip"),
  steps_any("matrix interpolated", W, "with.python-version", "regex", r"\$\{\{\s*matrix\.python\s*\}\}"), steps_any("install", W, "run", "regex", r"pip install -r requirements\.txt"), steps_any("pytest", W, "run", "regex", r"pytest"),
  C("ci_uses_pinned", "uses refs", file=W)]))

add(T("ci-gh-docker-publish", "write", "ci", "hard", """
Write `.github/workflows/release.yml`: when a tag matching `v*` is pushed, build the repository's Docker image and push it to GHCR as `ghcr.io/${{ github.repository }}`.
Use the exact pinned actions: `actions/checkout@v4`, `docker/setup-buildx-action@%s`, `docker/login-action@%s`, `docker/metadata-action@%s`, `docker/build-push-action@%s`.
Log in with the workflow's `GITHUB_TOKEN` (no PAT). Least privilege: top-level `permissions: contents: read`, and the build job additionally `packages: write`. Use the GitHub Actions cache for layers
(`cache-from: type=gha`, `cache-to: type=gha,mode=max`) and set `timeout-minutes: 30`.""" % (SHA_BUILDX, SHA_LOGIN, SHA_META, SHA_BUILD),
 {".github/workflows/release.yml": d(r"""
name: release
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
jobs:
  image:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@%s
      - uses: docker/login-action@%s
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@%s
        with:
          images: ghcr.io/${{ github.repository }}
      - uses: docker/build-push-action@%s
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
""" % (SHA_BUILDX, SHA_LOGIN, SHA_META, SHA_BUILD))},
 [C("valid", "valid", file=".github/workflows/release.yml"), Q("tag trigger v*", ".github/workflows/release.yml", "on.push.tags", "contains", "v*"),
  C("ci_uses_pinned", "third-party actions pinned to the given SHAs", file=".github/workflows/release.yml", sha=True),
  C("contains", "uses the exact SHAs", file=".github/workflows/release.yml", regex=SHA_BUILD),
  Q("top-level permissions read", ".github/workflows/release.yml", "permissions.contents", "eq", "read"),
  Q("job has packages: write", ".github/workflows/release.yml", "jobs.*.permissions.packages", "eq", "write"), C("ci_job_perms", "no other write permissions", file=".github/workflows/release.yml", allowed_writes=["packages"]),
  Q("login uses GITHUB_TOKEN", ".github/workflows/release.yml", "jobs.*.steps[*].with.password", "regex", r"secrets\.GITHUB_TOKEN", mode="any"),
  Q("registry ghcr.io", ".github/workflows/release.yml", "jobs.*.steps[*].with.registry", "eq", "ghcr.io", mode="any"),
  Q("push true", ".github/workflows/release.yml", "jobs.*.steps[*].with.push", "truthy", mode="any"), Q("gha cache from", ".github/workflows/release.yml", "jobs.*.steps[*].with.cache-from", "eq", "type=gha", mode="any"),
  Q("gha cache to max", ".github/workflows/release.yml", "jobs.*.steps[*].with.cache-to", "eq", "type=gha,mode=max", mode="any"), Q("timeout", ".github/workflows/release.yml", "jobs.*.timeout-minutes", "lte", 30),
  Q("image name", ".github/workflows/release.yml", "jobs.*.steps[*].with.images", "regex", r"^ghcr\.io/\$\{\{ github\.repository \}\}$", mode="any"),
  C("not_contains", "no PAT / static credentials", file=".github/workflows/release.yml", regex=r"secrets\.(?!GITHUB_TOKEN)\w+")]))

add(T("ci-gh-deploy-oidc", "write", "ci", "hard", """
Write `.github/workflows/deploy.yml` with two jobs. `test` (checkout, `make test`). `deploy` runs only after `test` succeeds, only for pushes to `main`, in the GitHub environment `production`,
authenticates to AWS with OIDC role assumption (action `aws-actions/configure-aws-credentials@%s`, `role-to-assume: arn:aws:iam::123456789012:role/gh-deploy`, `aws-region: eu-west-1`) - NO static AWS keys -
then runs `./scripts/deploy.sh`. Permissions: top-level `contents: read`; the deploy job needs `id-token: write` as well. Deploys must never run concurrently and a running deploy must not be cancelled
(`concurrency` group `deploy-production`, `cancel-in-progress: false`).""" % SHA_AWS,
 {".github/workflows/deploy.yml": d(r"""
name: deploy
on:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: deploy-production
  cancel-in-progress: false
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@%s
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gh-deploy
          aws-region: eu-west-1
      - run: ./scripts/deploy.sh
""" % SHA_AWS)},
 [C("valid", "valid", file=".github/workflows/deploy.yml"), C("ci_needs_acyclic", "needs graph valid", file=".github/workflows/deploy.yml"),
  Q("deploy needs test", ".github/workflows/deploy.yml", "jobs.deploy.needs", "in", ["test", ["test"]]), Q("deploy only on main", ".github/workflows/deploy.yml", "jobs.deploy.if", "regex", r"refs/heads/main"),
  Q("environment production", ".github/workflows/deploy.yml", "jobs.deploy.environment", "eq", "production"),
  Q("id-token write on deploy", ".github/workflows/deploy.yml", "jobs.deploy.permissions.id-token", "eq", "write"), Q("top-level contents read", ".github/workflows/deploy.yml", "permissions.contents", "eq", "read"),
  C("ci_job_perms", "no extra write scopes", file=".github/workflows/deploy.yml", allowed_writes=["id-token"]),
  Q("aws action pinned to SHA", ".github/workflows/deploy.yml", "jobs.deploy.steps[*].uses", "eq", "aws-actions/configure-aws-credentials@" + SHA_AWS, mode="any"),
  Q("role-to-assume", ".github/workflows/deploy.yml", "jobs.deploy.steps[*].with.role-to-assume", "eq", "arn:aws:iam::123456789012:role/gh-deploy", mode="any"),
  Q("region", ".github/workflows/deploy.yml", "jobs.deploy.steps[*].with.aws-region", "eq", "eu-west-1", mode="any"),
  C("not_contains", "no static AWS keys", file=".github/workflows/deploy.yml", regex=r"AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|aws-access-key-id|aws-secret-access-key", flags="mi"),
  Q("concurrency group", ".github/workflows/deploy.yml", "concurrency.group | jobs.deploy.concurrency.group", "eq", "deploy-production", mode="any"),
  Q("cancel-in-progress false", ".github/workflows/deploy.yml", "concurrency.cancel-in-progress | jobs.deploy.concurrency.cancel-in-progress", "eq", False, mode="any"),
  Q("runs deploy script", ".github/workflows/deploy.yml", "jobs.deploy.steps[*].run", "eq", "./scripts/deploy.sh", mode="any"), C("ci_uses_pinned", "pins", file=".github/workflows/deploy.yml", sha=True)]))

add(T("ci-gh-postgres-service", "write", "ci", "medium", """
Write `.github/workflows/ci.yml`: a job `integration` that runs the integration tests against a real PostgreSQL service container (`postgres:16-alpine`) with env `POSTGRES_PASSWORD: test` (CI-only value), port mapping `5432:5432`
and health options so the job waits for readiness: `--health-cmd "pg_isready -U postgres" --health-interval 5s --health-timeout 5s --health-retries 10`.
The test step runs `go test ./... -tags=integration` with `DATABASE_URL=postgres://postgres:test@localhost:5432/postgres?sslmode=disable`. Triggers: pull_request and push to main; `permissions: contents: read`; Go via `actions/setup-go@v5` with `go-version-file: go.mod` (module cache is on by default).""",
 {W: d(r"""
name: integration
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - run: go test ./... -tags=integration
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/postgres?sslmode=disable
""")},
 [C("valid", "valid YAML", file=W), Q("service image", W, "jobs.integration.services.postgres.image", "eq", "postgres:16-alpine"), Q("service password", W, "jobs.integration.services.postgres.env.POSTGRES_PASSWORD", "eq", "test"),
  Q("service port", W, "jobs.integration.services.postgres.ports[*]", "in", ["5432:5432", 5432], mode="any"), Q("health-cmd", W, "jobs.integration.services.postgres.options", "regex", r"--health-cmd[ =]\"?pg_isready"),
  Q("health retries", W, "jobs.integration.services.postgres.options", "regex", r"--health-retries[ =]10"), Q("health interval", W, "jobs.integration.services.postgres.options", "regex", r"--health-interval[ =]5s"),
  steps_any("setup-go v5 via go.mod", W, "with.go-version-file", "eq", "go.mod"), steps_any("go test integration", W, "run", "regex", r"go test \./\.\.\. -tags=integration"),
  steps_any("DATABASE_URL env", W, "env.DATABASE_URL", "regex", r"^postgres://postgres:test@localhost:5432/postgres\?sslmode=disable$"), C("ci_job_perms", "permissions", file=W), C("ci_uses_pinned", "pins", file=W)]))

add(T("ci-gh-reusable-workflow", "write", "ci", "hard", """
Implement a reusable workflow and its caller. `.github/workflows/build.yml` is triggered by `workflow_call` with an input `node-version` (type string, default `"20"`) and an OPTIONAL secret `npm_token`.
Its job `build` checks out, sets up Node with that input (with npm cache), runs `npm ci` with `NODE_AUTH_TOKEN` taken from the secret, then `npm run build`; permissions `contents: read`.
`.github/workflows/ci.yml` triggers on pull_request and calls the reusable workflow twice via a job per version: job `build-20` (`node-version: "20"`) and job `build-22` (`"22"`), passing `secrets: inherit`... NO - pass only `npm_token: ${{ secrets.NPM_TOKEN }}` explicitly (least privilege).""",
 {".github/workflows/build.yml": d(r"""
name: build
on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: "20"
    secrets:
      npm_token:
        required: false
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: npm
      - run: npm ci
        env:
          NODE_AUTH_TOKEN: ${{ secrets.npm_token }}
      - run: npm run build
"""), W: d(r"""
name: ci
on:
  pull_request:
permissions:
  contents: read
jobs:
  build-20:
    uses: ./.github/workflows/build.yml
    with:
      node-version: "20"
    secrets:
      npm_token: ${{ secrets.NPM_TOKEN }}
  build-22:
    uses: ./.github/workflows/build.yml
    with:
      node-version: "22"
    secrets:
      npm_token: ${{ secrets.NPM_TOKEN }}
""")},
 [C("valid", "build.yml valid", file=".github/workflows/build.yml"), C("valid", "ci.yml valid", file=W), Q("workflow_call input", ".github/workflows/build.yml", "on.workflow_call.inputs.node-version.type", "eq", "string"),
  Q("input default '20' (string)", ".github/workflows/build.yml", "on.workflow_call.inputs.node-version.default", "eq", "20"), Q("default is a string", ".github/workflows/build.yml", "on.workflow_call.inputs.node-version.default", "type", "str"),
  Q("npm_token secret optional", ".github/workflows/build.yml", "on.workflow_call.secrets.npm_token", "exists"), Q("uses input", ".github/workflows/build.yml", "jobs.build.steps[*].with.node-version", "regex", r"inputs\.node-version", mode="any"),
  Q("npm cache", ".github/workflows/build.yml", "jobs.build.steps[*].with.cache", "eq", "npm", mode="any"), Q("NODE_AUTH_TOKEN from secret", ".github/workflows/build.yml", "jobs.build.steps[*].env.NODE_AUTH_TOKEN", "regex", r"secrets\.npm_token", mode="any"),
  Q("build step", ".github/workflows/build.yml", "jobs.build.steps[*].run", "eq", "npm run build", mode="any"), Q("least privilege in build.yml", ".github/workflows/build.yml", "permissions.contents", "eq", "read"),
  Q("caller job build-20 calls local workflow", W, "jobs.build-20.uses", "eq", "./.github/workflows/build.yml"), Q("caller build-22", W, "jobs.build-22.uses", "eq", "./.github/workflows/build.yml"),
  Q("versions passed as strings", W, "jobs.build-20.with.node-version | jobs.build-22.with.node-version", "in", ["20", "22"]), Q("version types are strings", W, "jobs.build-20.with.node-version | jobs.build-22.with.node-version", "type", "str"),
  Q("explicit secret passing", W, "jobs.*.secrets.npm_token", "regex", r"secrets\.NPM_TOKEN"), C("not_contains", "no secrets: inherit", file=W, regex=r"secrets:\s*inherit")]))

add(T("ci-gh-pr-concurrency-paths", "write", "ci", "easy", """
Write `.github/workflows/ci.yml` running `make lint test` for pull requests that touch code. Skip the run for docs-only changes (`paths-ignore` for `docs/**` and `**.md`), cancel superseded runs for the same branch/PR
(`concurrency` group `${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true`), set `timeout-minutes: 10` and a read-only token.""",
 {W: d(r"""
name: ci
on:
  pull_request:
    paths-ignore:
      - "docs/**"
      - "**.md"
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  check:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - run: make lint test
""")},
 [C("valid", "valid", file=W), Q("paths-ignore docs", W, "on.pull_request.paths-ignore", "contains", "docs/**"), Q("paths-ignore md", W, "on.pull_request.paths-ignore", "contains", "**.md"),
  Q("concurrency group", W, "concurrency.group", "eq", "${{ github.workflow }}-${{ github.ref }}"), Q("cancel in progress", W, "concurrency.cancel-in-progress", "eq", True),
  jobs_each("timeout-minutes 10", W, "timeout-minutes", "lte", 10), C("ci_job_perms", "perms", file=W), steps_any("make lint test", W, "run", "regex", r"^make lint test$")]))

add(T("ci-gl-basic", "write", "ci", "medium", """
Write `.gitlab-ci.yml` for a Node project with stages `build`, `test`, `deploy`. Default image `node:20.14-alpine` (pinned). Cache `node_modules/` keyed on the lockfile
(`cache.key.files: [package-lock.json]`, policy pull-push). Job `build`: `npm ci` and `npm run build`, artifacts `dist/` expiring in 1 week. Job `test` (stage test): `npm test`, needs build, with `coverage` regex and junit report artifact
(`reports.junit: junit.xml`). Job `deploy` (stage deploy): runs `./deploy.sh` only on the default branch (use `rules`, not `only`), `when: manual`, in environment `production`. `interruptible: true` on build and test.""",
 {GL: d(r"""
stages: [build, test, deploy]
default:
  image: node:20.14-alpine
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - node_modules/
    policy: pull-push
build:
  stage: build
  interruptible: true
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
test:
  stage: test
  interruptible: true
  needs: [build]
  script:
    - npm test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    when: always
    reports:
      junit: junit.xml
deploy:
  stage: deploy
  script:
    - ./deploy.sh
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
""")},
 [C("valid", "valid YAML", file=GL), Q("stages", GL, "stages", "eq", ["build", "test", "deploy"]), Q("default image pinned", GL, "default.image", "eq", "node:20.14-alpine"),
  Q("cache keyed on lockfile", GL, "default.cache.key.files", "contains", "package-lock.json"), Q("cache node_modules", GL, "default.cache.paths", "contains", "node_modules/"),
  Q("build artifacts dist", GL, "build.artifacts.paths", "contains", "dist/"), Q("artifact expiry", GL, "build.artifacts.expire_in", "eq", "1 week"), Q("build script", GL, "build.script", "contains", "npm run build"),
  Q("test needs build", GL, "test.needs", "contains", "build"), Q("junit report", GL, "test.artifacts.reports.junit", "eq", "junit.xml"), Q("coverage regex", GL, "test.coverage", "regex", r"All files"),
  Q("deploy uses rules", GL, "deploy.rules[*].if", "regex", r"CI_DEFAULT_BRANCH|CI_COMMIT_BRANCH"), Q("deploy manual", GL, "deploy.rules[*].when", "eq", "manual"), Q("no only/except", GL, "deploy.only | deploy.except", "missing"),
  Q("environment production", GL, "deploy.environment.name | deploy.environment", "eq", "production", mode="any"), Q("interruptible build", GL, "build.interruptible", "eq", True), Q("interruptible test", GL, "test.interruptible", "eq", True)]))

add(T("ci-gh-release-job-split", "write", "ci", "medium", """
Write `.github/workflows/release.yml` triggered on tags `v*`. Job `build` (read-only token) builds with `make dist`, uploads `dist/` as artifact `dist` (`actions/upload-artifact@v4`, retention 7 days).
Job `publish` (`needs: build`) downloads it (`actions/download-artifact@v4`) and creates a GitHub release from the tag with `softprops/action-gh-release@%s` attaching `dist/*`.
Only `publish` gets `contents: write`; top-level permissions are `contents: read`.""" % SHA_RELEASE,
 {".github/workflows/release.yml": d(r"""
name: release
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make dist
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7
  publish:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: softprops/action-gh-release@%s
        with:
          files: dist/*
""" % SHA_RELEASE)},
 [C("valid", "valid", file=".github/workflows/release.yml"), Q("tag trigger", ".github/workflows/release.yml", "on.push.tags", "contains", "v*"), C("ci_needs_acyclic", "needs", file=".github/workflows/release.yml"),
  Q("publish needs build", ".github/workflows/release.yml", "jobs.publish.needs", "in", ["build", ["build"]]), Q("only publish has contents write", ".github/workflows/release.yml", "jobs.publish.permissions.contents", "eq", "write"),
  Q("build has no write", ".github/workflows/release.yml", "jobs.build.permissions", "regex", r"^$|^\{\}$|read", allow_empty=True), Q("top-level read", ".github/workflows/release.yml", "permissions.contents", "eq", "read"),
  C("ci_job_perms", "write only for contents", file=".github/workflows/release.yml", allowed_writes=["contents"]), Q("upload artifact v4", ".github/workflows/release.yml", "jobs.build.steps[*].uses", "eq", "actions/upload-artifact@v4", mode="any"),
  Q("retention 7", ".github/workflows/release.yml", "jobs.build.steps[*].with.retention-days", "eq", 7, mode="any"), Q("download artifact v4", ".github/workflows/release.yml", "jobs.publish.steps[*].uses", "eq", "actions/download-artifact@v4", mode="any"),
  Q("release action pinned", ".github/workflows/release.yml", "jobs.publish.steps[*].uses", "eq", "softprops/action-gh-release@" + SHA_RELEASE, mode="any"), Q("files dist/*", ".github/workflows/release.yml", "jobs.publish.steps[*].with.files", "eq", "dist/*", mode="any"),
  C("ci_uses_pinned", "pins", file=".github/workflows/release.yml", sha=True)]))

# ----------------------------------------------------------------- fix
add(T("ci-fix-permissions", "fix", "ci", "easy", """
The security team flagged this workflow for over-broad token permissions. Apply least privilege: remove `write-all`; the default for the workflow is `contents: read`; only the job `comment` (which posts a PR comment with
`gh pr comment`) additionally needs `pull-requests: write`. Keep all steps.""",
 {W: d(r"""
name: ci
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
  comment:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - run: gh pr comment "$PR" --repo "$REPO" --body "Tests passed"
        env:
          GH_TOKEN: ${{ github.token }}
          PR: ${{ github.event.number }}
          REPO: ${{ github.repository }}
""")},
 [C("valid", "valid", file=W), C("ci_job_perms", "permissions: write-all", file=W, bug=True, allowed_writes=["pull-requests"]), Q("default read", W, "permissions.contents", "eq", "read", bug=True),
  Q("comment job can write PRs", W, "jobs.comment.permissions.pull-requests", "eq", "write", bug=True), Q("test job has no write", W, "jobs.test.permissions", "regex", r"^$|^\{\}$|read", allow_empty=True),
  Q("steps kept", W, "jobs.test.steps[*].run", "eq", "make test", mode="any", keep=True), Q("comment step kept", W, "jobs.comment.steps[*].run", "regex", r"gh pr comment", mode="any", keep=True)],
 start={W: d(r"""
name: ci
on:
  pull_request:
permissions: write-all
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
  comment:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: gh pr comment "$PR" --repo "$REPO" --body "Tests passed"
        env:
          GH_TOKEN: ${{ github.token }}
          PR: ${{ github.event.number }}
          REPO: ${{ github.repository }}
""")}))

add(T("ci-fix-pin-actions", "fix", "ci", "medium", """
Supply-chain hardening: actions referenced by moving branches or without any ref can change under you. Pin them. First-party `actions/*` use their major tag (`@v4`); third-party actions must be pinned to a full commit SHA:
`softprops/action-gh-release` -> `%s`, `peaceiris/actions-gh-pages` -> `%s`. Do not change anything else.""" % (SHA_RELEASE, SHA_META),
 {W: d(r"""
name: docs
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mkdocs && mkdocs build
      - uses: peaceiris/actions-gh-pages@%s
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
""" % SHA_META)},
 [C("valid", "valid", file=W), C("ci_uses_pinned", "moving refs (@main/@master) and a ref-less action", file=W, sha=True, bug=True),
  steps_any("pages action pinned to SHA", W, "uses", "eq", "peaceiris/actions-gh-pages@" + SHA_META, bug=True), steps_any("checkout major tag", W, "uses", "regex", r"^actions/checkout@v\d+$"),
  steps_any("setup-python major tag", W, "uses", "regex", r"^actions/setup-python@v\d+$"), Q("build step kept", W, "jobs.docs.steps[*].run", "regex", r"mkdocs build", mode="any", keep=True),
  Q("publish_dir kept", W, "jobs.docs.steps[*].with.publish_dir", "eq", "./site", mode="any", keep=True)],
 start={W: d(r"""
name: docs
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@master
      - uses: actions/setup-python
        with:
          python-version: "3.12"
      - run: pip install mkdocs && mkdocs build
      - uses: peaceiris/actions-gh-pages@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./site
""")}))

add(T("ci-fix-script-injection", "fix", "ci", "hard", """
Security finding: this workflow interpolates attacker-controlled data (PR title, branch name, comment body) directly into shell scripts - classic GitHub Actions script injection.
Fix it the standard way: pass each value through the step's `env:` (`PR_TITLE`, `BRANCH`, `COMMENT`) and reference only the shell variables (quoted) inside `run:`. Behaviour stays the same.""",
 {W: d(r"""
name: triage
on:
  pull_request:
  issue_comment:
    types: [created]
permissions:
  contents: read
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Log PR info
        env:
          PR_TITLE: ${{ github.event.pull_request.title }}
          BRANCH: ${{ github.head_ref }}
        run: |
          echo "PR title: $PR_TITLE"
          echo "Branch: $BRANCH"
      - name: Echo comment
        env:
          COMMENT: ${{ github.event.comment.body }}
        run: echo "Comment: $COMMENT" >> "$GITHUB_STEP_SUMMARY"
""")},
 [C("valid", "valid", file=W), C("ci_no_untrusted_expr", "untrusted expressions inside run:", file=W, bug=True),
  Q("PR_TITLE env", W, "jobs.triage.steps[*].env.PR_TITLE", "regex", r"github\.event\.pull_request\.title", mode="any", bug=True),
  Q("BRANCH env", W, "jobs.triage.steps[*].env.BRANCH", "regex", r"github\.head_ref", mode="any", bug=True), Q("COMMENT env", W, "jobs.triage.steps[*].env.COMMENT", "regex", r"github\.event\.comment\.body", mode="any", bug=True),
  Q("run uses $PR_TITLE", W, "jobs.triage.steps[*].run", "regex", r"\$\{?PR_TITLE\}?", mode="any"), Q("run uses $BRANCH", W, "jobs.triage.steps[*].run", "regex", r"\$\{?BRANCH\}?", mode="any"),
  Q("run uses $COMMENT", W, "jobs.triage.steps[*].run", "regex", r"\$\{?COMMENT\}?", mode="any"), Q("permissions kept", W, "permissions.contents", "eq", "read", keep=True)],
 start={W: d(r"""
name: triage
on:
  pull_request:
  issue_comment:
    types: [created]
permissions:
  contents: read
jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - name: Log PR info
        run: |
          echo "PR title: ${{ github.event.pull_request.title }}"
          echo "Branch: ${{ github.head_ref }}"
      - name: Echo comment
        run: echo "Comment: ${{ github.event.comment.body }}" >> "$GITHUB_STEP_SUMMARY"
""")}))

add(T("ci-fix-pull-request-target", "fix", "ci", "hard", """
This workflow uses `pull_request_target` (which has secrets and a write token) and then checks out and runs the PR author's code - a well-known way to leak secrets from forks.
Fix it: the tests of untrusted PR code must run on the `pull_request` trigger with a read-only token and no secrets. Remove the explicit checkout of the PR head ref/repository (plain checkout of the merge commit is right),
do not expose `secrets.*` to the test job, and keep `make test`.""",
 {W: d(r"""
name: pr-tests
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - run: make test
""")},
 [C("valid", "valid", file=W), C("not_contains", "pull_request_target trigger", file=W, regex=r"pull_request_target", bug=True), C("not_contains", "checkout of PR head", file=W, regex=r"head\.(sha|ref|repo)|github\.head_ref", bug=True),
  C("contains", "uses pull_request", file=W, regex=r"^\s+pull_request:"), C("not_contains", "no secrets exposed", file=W, regex=r"secrets\.", bug=True), Q("read-only token", W, "permissions.contents", "eq", "read", bug=True),
  C("ci_job_perms", "no writes", file=W), steps_any("make test kept", W, "run", "eq", "make test", keep=True)],
 start={W: d(r"""
name: pr-tests
on:
  pull_request_target:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: make test
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
""")}))

add(T("ci-fix-slow-no-cache", "fix", "ci", "medium", """
CI takes 12 minutes per PR. Speed it up without changing what is tested: cache npm dependencies using setup-node's `cache: npm`, use the reproducible `npm ci` instead of `npm install`,
cancel superseded runs of the same ref (`concurrency` with `cancel-in-progress: true`), and add `timeout-minutes: 15` so hung jobs do not burn runner minutes.""",
 {W: d(r"""
name: ci
on:
  pull_request:
permissions:
  contents: read
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - run: npm test
""")},
 [C("valid", "valid", file=W), steps_any("npm cache", W, "with.cache", "eq", "npm", bug=True), steps_any("npm ci", W, "run", "regex", r"^npm ci", bug=True), C("not_contains", "no plain npm install", file=W, regex=r"run:\s*npm install\b", bug=True),
  Q("concurrency cancel", W, "concurrency.cancel-in-progress", "eq", True, bug=True), jobs_each("timeout 15", W, "timeout-minutes", "lte", 15, bug=True), steps_any("tests still run", W, "run", "regex", r"npm test", keep=True),
  C("ci_job_perms", "perms", file=W, keep=True)],
 start={W: d(r"""
name: ci
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install
      - run: npm test
""")}))

add(T("ci-fix-deploy-gating", "fix", "ci", "medium", """
Production got deployed from a feature branch before tests finished: `deploy` has no dependency on the test jobs and no branch condition. Fix the workflow: `deploy` must wait for BOTH `lint` and `test`
(`needs`), run only for pushes to `main` (`if: github.ref == 'refs/heads/main'`), and use the `production` environment. Nothing else changes.""",
 {W: d(r"""
name: pipeline
on:
  push:
  pull_request:
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make lint
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
  deploy:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
""")},
 [C("valid", "valid", file=W), C("ci_needs_acyclic", "needs", file=W), Q("deploy needs lint and test", W, "jobs.deploy.needs", "contains", "lint", bug=True), Q("also test", W, "jobs.deploy.needs", "contains", "test", bug=True),
  Q("branch condition", W, "jobs.deploy.if", "regex", r"refs/heads/main", bug=True), Q("environment", W, "jobs.deploy.environment", "eq", "production", bug=True),
  Q("deploy script kept", W, "jobs.deploy.steps[*].run", "eq", "./deploy.sh", mode="any", keep=True), Q("lint kept", W, "jobs.lint.steps[*].run", "eq", "make lint", mode="any", keep=True)],
 start={W: d(r"""
name: pipeline
on:
  push:
  pull_request:
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make lint
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
""")}))

add(T("ci-fix-hardcoded-creds", "fix", "ci", "medium", """
A hard-coded AWS key pair was committed in this workflow. Remove the literals: the job must authenticate through OIDC (role `arn:aws:iam::123456789012:role/gh-s3-sync`, region `us-east-1`) using
`aws-actions/configure-aws-credentials@%s`, which needs `permissions: id-token: write` (plus `contents: read`) on the job. The sync command stays.""" % SHA_AWS,
 {W: d(r"""
name: sync
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  sync:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@%s
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gh-s3-sync
          aws-region: us-east-1
      - run: aws s3 sync ./public s3://acme-static-site --delete
""" % SHA_AWS)},
 [C("valid", "valid", file=W), C("not_contains", "static AWS keys / secret literals", file=W, regex=r"AKIA[0-9A-Z]{8,}|AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|aws-secret-access-key|wJalr", flags="mi", bug=True),
  Q("id-token write", W, "jobs.sync.permissions.id-token", "eq", "write", bug=True), steps_any("OIDC action pinned", W, "uses", "eq", "aws-actions/configure-aws-credentials@" + SHA_AWS, bug=True),
  steps_any("role", W, "with.role-to-assume", "eq", "arn:aws:iam::123456789012:role/gh-s3-sync"), steps_any("region", W, "with.aws-region", "eq", "us-east-1"),
  steps_any("sync command kept", W, "run", "regex", r"aws s3 sync \./public s3://acme-static-site --delete", keep=True), C("ci_job_perms", "no write-all", file=W, allowed_writes=["id-token"])],
 start={W: d(r"""
name: sync
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    env:
      AWS_ACCESS_KEY_ID: AKIAIOSFODNN7EXAMPLE
      AWS_SECRET_ACCESS_KEY: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
      AWS_DEFAULT_REGION: us-east-1
    steps:
      - uses: actions/checkout@v4
      - run: aws s3 sync ./public s3://acme-static-site --delete
""")}))

add(T("ci-fix-gitlab-rules", "fix", "ci", "medium", """
This `.gitlab-ci.yml` still uses the deprecated `only`/`except` keywords, so merge-request pipelines run the deploy job. Migrate to `rules`: `test` runs for merge requests and for the default branch;
`deploy` runs ONLY for the default branch and manually. Also stop caching on every ref: cache key must be the lockfile (`key.files: [Gemfile.lock]`). Keep image, scripts and stages.""",
 {GL: d(r"""
image: ruby:3.3.4-slim
stages: [test, deploy]
cache:
  key:
    files:
      - Gemfile.lock
  paths:
    - vendor/bundle
test:
  stage: test
  script:
    - bundle install --path vendor/bundle
    - bundle exec rspec
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
deploy:
  stage: deploy
  script:
    - ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
""")},
 [C("valid", "valid", file=GL), Q("no only", GL, "test.only | deploy.only", "missing", bug=True), Q("no except", GL, "test.except | deploy.except", "missing", bug=True),
  Q("test runs for MRs", GL, "test.rules[*].if", "regex", r"merge_request_event", mode="any"), Q("test runs on default branch", GL, "test.rules[*].if", "regex", r"CI_DEFAULT_BRANCH|CI_COMMIT_BRANCH", mode="any"),
  Q("deploy only default branch", GL, "deploy.rules[*].if", "regex", r"CI_DEFAULT_BRANCH|CI_COMMIT_BRANCH == \"main\""), Q("deploy manual", GL, "deploy.rules[*].when", "eq", "manual"),
  Q("deploy not on MR", GL, "deploy.rules[*].if", "not_regex", r"merge_request_event"), Q("cache key on lockfile", GL, "cache.key.files", "contains", "Gemfile.lock", bug=True),
  Q("image kept", GL, "image", "eq", "ruby:3.3.4-slim", keep=True), Q("scripts kept", GL, "deploy.script", "contains", "./deploy.sh", keep=True)],
 start={GL: d(r"""
image: ruby:3.3.4-slim
stages: [test, deploy]
cache:
  key: "$CI_COMMIT_REF_SLUG"
  paths:
    - vendor/bundle
test:
  stage: test
  script:
    - bundle install --path vendor/bundle
    - bundle exec rspec
  only:
    - merge_requests
    - main
deploy:
  stage: deploy
  script:
    - ./deploy.sh
  except:
    - tags
  when: manual
""")}))

# ----------------------------------------------------------------- harden
add(T("ci-harden-workflow", "harden", "ci", "hard", """
Harden this release workflow end to end without changing what it builds: least-privilege permissions (top-level `contents: read`; `publish` may add `packages: write`), third-party actions pinned to SHAs
(`docker/login-action` -> `%s`, `docker/build-push-action` -> `%s`; `actions/checkout@v4` is fine), `persist-credentials: false` on checkout, `timeout-minutes` (<= 30) on every job,
a concurrency group `release-${{ github.ref }}` that does NOT cancel in-progress runs, and no attacker-controlled expressions interpolated into `run:` (use env). Triggers stay.""" % (SHA_LOGIN, SHA_BUILD),
 {".github/workflows/release.yml": d(r"""
name: release
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: docker/login-action@%s
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@%s
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
      - name: Announce
        env:
          TAG: ${{ github.ref_name }}
        run: echo "Released $TAG"
""" % (SHA_LOGIN, SHA_BUILD))},
 [C("valid", "valid", file=".github/workflows/release.yml"), C("ci_job_perms", "no write-all / over-broad token", file=".github/workflows/release.yml", bug=True, allowed_writes=["packages"]),
  Q("top-level read", ".github/workflows/release.yml", "permissions.contents", "eq", "read", bug=True), C("ci_uses_pinned", "unpinned third-party actions", file=".github/workflows/release.yml", sha=True, bug=True),
  Q("login pinned", ".github/workflows/release.yml", "jobs.publish.steps[*].uses", "eq", "docker/login-action@" + SHA_LOGIN, mode="any"),
  Q("build-push pinned", ".github/workflows/release.yml", "jobs.publish.steps[*].uses", "eq", "docker/build-push-action@" + SHA_BUILD, mode="any"),
  Q("persist-credentials false", ".github/workflows/release.yml", "jobs.publish.steps[*].with.persist-credentials", "eq", False, mode="any", bug=True),
  jobs_each("timeout", ".github/workflows/release.yml", "timeout-minutes", "lte", 30, bug=True), Q("concurrency group", ".github/workflows/release.yml", "concurrency.group", "eq", "release-${{ github.ref }}", bug=True),
  Q("no cancel", ".github/workflows/release.yml", "concurrency.cancel-in-progress", "eq", False, bug=True), C("ci_no_untrusted_expr", "untrusted expr", file=".github/workflows/release.yml", bug=True),
  Q("tag trigger kept", ".github/workflows/release.yml", "on.push.tags", "contains", "v*", keep=True)],
 start={".github/workflows/release.yml": d(r"""
name: release
on:
  push:
    tags: ["v*"]
permissions: write-all
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@master
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
      - name: Announce
        run: echo "Released ${{ github.event.head_commit.message }}"
""")}))

add(T("ci-harden-deploy-job", "harden", "ci", "hard", """
Harden the deploy workflow: the `deploy` job must (a) depend on `build`, (b) run only on `main`, (c) target the protected `production` environment, (d) use short-lived OIDC credentials
(`aws-actions/configure-aws-credentials@%s`, role `arn:aws:iam::123456789012:role/gh-prod-deploy`, region `eu-central-1`) instead of the stored keys, with `id-token: write` on that job only,
(e) never run two deploys at once (`concurrency: group: prod-deploy, cancel-in-progress: false`). Top-level token read-only. The deploy command `./ship.sh` stays.""" % SHA_AWS,
 {W: d(r"""
name: deploy
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make build
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    permissions:
      contents: read
      id-token: write
    concurrency:
      group: prod-deploy
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@%s
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gh-prod-deploy
          aws-region: eu-central-1
      - run: ./ship.sh
""" % SHA_AWS)},
 [C("valid", "valid", file=W), C("ci_needs_acyclic", "needs", file=W), Q("needs build", W, "jobs.deploy.needs", "in", ["build", ["build"]], bug=True), Q("main only", W, "jobs.deploy.if", "regex", r"refs/heads/main", bug=True),
  Q("environment production", W, "jobs.deploy.environment", "eq", "production", bug=True), C("not_contains", "static AWS keys", file=W, regex=r"AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|aws-access-key-id|aws-secret-access-key", flags="mi", bug=True),
  steps_any("OIDC action pinned", W, "uses", "eq", "aws-actions/configure-aws-credentials@" + SHA_AWS, bug=True), steps_any("role", W, "with.role-to-assume", "eq", "arn:aws:iam::123456789012:role/gh-prod-deploy"),
  steps_any("region", W, "with.aws-region", "eq", "eu-central-1"), Q("id-token write on deploy", W, "jobs.deploy.permissions.id-token", "eq", "write", bug=True), Q("top-level read", W, "permissions.contents", "eq", "read"),
  Q("build job has no id-token", W, "jobs.build.permissions.id-token", "missing"), C("ci_job_perms", "write scopes", file=W, allowed_writes=["id-token"]),
  Q("concurrency group", W, "concurrency.group | jobs.deploy.concurrency.group", "eq", "prod-deploy", mode="any", bug=True), Q("no cancel", W, "concurrency.cancel-in-progress | jobs.deploy.concurrency.cancel-in-progress", "eq", False, mode="any", bug=True),
  steps_any("ship kept", W, "run", "eq", "./ship.sh", keep=True)],
 start={W: d(r"""
name: deploy
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make build
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: ./ship.sh
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_DEFAULT_REGION: eu-central-1
""")}))

# ----------------------------------------------------------------- convert
add(T("ci-convert-gh-to-gitlab", "convert", "ci", "hard", """
Convert the GitHub Actions workflow in `.github/workflows/ci.yml` to an equivalent `.gitlab-ci.yml`: stages `lint`, `test`, `build`; default image `golang:1.22.5` (pinned); jobs `lint` (`go vet ./...`), `test` (`go test ./... -race`, needs lint),
`build` (`go build -o bin/app ./cmd/app`, needs test, artifact `bin/app` kept 1 week). Pipelines run for merge requests and the default branch (use `rules`, not only/except). Cache Go modules keyed on `go.sum` (`GOMODCACHE` set in `variables` to `$CI_PROJECT_DIR/.gomodcache`, cached path `.gomodcache/`).""",
 {GL: d(r"""
default:
  image: golang:1.22.5
variables:
  GOMODCACHE: $CI_PROJECT_DIR/.gomodcache
  GOFLAGS: -mod=readonly
stages: [lint, test, build]
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
cache:
  key:
    files:
      - go.sum
  paths:
    - .gomodcache/
lint:
  stage: lint
  script:
    - go vet ./...
test:
  stage: test
  needs: [lint]
  script:
    - go test ./... -race
build:
  stage: build
  needs: [test]
  script:
    - go build -o bin/app ./cmd/app
  artifacts:
    paths:
      - bin/app
    expire_in: 1 week
""")},
 [C("valid", "valid", file=GL), Q("stages", GL, "stages", "eq", ["lint", "test", "build"]), Q("pinned image", GL, "default.image | image", "eq", "golang:1.22.5", mode="any"),
  Q("lint script", GL, "lint.script", "contains", "go vet ./..."), Q("test script", GL, "test.script", "contains", "go test ./... -race"), Q("test needs lint", GL, "test.needs", "contains", "lint"),
  Q("build script", GL, "build.script", "contains", "go build -o bin/app ./cmd/app"), Q("build needs test", GL, "build.needs", "contains", "test"), Q("artifact bin/app", GL, "build.artifacts.paths", "contains", "bin/app"),
  Q("artifact expiry", GL, "build.artifacts.expire_in", "eq", "1 week"), Q("GOMODCACHE", GL, "variables.GOMODCACHE", "regex", r"\.gomodcache"), Q("cache key go.sum", GL, "cache.key.files | default.cache.key.files", "contains", "go.sum", mode="any"),
  Q("cache path", GL, "cache.paths | default.cache.paths", "contains", ".gomodcache/", mode="any"), C("not_contains", "uses rules not only/except", file=GL, regex=r"^\s+(only|except):", flags="m"),
  C("contains", "rules for merge requests", file=GL, regex=r"merge_request_event")],
 start={".github/workflows/ci.yml": d(r"""
name: ci
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.22.5"
      - run: go vet ./...
  test:
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.22.5"
      - run: go test ./... -race
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.22.5"
      - run: go build -o bin/app ./cmd/app
      - uses: actions/upload-artifact@v4
        with:
          name: app
          path: bin/app
          retention-days: 7
""")}))

add(T("ci-convert-script-to-workflow", "convert", "ci", "medium", """
The legacy pipeline is `ci.sh` run by cron. Convert it to a GitHub Actions workflow `.github/workflows/ci.yml` triggered by pushes to `main` and a nightly schedule (`cron: "0 3 * * *"`).
Split into jobs `lint`, `test` and `package` (package needs both), run each former command as its own step with Python 3.12 (`actions/setup-python@v5`, pip cache), install deps from `requirements.txt`, and upload `dist/` as an artifact named `package`. Least-privilege token.""",
 {W: d(r"""
name: ci
on:
  push:
    branches: [main]
  schedule:
    - cron: "0 3 * * *"
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: flake8 src
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt
      - run: pytest -q
  package:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt build
      - run: python -m build
      - uses: actions/upload-artifact@v4
        with:
          name: package
          path: dist/
""")},
 [C("valid", "valid", file=W), Q("push to main", W, "on.push.branches", "contains", "main"), Q("nightly cron", W, "on.schedule[*].cron", "eq", "0 3 * * *"), C("ci_job_perms", "permissions", file=W), C("ci_needs_acyclic", "needs", file=W),
  Q("package needs lint", W, "jobs.package.needs", "contains", "lint"), Q("package needs test", W, "jobs.package.needs", "contains", "test"), Q("flake8 step", W, "jobs.lint.steps[*].run", "regex", r"flake8 src", mode="any"),
  Q("pytest step", W, "jobs.test.steps[*].run", "regex", r"pytest -q", mode="any"), Q("build step", W, "jobs.package.steps[*].run", "regex", r"python -m build", mode="any"),
  Q("python 3.12 string", W, "jobs.*.steps[*].with.python-version", "eq", "3.12", mode="any"), Q("python-version is a string", W, "jobs.*.steps[*].with.python-version", "type", "str"),
  Q("pip cache", W, "jobs.*.steps[*].with.cache", "eq", "pip", mode="any"), Q("artifact package", W, "jobs.package.steps[*].with.name", "eq", "package", mode="any"), Q("artifact path dist/", W, "jobs.package.steps[*].with.path", "eq", "dist/", mode="any"),
  C("ci_uses_pinned", "pins", file=W)],
 start={"ci.sh": d(r"""
#!/bin/sh
# nightly + on-push pipeline (runs on the old build box)
set -e
pip install -r requirements.txt
flake8 src
pytest -q
pip install build
python -m build
cp -r dist /srv/artifacts/latest
""")}))
