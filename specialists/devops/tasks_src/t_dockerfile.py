from _dsl import C, T, d

BASE = C("df_base_pinned", "every FROM has an explicit, non-latest tag (or digest)")
NONROOT = C("df_user_nonroot", "final stage runs as a non-root USER")
EXEC = C("df_exec_form", "CMD/ENTRYPOINT use exec (JSON array) form")
HC = C("df_healthcheck", "final stage defines a HEALTHCHECK")
NOURLADD = C("df_no_add_url", "no ADD of remote URLs")

TASKS = []
add = TASKS.append

# ------------------------------------------------------------------ write from spec
add(T("df-node-basic", "write", "dockerfile", "easy", """
Write a `Dockerfile` for a Node.js 20 web service. Source layout: `package.json`, `package-lock.json`, `server.js`, `src/`.
Requirements: use a pinned Alpine-based Node 20 image (not :latest), work in /app, install only production dependencies
reproducibly from the lockfile, make sure editing source code does not invalidate the dependency-install layer, run as the
unprivileged `node` user, document port 3000, and start with `node server.js` in exec form.""",
 {"Dockerfile": d(r"""
FROM node:20-alpine3.19
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . .
USER node
EXPOSE 3000
CMD ["node", "server.js"]
""")},
 [BASE, C("df_from_regex", "uses an alpine variant", regex=r"alpine"), C("df_instr", "WORKDIR /app", instr="WORKDIR", regex=r"^/app/?$"),
  C("df_instr", "uses npm ci (not npm install) with prod-only flag", instr="RUN", regex=r"npm ci .*(--omit=dev|--only=production)|npm ci (--omit=dev|--only=production)"),
  C("df_copy_dot_last", "package manifests copied before install, source copied after", manifests=["package.json"], install_regex=r"npm ci"),
  NONROOT, C("df_instr", "EXPOSE 3000", instr="EXPOSE", regex=r"\b3000\b"), EXEC,
  C("df_instr", "CMD runs node server.js", instr="CMD", regex=r"node.*server\.js")]))

add(T("df-py-flask-gunicorn", "write", "dockerfile", "easy", """
Write a `Dockerfile` for a Flask app (`app.py` exposing `app`, plus `requirements.txt`). Use `python:3.12-slim` pinned to a
minor version tag, keep pip from leaving its cache in the image, copy requirements first for layer caching, create and switch
to a dedicated non-root user, expose 8000, add a HEALTHCHECK that works WITHOUT curl installed (python stdlib is fine), and
run `gunicorn -b 0.0.0.0:8000 app:app` in exec form.""",
 {"Dockerfile": d(r"""
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')"]
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
""").replace("python:3.12-slim", "python:3.12.4-slim")},
 [BASE, C("df_instr", "pip install uses --no-cache-dir", instr="RUN", regex=r"pip install .*--no-cache-dir|PIP_NO_CACHE_DIR"),
  C("df_copy_dot_last", "requirements.txt copied before pip install, source after", manifests=["requirements.txt"], install_regex=r"pip install"),
  C("df_instr", "a dedicated user is created", instr="RUN", regex=r"useradd|adduser"), NONROOT, C("df_user_before_cmd", "USER precedes CMD"),
  C("df_instr", "EXPOSE 8000", instr="EXPOSE", regex=r"\b8000\b"), HC,
  C("df_instr", "healthcheck must not depend on curl/wget (not installed in slim)", instr="HEALTHCHECK", regex=r"curl|wget", expect="absent"),
  EXEC, C("df_instr", "CMD starts gunicorn", instr="CMD", regex=r"gunicorn")]))

add(T("df-go-distroless", "write", "dockerfile", "medium", """
Write a multi-stage `Dockerfile` for a Go 1.22 service (`go.mod`, `go.sum`, `main.go`, `internal/`). Build stage: a pinned
`golang:1.22` image (any pinned variant), download modules in a cacheable layer BEFORE copying the rest of the source, build a
static binary (`CGO_ENABLED=0`) to /out/app. Final stage: `gcr.io/distroless/static-debian12:nonroot` (pinned tag), copy only the
binary, run as the nonroot user (UID 65532), expose 8080, `ENTRYPOINT ["/app"]`.""",
 {"Dockerfile": d(r"""
FROM golang:1.22.5-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /out/app .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
""")},
 [BASE, C("df_multistage", "two stages, final copies from builder", min_stages=2),
  C("df_from_regex", "final image is distroless static", regex=r"distroless/static", stage="final"),
  C("df_copy_dot_last", "go.mod/go.sum copied -> go mod download -> source copied", manifests=["go.mod"], install_regex=r"go mod download"),
  C("df_instr", "static build CGO_ENABLED=0", instr="RUN", regex=r"CGO_ENABLED=0\s+.*go build", scope="any"),
  C("df_instr", "binary lands at /out/app", instr="RUN", regex=r"-o /out/app", scope="any"),
  NONROOT, C("df_instr", "EXPOSE 8080", instr="EXPOSE", regex=r"\b8080\b"),
  C("df_instr", "ENTRYPOINT /app exec form", instr="ENTRYPOINT", regex=r'^\[\s*"/app"\s*\]$')]))

add(T("df-java-jre", "write", "dockerfile", "medium", """
Write a multi-stage `Dockerfile` for a Spring Boot service built with Maven (`pom.xml`, `src/`). Stage 1: `maven:3.9-eclipse-temurin-21`
(pinned variant) - resolve dependencies offline first (`mvn -B dependency:go-offline`) in a cacheable layer, then package with
`-DskipTests` producing target/app.jar. Stage 2: a JRE-only image `eclipse-temurin:21-jre-alpine` (pinned), create a non-root user
`app`, copy only the jar, expose 8080, and run `java -jar /opt/app/app.jar` via exec-form ENTRYPOINT.""",
 {"Dockerfile": d(r"""
FROM maven:3.9.8-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml .
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q package -DskipTests && cp target/*.jar target/app.jar

FROM eclipse-temurin:21.0.3_9-jre-alpine
RUN addgroup -S app && adduser -S -G app app
WORKDIR /opt/app
COPY --from=build /build/target/app.jar /opt/app/app.jar
USER app
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/opt/app/app.jar"]
""")},
 [BASE, C("df_multistage", "two stages"), C("df_from_regex", "final stage is a JRE image", regex=r"jre", stage="final"),
  C("df_instr_order", "pom.xml copied, then dependency resolution, then src copied", scope="any",
    steps=[["COPY", r"pom\.xml"], ["RUN", r"dependency:go-offline"], ["COPY", r"\bsrc\b"], ["RUN", r"package"]]),
  C("df_instr", "tests skipped in image build", instr="RUN", regex=r"-DskipTests", scope="any"),
  C("df_instr", "final stage creates user", instr="RUN", regex=r"adduser|useradd"), NONROOT, EXEC,
  C("df_instr", "ENTRYPOINT runs java -jar", instr="ENTRYPOINT", regex=r"java.*-jar"), C("df_instr", "EXPOSE 8080", instr="EXPOSE", regex=r"\b8080\b")]))

add(T("df-rust-dummy-build", "write", "dockerfile", "hard", """
Write a `Dockerfile` for a Rust binary crate (`Cargo.toml`, `Cargo.lock`, `src/main.rs`) that maximises build-cache reuse: dependencies
must be compiled in a layer that only invalidates when Cargo.toml/Cargo.lock change. Use the dummy-main trick (copy the manifests, create a
stub `src/main.rs` containing `fn main() {}`, run `cargo build --release --locked`, then copy the real sources and build again).
Multi-stage: builder `rust:1.79-slim-bookworm` (pinned), runtime `debian:bookworm-slim` (pinned) containing only the binary
`/usr/local/bin/app`, running as a non-root user, exec-form ENTRYPOINT.""",
 {"Dockerfile": d(r"""
FROM rust:1.79-slim-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs && cargo build --release --locked
COPY src ./src
RUN touch src/main.rs && cargo build --release --locked

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 app
COPY --from=builder /app/target/release/app /usr/local/bin/app
USER app
ENTRYPOINT ["/usr/local/bin/app"]
""")},
 [BASE, C("df_multistage", "multi-stage"), C("df_instr_order", "manifests -> stub build -> real src -> final build", scope="any",
    steps=[["COPY", r"Cargo\.toml"], ["RUN", r"fn main\(\) \{\}.*cargo build --release --locked"], ["COPY", r"\bsrc\b"], ["RUN", r"cargo build --release --locked"]]),
  C("df_instr", "uses --locked", instr="RUN", regex=r"cargo build.*--locked", scope="any", min=2),
  C("df_from_regex", "runtime is debian bookworm-slim", regex=r"debian:.*bookworm.*slim", stage="final"),
  C("df_instr", "binary copied from builder to /usr/local/bin/app", instr="COPY", regex=r"--from=builder .*/usr/local/bin/app"), NONROOT, EXEC]))

add(T("df-nginx-static", "write", "dockerfile", "easy", """
Write a `Dockerfile` that serves a pre-built static site from `./dist` using the unprivileged nginx image
(`nginxinc/nginx-unprivileged`, pinned tag, alpine variant). Copy dist to /usr/share/nginx/html, copy `nginx.conf` to
/etc/nginx/conf.d/default.conf, listen on 8080 (EXPOSE it), keep the non-root user, and add a HEALTHCHECK using wget (available in alpine/busybox).""",
 {"Dockerfile": d(r"""
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
""")},
 [BASE, C("df_from_regex", "unprivileged nginx", regex=r"nginx-unprivileged.*alpine"), NONROOT, HC,
  C("df_instr", "dist copied to html root", instr="COPY", regex=r"dist/?\s+/usr/share/nginx/html"),
  C("df_instr", "nginx.conf installed as default.conf", instr="COPY", regex=r"nginx\.conf\s+/etc/nginx/conf\.d/default\.conf"),
  C("df_instr", "EXPOSE 8080", instr="EXPOSE", regex=r"\b8080\b"), NOURLADD]))

add(T("df-build-args", "write", "dockerfile", "medium", """
Write a `Dockerfile` for a Python 3.12 service where the Python version and app version are build arguments.
Define `ARG PYTHON_VERSION=3.12.4` BEFORE the first FROM and use it in the base tag (`python:${PYTHON_VERSION}-slim`). Declare `ARG APP_VERSION=0.0.0-dev`
in the stage that uses it and expose it both as a LABEL `org.opencontainers.image.version` and as ENV `APP_VERSION`.
Install `requirements.txt` with pip (no cache), copy the source, run as a non-root user, CMD `python -m app` in exec form.""",
 {"Dockerfile": d(r"""
ARG PYTHON_VERSION=3.12.4
FROM python:${PYTHON_VERSION}-slim
ARG APP_VERSION=0.0.0-dev
LABEL org.opencontainers.image.version="${APP_VERSION}"
ENV APP_VERSION=${APP_VERSION}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r -u 10001 app
USER app
CMD ["python", "-m", "app"]
""")},
 [BASE, C("contains", "global ARG PYTHON_VERSION before FROM", file="Dockerfile", regex=r"\A\s*(#.*\n\s*)*ARG PYTHON_VERSION=3\.12\.\d+\s*\nFROM python:\$\{PYTHON_VERSION\}-slim", flags="s"),
  C("df_instr", "ARG APP_VERSION re-declared in the stage", instr="ARG", regex=r"^APP_VERSION="),
  C("df_instr", "LABEL image.version uses APP_VERSION", instr="LABEL", regex=r"org\.opencontainers\.image\.version=.*APP_VERSION"),
  C("df_instr", "ENV APP_VERSION", instr="ENV", regex=r"APP_VERSION=.*APP_VERSION"),
  C("df_instr", "pip --no-cache-dir", instr="RUN", regex=r"pip install .*--no-cache-dir"), NONROOT, EXEC,
  C("df_instr", "CMD python -m app", instr="CMD", regex=r"python.*-m.*app")]))

add(T("df-py-venv-multistage", "write", "dockerfile", "hard", """
Write a two-stage `Dockerfile` for a Python 3.12 service with native dependencies. Builder stage (`python:3.12-slim`, pinned): install
`build-essential` correctly (single RUN, apt hygiene: update+install+list cleanup, --no-install-recommends), create a virtualenv at /opt/venv,
and pip-install `requirements.txt` into it. Final stage (`python:3.12-slim`, pinned): copy ONLY /opt/venv from the builder (no compilers in the final image),
put /opt/venv/bin first on PATH, create user with numeric UID 10001, copy the app, run as that UID, CMD `python main.py` in exec form.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim AS builder
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12.4-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY . .
USER 10001
CMD ["python", "main.py"]
""")},
 [BASE, C("df_multistage", "multi-stage"), C("df_apt_hygiene", "apt hygiene (update+install+cleanup, no recommends)"),
  C("df_instr", "build-essential only in builder (not in final stage)", instr="RUN", regex=r"build-essential", scope="final", expect="absent"),
  C("df_instr", "final copies /opt/venv from builder", instr="COPY", regex=r"--from=builder\s+/opt/venv\s+/opt/venv"),
  C("df_instr", "final stage PATH starts with /opt/venv/bin", instr="ENV", regex=r"PATH=\"?/opt/venv/bin:"),
  NONROOT, C("df_instr", "USER is numeric 10001", instr="USER", regex=r"^10001(:\d+)?$"), EXEC]))

add(T("df-entrypoint-script", "write", "dockerfile", "medium", """
Write a `Dockerfile` for a small service image based on `python:3.12-slim` (pinned) that has a wrapper `docker-entrypoint.sh` in the build context.
Install the script at /usr/local/bin/docker-entrypoint.sh with the executable bit set WITHOUT a separate chmod layer (use `COPY --chmod=755`),
use it as an exec-form ENTRYPOINT, keep `["serve", "--port", "8080"]` as the default exec-form CMD (overridable arguments), run as non-root user `svc`,
and expose 8080.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim
RUN useradd --system --uid 10001 svc
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
WORKDIR /srv
COPY . .
USER svc
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["serve", "--port", "8080"]
""")},
 [BASE, C("df_instr", "entrypoint script installed with COPY --chmod=755", instr="COPY", regex=r"--chmod=0?755\s+docker-entrypoint\.sh\s+/usr/local/bin/docker-entrypoint\.sh"),
  C("df_instr", "no extra chmod layer", instr="RUN", regex=r"chmod", scope="any", expect="absent"),
  C("df_instr", "ENTRYPOINT exec form pointing at the script", instr="ENTRYPOINT", regex=r'^\["/usr/local/bin/docker-entrypoint\.sh"\]$'),
  C("df_instr", "default CMD args", instr="CMD", regex=r'^\["serve",\s*"--port",\s*"8080"\]$'), NONROOT, C("df_instr", "EXPOSE 8080", instr="EXPOSE", regex=r"\b8080\b")]))

add(T("df-dockerignore-node", "write", "dockerfile", "easy", """
The project is a Node.js app built with `COPY . .` (see Dockerfile). Write the `.dockerignore` for it so the build context stays small and
secrets never enter the image. The repo contains: node_modules/, .git/, .env and .env.local files, coverage/, dist/ (built inside the image, not copied),
npm-debug.log, *.md docs, Dockerfile and docker-compose.yml, .github/, and `src/`, `package.json`, `package-lock.json`, `server.js` which MUST remain in the context.""",
 {".dockerignore": d(r"""
node_modules
.git
.github
.env
.env.*
coverage
dist
npm-debug.log
*.md
Dockerfile
docker-compose.yml
""")},
 [C("lineset", "must exclude node_modules, .git, .env, coverage, dist, npm-debug.log", file=".dockerignore",
    has=[["node_modules", "**/node_modules"], [".git", "**/.git"], [".env"], ["coverage"], ["dist"], ["npm-debug.log", "npm-debug.log*"]]),
  C("lineset", "env variants must be excluded too (.env.local)", file=".dockerignore", has=[[".env.*", ".env*", ".env.local", "*.env", "**/.env*"]]),
  C("lineset", "must not ignore needed files", file=".dockerignore", has=[], absent=["src", "package.json", "package-lock.json", "server.js", "*.json", "*.js", "src/"]),
  C("not_contains", "no negation hacks that re-include secrets", file=".dockerignore", regex=r"^!\.env")],
 start={"Dockerfile": d(r"""
FROM node:20-alpine3.19
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build
USER node
CMD ["node", "dist/server.js"]
""")}))

add(T("df-convert-shell-to-dockerfile", "convert", "dockerfile", "medium", """
Convert the provisioning script `provision.sh` (how the service is installed on a VM today) into a production-quality `Dockerfile`.
Keep the same runtime result: Debian packages installed (with proper apt hygiene), the app under /opt/reports, the `reports` user (no root at runtime),
env `REPORT_DIR=/var/reports` writable by that user, and the final process started by CMD in exec form. Pin the base image.""",
 {"Dockerfile": d(r"""
FROM debian:bookworm-20240612-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN useradd --system --create-home --uid 10001 reports \
 && mkdir -p /var/reports \
 && chown reports:reports /var/reports
ENV REPORT_DIR=/var/reports
COPY --chown=reports:reports app/ /opt/reports/
WORKDIR /opt/reports
USER reports
CMD ["python3", "/opt/reports/run.py"]
""")},
 [BASE, C("df_apt_hygiene", "apt hygiene"), C("df_instr", "packages python3 python3-pip ca-certificates", instr="RUN", regex=r"python3.*python3-pip.*ca-certificates|ca-certificates.*python3"),
  C("df_instr", "REPORT_DIR env", instr="ENV", regex=r"REPORT_DIR=/var/reports"), C("df_instr", "reports dir owned by reports", instr="RUN", regex=r"chown.*reports.*/var/reports|chown.*/var/reports", scope="any"),
  C("df_instr", "app copied to /opt/reports", instr="COPY", regex=r"/opt/reports"), NONROOT, C("df_instr", "USER reports", instr="USER", regex=r"^reports"), EXEC,
  C("df_instr", "CMD runs run.py", instr="CMD", regex=r"run\.py")],
 start={"provision.sh": d(r"""
#!/bin/bash
set -e
apt-get update
apt-get install -y python3 python3-pip ca-certificates
useradd -r -m reports
mkdir -p /opt/reports /var/reports
cp -r app/* /opt/reports/
chown -R reports:reports /var/reports
export REPORT_DIR=/var/reports
su reports -c "python3 /opt/reports/run.py"
""")}))

# ------------------------------------------------------------------ fix
add(T("df-fix-latest-root-add", "fix", "dockerfile", "easy", """
This Dockerfile builds but the security review flagged it. Fix it: the image must be reproducible, must not run as root, and must not fetch
remote content at build time via ADD. The app still needs the same tarball content under /app (download it in a RUN step with curl, verify the SHA-256
`3f5b0c1d2e4a6f8091b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718` with `sha256sum -c`, and extract it - curl and ca-certificates are installed already), keep port 5000 and the CMD.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN curl -fsSL -o /tmp/app.tgz https://releases.example.com/app-1.4.2.tar.gz \
 && echo "3f5b0c1d2e4a6f8091b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718  /tmp/app.tgz" | sha256sum -c - \
 && tar -xzf /tmp/app.tgz -C /app \
 && rm /tmp/app.tgz
RUN useradd --system --uid 10001 app && chown -R app /app
USER app
EXPOSE 5000
CMD ["python", "-m", "app"]
""")},
 [C("df_base_pinned", "base image tag is :latest", bug=True), C("df_user_nonroot", "no USER instruction (runs as root)", bug=True),
  C("df_no_add_url", "ADD with remote URL", bug=True), C("df_instr", "checksum verified", instr="RUN", regex=r"sha256sum -c", scope="any"),
  C("df_instr", "EXPOSE 5000 kept", instr="EXPOSE", regex=r"5000"), C("df_instr", "CMD kept", instr="CMD", regex=r"python.*-m.*app")],
 start={"Dockerfile": d(r"""
FROM python:latest
WORKDIR /app
ADD https://releases.example.com/app-1.4.2.tar.gz /app/
RUN tar -xzf /app/app-1.4.2.tar.gz -C /app && rm /app/app-1.4.2.tar.gz
EXPOSE 5000
CMD ["python", "-m", "app"]
""")}))

add(T("df-fix-cache-order", "fix", "dockerfile", "medium", """
Every code change makes CI reinstall all npm dependencies (10 minutes). Fix this Dockerfile's layer ordering so that editing files under `src/` does NOT
re-run the dependency install, without changing the final image contents, base image, port or command.""",
 {"Dockerfile": d(r"""
FROM node:20.14-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY . .
RUN npm run build
USER node
EXPOSE 8080
CMD ["node", "dist/index.js"]
""")},
 [C("df_copy_dot_last", "COPY . . happens before npm ci -> cache busted on every change", bug=True, manifests=["package.json"], install_regex=r"npm (ci|install)"),
  BASE, NONROOT, C("df_instr", "EXPOSE 8080 kept", instr="EXPOSE", regex=r"8080"), C("df_instr", "build step kept", instr="RUN", regex=r"npm run build"),
  C("df_instr", "CMD kept", instr="CMD", regex=r"dist/index\.js"), C("df_instr_order", "build runs after source copy", steps=[["RUN", "npm (ci|install)"], ["COPY", r"\."], ["RUN", "npm run build"]])],
 start={"Dockerfile": d(r"""
FROM node:20.14-alpine
WORKDIR /app
COPY . .
RUN npm ci --omit=dev
RUN npm run build
USER node
EXPOSE 8080
CMD ["node", "dist/index.js"]
""")}))

add(T("df-fix-apt-layers", "fix", "dockerfile", "medium", """
Fix the apt usage in this Dockerfile: it produces a stale package index in a cached layer, installs recommended packages nobody needs,
leaves the apt lists in the image and prompts interactively. Keep exactly the same packages (git, openssh-client, ca-certificates), base image and the rest.""",
 {"Dockerfile": d(r"""
FROM ubuntu:22.04
RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
COPY ci-scripts/ /work/
USER nobody
ENTRYPOINT ["/work/run.sh"]
""")},
 [C("df_apt_hygiene", "apt update alone in a layer / install without --no-install-recommends / no cleanup / no -y", bug=True),
  C("df_instr", "git, openssh-client, ca-certificates all still installed", instr="RUN", regex=r"git.*openssh-client.*ca-certificates|ca-certificates.*git.*openssh-client|openssh-client.*git.*ca-certificates|git.*ca-certificates.*openssh-client|openssh-client.*ca-certificates.*git|ca-certificates.*openssh-client.*git"),
  BASE, NONROOT, EXEC],
 start={"Dockerfile": d(r"""
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install git openssh-client ca-certificates
WORKDIR /work
COPY ci-scripts/ /work/
USER nobody
ENTRYPOINT ["/work/run.sh"]
""")}))

add(T("df-fix-shell-form-signals", "fix", "dockerfile", "easy", """
`docker stop` on this container always waits 10 seconds and then SIGKILLs the process, because the app never gets SIGTERM.
Fix the Dockerfile (no new packages, no init system) so the Python process runs as PID 1 and receives signals. Keep the same entrypoint behaviour and arguments.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim
WORKDIR /app
COPY . .
RUN useradd -r -u 10001 app
USER app
ENTRYPOINT ["python", "worker.py"]
CMD ["--queue", "default", "--concurrency", "4"]
""")},
 [C("df_exec_form", "ENTRYPOINT/CMD in shell form (sh -c wraps the process)", bug=True),
  C("df_instr", "entrypoint still runs worker.py", instr="ENTRYPOINT", regex=r"worker\.py"),
  C("df_instr", "queue args preserved", instr="CMD", regex=r"--queue.*default.*--concurrency.*4|--queue default --concurrency 4"), BASE, NONROOT],
 start={"Dockerfile": d(r"""
FROM python:3.12.4-slim
WORKDIR /app
COPY . .
RUN useradd -r -u 10001 app
USER app
ENTRYPOINT python worker.py
CMD --queue default --concurrency 4
""")}))

add(T("df-fix-build-secrets", "fix", "dockerfile", "hard", """
This Dockerfile bakes credentials into image layers (visible via `docker history`). Fix it: no secret values may appear in ENV/ARG defaults or be written
into a layer. The private npm registry token must reach `npm ci` only through a BuildKit secret mount (`--mount=type=secret,id=npmrc,target=/root/.npmrc`),
and the runtime DB password must be supplied at runtime (just remove it from the image). Keep the base image, WORKDIR, port and CMD.""",
 {"Dockerfile": d(r"""
# syntax=docker/dockerfile:1.7
FROM node:20.14-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci --omit=dev
COPY . .
USER node
EXPOSE 3000
CMD ["node", "index.js"]
""")},
 [C("df_no_secrets", "secret-looking ENV/ARG literals (NPM_TOKEN, DB_PASSWORD)", bug=True),
  C("df_instr", "npm ci uses a BuildKit secret mount", instr="RUN", regex=r"--mount=type=secret,id=npmrc.*npm ci", bug=True),
  C("not_contains", "no .npmrc written with echo/printf into a layer", bug=True, file="Dockerfile", regex=r"(echo|printf).*(_authToken|npmrc)", flags="m"),
  BASE, C("df_instr", "EXPOSE 3000 kept", instr="EXPOSE", regex=r"3000"), C("df_instr", "CMD kept", instr="CMD", regex=r"index\.js")],
 start={"Dockerfile": d(r"""
FROM node:20.14-alpine
WORKDIR /app
ARG NPM_TOKEN=npm_9f8e7d6c5b4a
ENV DB_PASSWORD=hunter2
COPY package.json package-lock.json ./
RUN echo "//registry.example.com/:_authToken=${NPM_TOKEN}" > /root/.npmrc && npm ci --omit=dev && rm /root/.npmrc
COPY . .
USER node
EXPOSE 3000
CMD ["node", "index.js"]
""")}))

add(T("df-fix-curl-pipe-sh", "fix", "dockerfile", "medium", """
The Dockerfile installs `hadolint`-style tooling by piping a remote script into a shell. Replace that with a pinned, verified install: download
`https://example.com/dl/tool-2.8.1-linux-amd64.tar.gz` with curl, verify it with `sha256sum -c` against
`9a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9`, extract the `tool` binary to /usr/local/bin, and remove the archive in the same layer. Everything else stays.""",
 {"Dockerfile": d(r"""
FROM debian:bookworm-20240612-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSLO https://example.com/dl/tool-2.8.1-linux-amd64.tar.gz \
 && echo "9a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9  tool-2.8.1-linux-amd64.tar.gz" | sha256sum -c - \
 && tar -xzf tool-2.8.1-linux-amd64.tar.gz -C /usr/local/bin tool \
 && rm tool-2.8.1-linux-amd64.tar.gz
USER nobody
ENTRYPOINT ["tool"]
""")},
 [C("df_no_curl_pipe", "curl | sh installer", bug=True), C("df_instr", "checksum verified", instr="RUN", regex=r"sha256sum -c", bug=True, scope="any"),
  C("df_instr", "pinned version 2.8.1 downloaded", instr="RUN", regex=r"tool-2\.8\.1-linux-amd64\.tar\.gz"), C("df_instr", "archive removed in same layer", instr="RUN", regex=r"tar .*&&.*rm |rm .*tool-2\.8\.1"),
  BASE, NONROOT, C("df_apt_hygiene", "apt hygiene retained")],
 start={"Dockerfile": d(r"""
FROM debian:bookworm-20240612-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://example.com/install.sh | sh
USER nobody
ENTRYPOINT ["tool"]
""")}))

add(T("df-fix-single-to-multistage", "fix", "dockerfile", "hard", """
This image for a Go service is 1.2 GB because the entire toolchain ships to production. Fix the Dockerfile: build in one stage and ship in a second,
minimal stage (alpine or distroless, pinned) that contains only the compiled static binary. Preserve: Go 1.22 build with CGO disabled producing
`/out/server`, the cacheable `go mod download` layer before the source copy, port 9090, and a non-root runtime user.""",
 {"Dockerfile": d(r"""
FROM golang:1.22.5-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/server ./cmd/server

FROM alpine:3.20
RUN adduser -D -u 10001 app
COPY --from=build /out/server /usr/local/bin/server
USER app
EXPOSE 9090
ENTRYPOINT ["/usr/local/bin/server"]
""")},
 [C("df_multistage", "single stage: build toolchain ships to production", bug=True),
  C("df_from_regex", "final stage must not be the golang image", regex=r"^(?!golang)", stage="final", bug=True),
  C("df_copy_dot_last", "download layer is cacheable", manifests=["go.mod"], install_regex=r"go mod download"),
  C("df_instr", "CGO disabled", instr="RUN", regex=r"CGO_ENABLED=0", scope="any"), C("df_instr", "output /out/server", instr="RUN", regex=r"/out/server", scope="any"),
  BASE, NONROOT, C("df_instr", "EXPOSE 9090 kept", instr="EXPOSE", regex=r"9090")],
 start={"Dockerfile": d(r"""
FROM golang:1.22.5
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/server ./cmd/server
EXPOSE 9090
ENTRYPOINT ["/out/server"]
""")}))

add(T("df-fix-nonroot-permission", "fix", "dockerfile", "hard", """
After the security team added `USER app`, the container crashes at startup with `PermissionError: /app/data/state.db` (the app writes its SQLite file to /app/data).
Fix the Dockerfile so it still runs as the unprivileged `app` user (UID 10001) but /app/data exists and is writable by it, and the application files are owned by
`app` using `COPY --chown` (not a recursive chown RUN that duplicates the layer). USER must stay before CMD. Do not use chmod 777.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
RUN mkdir -p /app/data && chown app:app /app/data
USER app
VOLUME ["/app/data"]
EXPOSE 8000
CMD ["python", "-m", "svc"]
""")},
 [C("df_instr", "no directory /app/data created and chowned to app", instr="RUN", regex=r"mkdir.*/app/data.*chown.*app|chown.*app.*/app/data", bug=True),
  C("df_instr", "source copied with --chown", instr="COPY", regex=r"--chown=(app|10001)(:\S+)?\s+\.\s", bug=True),
  C("not_contains", "no chmod 777 / recursive chown layer", file="Dockerfile", regex=r"chmod\s+-?R?\s*777|chown\s+-R"),
  NONROOT, C("df_user_before_cmd", "USER before CMD"), C("df_instr", "USER is app/10001", instr="USER", regex=r"^(app|10001)"), BASE,
  C("df_instr", "CMD kept", instr="CMD", regex=r"svc")],
 start={"Dockerfile": d(r"""
FROM python:3.12.4-slim
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER app
EXPOSE 8000
CMD ["python", "-m", "svc"]
""")}))

add(T("df-fix-no-healthcheck", "fix", "dockerfile", "easy", """
Orchestrators keep routing traffic to this container while the app is wedged. Add a container HEALTHCHECK that probes `http://127.0.0.1:8080/healthz`
every 15s with a 2s timeout and 3 retries. The image is Alpine-based and has busybox `wget` but no curl. Change nothing else.""",
 {"Dockerfile": d(r"""
FROM alpine:3.20
RUN apk add --no-cache ca-certificates && adduser -D -u 10001 svc
COPY svc /usr/local/bin/svc
USER svc
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=2s --retries=3 CMD wget -q --spider http://127.0.0.1:8080/healthz || exit 1
ENTRYPOINT ["/usr/local/bin/svc"]
""")},
 [C("df_healthcheck", "missing HEALTHCHECK", bug=True), C("df_instr", "probes /healthz on 8080", instr="HEALTHCHECK", regex=r"127\.0\.0\.1:8080/healthz|localhost:8080/healthz"),
  C("df_instr", "interval/timeout/retries set", instr="HEALTHCHECK", regex=r"--interval=15s.*--timeout=2s.*--retries=3|--timeout=2s.*--interval=15s.*--retries=3|--interval=15s.*--retries=3.*--timeout=2s"),
  C("df_instr", "uses wget not curl", instr="HEALTHCHECK", regex=r"curl", expect="absent"), BASE, NONROOT, EXEC],
 start={"Dockerfile": d(r"""
FROM alpine:3.20
RUN apk add --no-cache ca-certificates && adduser -D -u 10001 svc
COPY svc /usr/local/bin/svc
USER svc
EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/svc"]
""")}))

add(T("df-fix-arg-scope", "fix", "dockerfile", "hard", """
The image label always reports an empty version: `docker inspect` shows `org.opencontainers.image.version=""` even when building with
`--build-arg APP_VERSION=1.9.0`, and the build also warns about the base image variable. Fix the Dockerfile (hint: ARG scoping across FROM).
The Python version must remain a build argument defaulting to 3.12.4.""",
 {"Dockerfile": d(r"""
ARG PYTHON_VERSION=3.12.4
ARG APP_VERSION=dev
FROM python:${PYTHON_VERSION}-slim
ARG APP_VERSION
LABEL org.opencontainers.image.version="${APP_VERSION}"
WORKDIR /app
COPY . .
RUN useradd -r -u 10001 app
USER app
CMD ["python", "main.py"]
""")},
 [C("df_instr", "APP_VERSION is not re-declared after FROM, so it is empty in the stage", instr="ARG", regex=r"^APP_VERSION(=|$)", bug=True),
  C("df_base_pinned", "base resolves to a pinned tag", bug=False),
  C("df_instr", "LABEL still uses APP_VERSION", instr="LABEL", regex=r"APP_VERSION"), NONROOT, EXEC],
 start={"Dockerfile": d(r"""
ARG PYTHON_VERSION=3.12.4
ARG APP_VERSION=dev
FROM python:${PYTHON_VERSION}-slim
LABEL org.opencontainers.image.version="${APP_VERSION}"
WORKDIR /app
COPY . .
RUN useradd -r -u 10001 app
USER app
CMD ["python", "main.py"]
""")}))

# ------------------------------------------------------------------ harden
add(T("df-harden-python-svc", "harden", "dockerfile", "medium", """
Harden this Dockerfile for production without changing what the service does (Flask on port 8000 started by gunicorn, same requirements and sources).
Apply container best practices: reproducible base, no root at runtime, no pip cache, no sudo, a health probe that works with the tools available in the image,
exec-form start command.""",
 {"Dockerfile": d(r"""
FROM python:3.12.4-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --system --uid 10001 app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
""")},
 [C("df_base_pinned", "FROM python:latest", bug=True), C("df_user_nonroot", "runs as root", bug=True), C("df_exec_form", "shell-form CMD", bug=True),
  C("df_healthcheck", "no healthcheck", bug=True), C("df_instr", "pip cache left behind", instr="RUN", regex=r"pip install(?!.*--no-cache-dir)", expect="absent", scope="any", bug=True),
  C("df_instr", "no sudo anywhere", instr="RUN", regex=r"\bsudo\b", expect="absent", scope="any", bug=True),
  C("df_instr", "still gunicorn on 8000", instr="CMD", regex=r"gunicorn.*8000|8000.*gunicorn"), C("df_instr", "EXPOSE 8000 kept", instr="EXPOSE", regex=r"8000"),
  C("df_instr", "requirements still installed", instr="RUN", regex=r"-r requirements\.txt", scope="any")],
 start={"Dockerfile": d(r"""
FROM python:latest
WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y sudo
RUN sudo pip install -r requirements.txt
EXPOSE 8000
CMD gunicorn -b 0.0.0.0:8000 app:app
""")}))

add(T("df-harden-node-prod", "harden", "dockerfile", "hard", """
Harden and slim this Node.js Dockerfile for production. Requirements: pinned Alpine base (no :latest, no full Debian image), a multi-stage build where devDependencies
and the TypeScript compiler never reach the final image (build in stage 1 with `npm ci`, ship only `dist/` plus production node_modules installed with `npm ci --omit=dev`),
`NODE_ENV=production` in the final stage, unprivileged `node` user, a HEALTHCHECK (node is available; no curl), no ADD, exec-form command `node dist/main.js`.""",
 {"Dockerfile": d(r"""
FROM node:20.14-alpine3.20 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

FROM node:20.14-alpine3.20
ENV NODE_ENV=production
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD node -e "require('http').get('http://127.0.0.1:3000/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"
CMD ["node", "dist/main.js"]
""")},
 [C("df_base_pinned", "FROM node:latest", bug=True), C("df_from_regex", "final base must be alpine", regex=r"alpine", stage="final", bug=True),
  C("df_multistage", "single stage ships devDependencies", bug=True), C("df_user_nonroot", "runs as root", bug=True), C("df_healthcheck", "no healthcheck", bug=True),
  C("df_no_add", "ADD used", bug=True),
  C("df_instr", "NODE_ENV=production in final stage", instr="ENV", regex=r"NODE_ENV=production"),
  C("df_instr", "production-only install in final stage", instr="RUN", regex=r"npm ci .*--omit=dev|npm ci --omit=dev|npm ci --only=production"),
  C("df_instr", "final stage must not run the compiler", instr="RUN", regex=r"npm run build|tsc", expect="absent"),
  C("df_instr", "HEALTHCHECK does not need curl", instr="HEALTHCHECK", regex=r"curl", expect="absent"),
  C("df_instr", "CMD node dist/main.js", instr="CMD", regex=r"node.*dist/main\.js"), EXEC],
 start={"Dockerfile": d(r"""
FROM node:latest
WORKDIR /app
ADD . /app
RUN npm install
RUN npm run build
EXPOSE 3000
CMD npm start
""")}))

add(T("df-harden-user-root-end", "harden", "dockerfile", "medium", """
A previous engineer 'fixed' a permissions problem by switching back to root at the end of this Dockerfile. Fix the root cause so the container runs as the
`appuser` account (UID 10001) while still being able to do its job: the package installation needs root, so it must happen BEFORE dropping privileges; the
final effective user must be appuser, set before the CMD. Keep base image, packages and CMD.""",
 {"Dockerfile": d(r"""
FROM debian:bookworm-20240612-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 appuser
WORKDIR /home/appuser
COPY --chown=appuser:appuser poller.sh .
USER appuser
CMD ["./poller.sh"]
""")},
 [C("df_user_nonroot", "final USER is root", bug=True), C("df_instr", "USER appuser/10001 is the last USER", instr="USER", regex=r"^(appuser|10001)"),
  C("df_user_before_cmd", "USER before CMD"), C("df_apt_hygiene", "apt hygiene"), BASE, C("df_instr", "netcat still installed", instr="RUN", regex=r"netcat"),
  C("df_instr", "CMD kept", instr="CMD", regex=r"poller\.sh")],
 start={"Dockerfile": d(r"""
FROM debian:bookworm-20240612-slim
RUN useradd --system --uid 10001 appuser
USER appuser
WORKDIR /home/appuser
RUN apt-get update \
 && apt-get install -y --no-install-recommends netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*
COPY poller.sh .
USER root
CMD ["./poller.sh"]
""")}))

add(T("df-convert-ubuntu-to-alpine", "convert", "dockerfile", "hard", """
Convert this Ubuntu-based Dockerfile to an Alpine-based one (`alpine:3.20`, pinned) with the same behaviour: same tools installed (bash, curl, jq, tzdata),
apk with no index cache left behind (use `apk add --no-cache`), the `ops` user created the Alpine way (`adduser -D`, UID 10001), `TZ=UTC`, work dir /ops,
`COPY` the scripts, run as ops, `ENTRYPOINT ["/bin/bash", "/ops/run.sh"]` in exec form. No apt-get anywhere.""",
 {"Dockerfile": d(r"""
FROM alpine:3.20
RUN apk add --no-cache bash curl jq tzdata \
 && adduser -D -u 10001 ops
ENV TZ=UTC
WORKDIR /ops
COPY scripts/ /ops/
USER ops
ENTRYPOINT ["/bin/bash", "/ops/run.sh"]
""")},
 [C("df_from_regex", "alpine base", regex=r"^alpine:3\.\d+(\.\d+)?$"), BASE, C("df_instr", "apk add --no-cache with all four tools", instr="RUN", regex=r"apk add --no-cache.*bash.*|apk add .*--no-cache.*bash"),
  C("df_instr", "all four packages", instr="RUN", regex=r"(?=.*\bbash\b)(?=.*\bcurl\b)(?=.*\bjq\b)(?=.*\btzdata\b)"), C("df_instr", "no apt-get", instr="RUN", regex=r"apt(-get)?\s", expect="absent", scope="any"),
  C("df_instr", "adduser -D with uid 10001", instr="RUN", regex=r"adduser\s+-D.*10001|adduser.*-u 10001.*-D"), C("df_instr", "TZ=UTC", instr="ENV", regex=r"TZ=UTC"),
  NONROOT, C("df_instr", "ENTRYPOINT exec form for run.sh", instr="ENTRYPOINT", regex=r'^\["/bin/bash",\s*"/ops/run\.sh"\]$')],
 start={"Dockerfile": d(r"""
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive TZ=UTC
RUN apt-get update \
 && apt-get install -y --no-install-recommends bash curl jq tzdata \
 && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --create-home ops
WORKDIR /ops
COPY scripts/ /ops/
USER ops
ENTRYPOINT ["/bin/bash", "/ops/run.sh"]
""")}))
