from _dsl import C, Q, T, d

F = "docker-compose.yml"
VALID = C("valid", "file is valid YAML", file=F)
TASKS = []
add = TASKS.append


def noprivileged():
    return Q("no service is privileged", F, "services.*.privileged", "falsy", allow_empty=True)


def pinned():
    return Q("every image has a pinned, non-latest tag", F, "services.*.image", "regex", r"^[^:\s]+(/[^:\s]+)*:(?!latest$)[\w][\w.\-]*$|@sha256:", mode="all", allow_empty=True)


add(T("cp-web-db-health", "write", "compose", "medium", """
Write `docker-compose.yml` for a web app and its PostgreSQL database. `db`: `postgres:16.3-alpine`, data in a named volume `pgdata` (mounted at /var/lib/postgresql/data),
env POSTGRES_USER=app, POSTGRES_DB=app and POSTGRES_PASSWORD taken from the host environment `DB_PASSWORD` (compose must refuse to start if it is unset), a healthcheck using
`pg_isready -U app -d app`. `web`: `ghcr.io/acme/web:1.8.2`, published only on localhost `127.0.0.1:8080:8080`, starts only after the database is HEALTHY, restart policy `unless-stopped`,
env `DATABASE_URL` pointing at host `db`.""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD must be set}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
  web:
    image: ghcr.io/acme/web:1.8.2
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      DATABASE_URL: postgres://app:${DB_PASSWORD}@db:5432/app
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
volumes:
  pgdata:
""")},
 [VALID, pinned(), Q("db data on named volume", F, "services.db.volumes[*]", "regex", r"^pgdata:/var/lib/postgresql/data$", mode="any"), C("contains", "top-level volumes: pgdata declared", file=F, regex=r"^volumes:\s*\n\s+pgdata:"),
  Q("password required from env", F, "services.db.environment.POSTGRES_PASSWORD", "regex", r"^\$\{DB_PASSWORD:\?.*\}$"),
  Q("db healthcheck uses pg_isready", F, "services.db.healthcheck.test", "regex", r"pg_isready.*-U app"), Q("db healthcheck has interval+retries", F, "services.db.healthcheck", "exists"),
  Q("web waits for healthy db", F, "services.web.depends_on.db.condition", "eq", "service_healthy"),
  Q("web only on localhost", F, "services.web.ports[*]", "regex", r"^127\.0\.0\.1:8080:8080$"), Q("restart unless-stopped", F, "services.web.restart", "eq", "unless-stopped"),
  Q("DATABASE_URL points at db host", F, "services.web.environment.DATABASE_URL", "regex", r"@db:5432/")]))

add(T("cp-redis-worker", "write", "compose", "easy", """
Write `docker-compose.yml` with a `redis` service (`redis:7.2-alpine`, healthcheck `redis-cli ping`, no published ports) and a `worker` service
(`ghcr.io/acme/worker:2.0.1`) that waits for redis to be healthy, has `restart: unless-stopped`, and gets `REDIS_URL=redis://redis:6379/0`.""",
 {F: d(r"""
services:
  redis:
    image: redis:7.2-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 2s
      retries: 5
  worker:
    image: ghcr.io/acme/worker:2.0.1
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
    restart: unless-stopped
""")},
 [VALID, pinned(), Q("redis healthcheck pings", F, "services.redis.healthcheck.test", "regex", r"redis-cli.*ping"), Q("redis not published", F, "services.redis.ports", "missing"),
  Q("worker waits for healthy redis", F, "services.worker.depends_on.redis.condition", "eq", "service_healthy"),
  Q("restart policy", F, "services.worker.restart", "eq", "unless-stopped"), Q("REDIS_URL", F, "services.worker.environment.REDIS_URL", "eq", "redis://redis:6379/0")]))

add(T("cp-nginx-proxy", "write", "compose", "medium", """
Write `docker-compose.yml`: `app` (`ghcr.io/acme/api:3.4.0`, listens on 3000, healthcheck `wget -qO- http://127.0.0.1:3000/health`) must NOT be reachable from the host (use `expose`, not `ports`).
`proxy` (`nginx:1.27-alpine`) publishes `8080:80`, mounts `./nginx.conf` to /etc/nginx/nginx.conf READ-ONLY, and starts only once app is healthy.
Put both on a user-defined network `edge` (no default network usage required).""",
 {F: d(r"""
services:
  app:
    image: ghcr.io/acme/api:3.4.0
    expose:
      - "3000"
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:3000/health || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks: [edge]
  proxy:
    image: nginx:1.27-alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      app:
        condition: service_healthy
    networks: [edge]
networks:
  edge:
""")},
 [VALID, pinned(), Q("app has no published ports", F, "services.app.ports", "missing"), Q("app exposes 3000", F, "services.app.expose[*]", "in", ["3000", 3000], mode="any"),
  Q("app healthcheck uses wget on 3000", F, "services.app.healthcheck.test", "regex", r"wget.*3000/health"),
  Q("proxy publishes 8080:80", F, "services.proxy.ports[*]", "regex", r"8080:80$", mode="any"),
  Q("nginx.conf mounted read-only", F, "services.proxy.volumes[*]", "regex", r"^\./nginx\.conf:/etc/nginx/nginx\.conf:ro$", mode="any"),
  Q("proxy waits for healthy app", F, "services.proxy.depends_on.app.condition", "eq", "service_healthy"),
  Q("both on edge", F, "services.*.networks", "contains", "edge"), C("contains", "top-level network edge", file=F, regex=r"^networks:\s*\n\s+edge:")]))

add(T("cp-file-secrets", "write", "compose", "hard", """
Write `docker-compose.yml` for `postgres:16.3-alpine` (`db`) and `ghcr.io/acme/api:5.1.0` (`api`) that never puts the DB password in an environment variable value.
Use compose file-based secrets: top-level `secrets: db_password: file: ./secrets/db_password.txt`. `db` reads it through `POSTGRES_PASSWORD_FILE=/run/secrets/db_password`
and has the secret granted; `api` gets the same secret granted and `DB_PASSWORD_FILE=/run/secrets/db_password`. db has a `pg_isready` healthcheck; api waits for it (service_healthy).""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_USER: app
    secrets:
      - db_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 10
  api:
    image: ghcr.io/acme/api:5.1.0
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    depends_on:
      db:
        condition: service_healthy
secrets:
  db_password:
    file: ./secrets/db_password.txt
""")},
 [VALID, pinned(), Q("top-level secret from file", F, "secrets.db_password.file", "eq", "./secrets/db_password.txt"),
  Q("db uses POSTGRES_PASSWORD_FILE", F, "services.db.environment.POSTGRES_PASSWORD_FILE", "eq", "/run/secrets/db_password"),
  Q("db has no plain POSTGRES_PASSWORD", F, "services.db.environment.POSTGRES_PASSWORD", "missing"),
  Q("db granted the secret", F, "services.db.secrets", "contains", "db_password"),
  Q("api granted the secret", F, "services.api.secrets", "contains", "db_password"), Q("api DB_PASSWORD_FILE", F, "services.api.environment.DB_PASSWORD_FILE", "eq", "/run/secrets/db_password"),
  Q("api has no DB_PASSWORD env", F, "services.api.environment.DB_PASSWORD", "missing"),
  Q("healthcheck pg_isready", F, "services.db.healthcheck.test", "regex", r"pg_isready"), Q("api waits for healthy db", F, "services.api.depends_on.db.condition", "eq", "service_healthy")]))

add(T("cp-locked-down-service", "write", "compose", "medium", """
Write `docker-compose.yml` with one service `api` (`ghcr.io/acme/api:1.2.3`, port `127.0.0.1:9000:9000`) configured as a locked-down container: read-only root filesystem with a
16 MiB `tmpfs` at /tmp, all Linux capabilities dropped, `no-new-privileges`, runs as user `10001:10001`, memory limit 256m and cpu limit 0.5 (use `deploy.resources.limits`), `pids_limit: 100`,
and a healthcheck `wget -q --spider http://127.0.0.1:9000/healthz`.""",
 {F: d(r"""
services:
  api:
    image: ghcr.io/acme/api:1.2.3
    user: "10001:10001"
    read_only: true
    tmpfs:
      - /tmp:size=16m
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    pids_limit: 100
    ports:
      - "127.0.0.1:9000:9000"
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:9000/healthz || exit 1"]
      interval: 15s
      timeout: 3s
      retries: 3
""")},
 [VALID, pinned(), Q("read_only rootfs", F, "services.api.read_only", "eq", True), Q("tmpfs /tmp", F, "services.api.tmpfs[*]", "regex", r"^/tmp", mode="any"),
  Q("cap_drop ALL", F, "services.api.cap_drop", "contains", "ALL"), Q("no-new-privileges", F, "services.api.security_opt[*]", "regex", r"^no-new-privileges(:true)?$", mode="any"),
  Q("user 10001:10001", F, "services.api.user", "eq", "10001:10001"), Q("memory limit 256m", F, "services.api.deploy.resources.limits.memory", "qty_lte", "256Mi"),
  Q("memory limit set", F, "services.api.deploy.resources.limits.memory", "exists"), Q("cpu limit 0.5", F, "services.api.deploy.resources.limits.cpus", "lte", 0.5),
  Q("pids_limit 100", F, "services.api.pids_limit", "lte", 100), Q("localhost-only port", F, "services.api.ports[*]", "regex", r"^127\.0\.0\.1:9000:9000$"),
  Q("healthcheck", F, "services.api.healthcheck.test", "regex", r"wget.*9000/healthz")]))

add(T("cp-migrate-then-app", "write", "compose", "hard", """
Write `docker-compose.yml` implementing a safe startup order: `db` (`postgres:16.3-alpine`, pg_isready healthcheck, POSTGRES_PASSWORD from `${DB_PASSWORD:?required}`) ->
`migrate` (`ghcr.io/acme/api:4.0.0`, command `["migrate", "up"]`, runs once and must not be restarted: `restart: "no"`, waits for a healthy db) ->
`api` (same image, command `["serve"]`, starts only after `migrate` COMPLETED SUCCESSFULLY and db is healthy, `restart: unless-stopped`, port `127.0.0.1:4000:4000`).
Share the connection string through a YAML anchor under `x-api-env` merged into both migrate and api environments.""",
 {F: d(r"""
x-api-env: &api-env
  DATABASE_URL: postgres://postgres:${DB_PASSWORD}@db:5432/postgres

services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10
  migrate:
    image: ghcr.io/acme/api:4.0.0
    command: ["migrate", "up"]
    environment: *api-env
    restart: "no"
    depends_on:
      db:
        condition: service_healthy
  api:
    image: ghcr.io/acme/api:4.0.0
    command: ["serve"]
    environment: *api-env
    ports:
      - "127.0.0.1:4000:4000"
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      migrate:
        condition: service_completed_successfully
""")},
 [VALID, pinned(), Q("db healthy check", F, "services.db.healthcheck.test", "regex", r"pg_isready"), Q("db password required", F, "services.db.environment.POSTGRES_PASSWORD", "regex", r"^\$\{DB_PASSWORD:\?.+\}$"),
  Q("migrate command", F, "services.migrate.command", "eq", ["migrate", "up"]), Q("migrate does not restart", F, "services.migrate.restart", "in", ["no", False]),
  Q("migrate waits for healthy db", F, "services.migrate.depends_on.db.condition", "eq", "service_healthy"),
  Q("api waits for migrate completion", F, "services.api.depends_on.migrate.condition", "eq", "service_completed_successfully"),
  Q("api waits for healthy db", F, "services.api.depends_on.db.condition", "eq", "service_healthy"), Q("api command serve", F, "services.api.command", "eq", ["serve"]),
  Q("api restart", F, "services.api.restart", "eq", "unless-stopped"), Q("api localhost port", F, "services.api.ports[*]", "eq", "127.0.0.1:4000:4000"),
  C("contains", "uses a YAML anchor for shared env", file=F, regex=r"&\w+"), C("contains", "and reuses it with an alias", file=F, regex=r"\*\w+", count_min=2),
  Q("DATABASE_URL present in both", F, "services.migrate.environment.DATABASE_URL | services.api.environment.DATABASE_URL", "regex", r"@db:5432", mode="all")]))

add(T("cp-fix-privileged", "fix", "compose", "easy", """
Security review: this compose file gives the container full host access although the app only needs to bind port 80 inside the container and read nothing from the host.
Fix it with the minimum privileges needed: no privileged mode, no host docker socket, no host network; keep the port mapping, image and healthcheck. If it needs a capability, grant only `NET_BIND_SERVICE`
and drop everything else.""",
 {F: d(r"""
services:
  gateway:
    image: ghcr.io/acme/gateway:0.9.4
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    ports:
      - "8080:80"
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:80/ || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
""")},
 [VALID, Q("privileged: true", F, "services.gateway.privileged", "falsy", bug=True, allow_empty=True), Q("docker.sock mounted", F, "services.gateway.volumes[*]", "not_regex", r"docker\.sock", bug=True, allow_empty=True),
  Q("host networking", F, "services.gateway.network_mode", "ne", "host", bug=True, allow_empty=True), Q("cap_add only NET_BIND_SERVICE", F, "services.gateway.cap_add[*]", "eq", "NET_BIND_SERVICE", allow_empty=True),
  Q("drops all caps", F, "services.gateway.cap_drop", "contains", "ALL"), Q("port mapping kept", F, "services.gateway.ports[*]", "eq", "8080:80", keep=True), pinned(),
  Q("healthcheck kept", F, "services.gateway.healthcheck.test", "exists", keep=True)],
 start={F: d(r"""
services:
  gateway:
    image: ghcr.io/acme/gateway:0.9.4
    privileged: true
    network_mode: host
    ports:
      - "8080:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:80/ || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
""")}))

add(T("cp-fix-startup-race", "fix", "compose", "medium", """
The API crash-loops on `docker compose up` because Postgres is not accepting connections yet: `depends_on` only waits for the container to start.
Fix the compose file so `api` starts only when the database is actually ready (add the missing healthcheck to db with `pg_isready -U app -d app` and use the long-form depends_on condition). Nothing else should change.""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 3s
      retries: 10
  api:
    image: ghcr.io/acme/api:2.6.0
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:7000:7000"
""")},
 [VALID, Q("db has no healthcheck", F, "services.db.healthcheck.test", "regex", r"pg_isready.*-U app.*-d app", bug=True),
  Q("api depends_on db with service_healthy", F, "services.api.depends_on.db.condition", "eq", "service_healthy", bug=True),
  Q("api port kept", F, "services.api.ports[*]", "eq", "127.0.0.1:7000:7000", keep=True), Q("db image kept", F, "services.db.image", "eq", "postgres:16.3-alpine", keep=True)],
 start={F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
  api:
    image: ghcr.io/acme/api:2.6.0
    depends_on:
      - db
    ports:
      - "127.0.0.1:7000:7000"
""")}))

add(T("cp-fix-latest-exposed-db", "fix", "compose", "easy", """
Two problems were reported: deployments are not reproducible (floating image tags) and the database is reachable from the whole LAN. Fix them.
Use `postgres:16.3-alpine` and `ghcr.io/acme/shop:1.12.0`; the database must not publish any port to the host (services reach it over the compose network);
the shop keeps publishing 3000 but only on the loopback interface.""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
  shop:
    image: ghcr.io/acme/shop:1.12.0
    ports:
      - "127.0.0.1:3000:3000"
    depends_on:
      - db
""")},
 [VALID, Q("db image tag", F, "services.db.image", "eq", "postgres:16.3-alpine", bug=True), Q("shop image tag", F, "services.shop.image", "eq", "ghcr.io/acme/shop:1.12.0", bug=True),
  Q("db publishes nothing", F, "services.db.ports", "missing", bug=True), Q("shop only on loopback", F, "services.shop.ports[*]", "eq", "127.0.0.1:3000:3000", bug=True), pinned()],
 start={F: d(r"""
services:
  db:
    image: postgres:latest
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
  shop:
    image: ghcr.io/acme/shop
    ports:
      - "3000:3000"
    depends_on:
      - db
""")}))

add(T("cp-fix-plain-secrets", "fix", "compose", "medium", """
Credentials are committed in plain text in this compose file. Fix it: no literal passwords/keys anywhere in the YAML. Every secret value must be read from the
host environment via interpolation that fails loudly when missing (`${NAME:?message}`) - for DB_PASSWORD, REDIS_PASSWORD and STRIPE_KEY. Keep all service names, images and ports.""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD is required}
  cache:
    image: redis:7.2-alpine
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD:?REDIS_PASSWORD is required}"]
  shop:
    image: ghcr.io/acme/shop:1.12.0
    environment:
      DB_URL: postgres://shop:${DB_PASSWORD:?DB_PASSWORD is required}@db/shop
      REDIS_PASSWORD: ${REDIS_PASSWORD:?REDIS_PASSWORD is required}
      STRIPE_KEY: ${STRIPE_KEY:?STRIPE_KEY is required}
    ports:
      - "127.0.0.1:3000:3000"
""")},
 [VALID, C("not_contains", "plain-text secrets in file", bug=True, file=F, regex=r"(password|PASSWORD|STRIPE_KEY)\S*[:=]\s*[\"']?(?!\$\{)[A-Za-z0-9_\-]{6,}|sk_live_"),
  Q("db password interpolated", F, "services.db.environment.POSTGRES_PASSWORD", "regex", r"^\$\{DB_PASSWORD:\?.+\}$", bug=True),
  Q("stripe key interpolated", F, "services.shop.environment.STRIPE_KEY", "regex", r"^\$\{STRIPE_KEY:\?.+\}$", bug=True),
  Q("redis password not in command literal", F, "services.cache.command", "regex", r"\$\{REDIS_PASSWORD:\?", bug=True),
  Q("services kept", F, "services.*.image", "len_gte", 0, allow_empty=True), Q("shop port kept", F, "services.shop.ports[*]", "regex", r"3000:3000$", keep=True), pinned()],
 start={F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD: pg-s3cret-2024
  cache:
    image: redis:7.2-alpine
    command: ["redis-server", "--requirepass", "r3dis-s3cret"]
  shop:
    image: ghcr.io/acme/shop:1.12.0
    environment:
      DB_URL: postgres://shop:pg-s3cret-2024@db/shop
      REDIS_PASSWORD: r3dis-s3cret
      STRIPE_KEY: sk_live_51Hq3xYzABCDEFGH
    ports:
      - "127.0.0.1:3000:3000"
""")}))

add(T("cp-fix-network-isolation", "fix", "compose", "hard", """
Everything in this stack shares the default network, so the public-facing `web` container can talk straight to the database. Fix the topology: two networks, `frontend` and `backend`;
`backend` must be `internal: true` (no outbound internet). `web` is on frontend only; `api` is on both; `db` is on backend only. Keep images, `web`'s published port (`127.0.0.1:8080:8080`) and the db volume.""",
 {F: d(r"""
services:
  web:
    image: ghcr.io/acme/web:1.0.0
    ports:
      - "127.0.0.1:8080:8080"
    networks: [frontend]
  api:
    image: ghcr.io/acme/api:1.0.0
    networks: [frontend, backend]
  db:
    image: postgres:16.3-alpine
    volumes:
      - dbdata:/var/lib/postgresql/data
    networks: [backend]
networks:
  frontend:
  backend:
    internal: true
volumes:
  dbdata:
""")},
 [VALID, Q("backend network is internal", F, "networks.backend.internal", "eq", True, bug=True), C("contains", "frontend network declared", file=F, regex=r"^networks:\s*\n(\s+.*\n)*?\s+frontend:", bug=True),
  Q("web on frontend only", F, "services.web.networks", "eq", ["frontend"], bug=True), Q("api on both", F, "services.api.networks", "contains", "backend", bug=True),
  Q("api also frontend", F, "services.api.networks", "contains", "frontend"), Q("db on backend only", F, "services.db.networks", "eq", ["backend"], bug=True),
  Q("web port kept", F, "services.web.ports[*]", "eq", "127.0.0.1:8080:8080", keep=True), Q("db volume kept", F, "services.db.volumes[*]", "regex", r"^dbdata:/var/lib/postgresql/data", keep=True), pinned()],
 start={F: d(r"""
services:
  web:
    image: ghcr.io/acme/web:1.0.0
    ports:
      - "127.0.0.1:8080:8080"
  api:
    image: ghcr.io/acme/api:1.0.0
  db:
    image: postgres:16.3-alpine
    volumes:
      - dbdata:/var/lib/postgresql/data
volumes:
  dbdata:
""")}))

add(T("cp-harden-stack", "harden", "compose", "hard", """
Harden this compose stack for a production-like host without changing what it does (same services, images apart from tags, internal ports). Apply: pinned image tags (use the tags
`postgres:16.3-alpine`, `ghcr.io/acme/api:2.1.0`), no privileged containers or docker.sock, published ports bound to 127.0.0.1 only (db must not publish at all),
healthchecks on db and api (db: pg_isready, api: `wget -q --spider http://127.0.0.1:8000/health`), `api` waits for a healthy db, `api` runs read-only with `cap_drop: [ALL]`
and `no-new-privileges`, `restart: unless-stopped` on both, and a memory limit of at most 512M on api via `deploy.resources.limits`.""",
 {F: d(r"""
services:
  db:
    image: postgres:16.3-alpine
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 10
  api:
    image: ghcr.io/acme/api:2.1.0
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp
    cap_drop: [ALL]
    security_opt:
      - no-new-privileges:true
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget -q --spider http://127.0.0.1:8000/health || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
""")},
 [VALID, pinned(), Q("db tag", F, "services.db.image", "eq", "postgres:16.3-alpine", bug=True), noprivileged(), Q("privileged flagged", F, "services.*.privileged", "not_in", [True], allow_empty=True, bug=True),
  Q("docker.sock not mounted", F, "services.*.volumes[*]", "not_regex", r"docker\.sock", allow_empty=True, bug=True), Q("db not published", F, "services.db.ports", "missing", bug=True),
  Q("api bound to loopback", F, "services.api.ports[*]", "regex", r"^127\.0\.0\.1:", bug=True), Q("db healthcheck", F, "services.db.healthcheck.test", "regex", r"pg_isready", bug=True),
  Q("api healthcheck", F, "services.api.healthcheck.test", "regex", r"wget.*8000/health", bug=True), Q("api waits for healthy db", F, "services.api.depends_on.db.condition", "eq", "service_healthy", bug=True),
  Q("api read_only", F, "services.api.read_only", "eq", True, bug=True), Q("api cap_drop ALL", F, "services.api.cap_drop", "contains", "ALL", bug=True),
  Q("api no-new-privileges", F, "services.api.security_opt[*]", "regex", r"^no-new-privileges", mode="any", bug=True),
  Q("restart policy on both", F, "services.*.restart", "eq", "unless-stopped", bug=True), Q("api memory limit", F, "services.api.deploy.resources.limits.memory", "qty_lte", "512Mi", bug=True),
  Q("host network not used", F, "services.*.network_mode", "ne", "host", allow_empty=True)],
 start={F: d(r"""
services:
  db:
    image: postgres:latest
    privileged: true
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:?required}
  api:
    image: ghcr.io/acme/api:latest
    network_mode: host
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - db
""")}))

add(T("cp-convert-docker-run", "convert", "compose", "medium", """
Convert the `docker run` commands in `run.sh` into one `docker-compose.yml` with equivalent behaviour: same images, container networking by service name, env vars, port mappings, volumes (named volume `cachedata`),
restart policies, the healthcheck flags, and the start order (cache first, app after it is healthy).""",
 {F: d(r"""
services:
  cache:
    image: redis:7.2-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - cachedata:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 2s
      retries: 5
  app:
    image: ghcr.io/acme/app:1.4.0
    environment:
      CACHE_HOST: cache
      LOG_LEVEL: info
    ports:
      - "127.0.0.1:8080:8080"
    restart: on-failure
    depends_on:
      cache:
        condition: service_healthy
volumes:
  cachedata:
""")},
 [VALID, Q("cache image", F, "services.cache.image", "eq", "redis:7.2-alpine"), Q("cache command with appendonly", F, "services.cache.command", "regex", r"redis-server.*--appendonly.*yes"),
  Q("cache volume", F, "services.cache.volumes[*]", "eq", "cachedata:/data"), C("contains", "named volume declared", file=F, regex=r"^volumes:\s*\n\s+cachedata:"),
  Q("cache restart", F, "services.cache.restart", "eq", "unless-stopped"), Q("cache healthcheck", F, "services.cache.healthcheck.test", "regex", r"redis-cli.*ping"),
  Q("app image", F, "services.app.image", "eq", "ghcr.io/acme/app:1.4.0"), Q("CACHE_HOST=cache", F, "services.app.environment.CACHE_HOST", "eq", "cache"),
  Q("LOG_LEVEL", F, "services.app.environment.LOG_LEVEL", "eq", "info"), Q("app port loopback", F, "services.app.ports[*]", "eq", "127.0.0.1:8080:8080"),
  Q("app restart on-failure", F, "services.app.restart", "eq", "on-failure"), Q("app waits for healthy cache", F, "services.app.depends_on.cache.condition", "eq", "service_healthy")],
 start={"run.sh": d(r"""
#!/bin/sh
docker volume create cachedata
docker network create appnet
docker run -d --name cache --network appnet --restart unless-stopped \
  -v cachedata:/data \
  --health-cmd "redis-cli ping" --health-interval 5s --health-timeout 2s --health-retries 5 \
  redis:7.2-alpine redis-server --appendonly yes
# wait for the cache to be healthy before starting the app
docker run -d --name app --network appnet --restart on-failure \
  -e CACHE_HOST=cache -e LOG_LEVEL=info \
  -p 127.0.0.1:8080:8080 \
  ghcr.io/acme/app:1.4.0
""")}))

add(T("cp-convert-legacy-v2", "convert", "compose", "easy", """
Modernise this legacy compose v2-style file for the current Compose Specification: remove the obsolete top-level `version`, replace `links:` with the default project network plus a proper
`depends_on`, replace `container_name` usage (drop it - it blocks scaling), and replace `volumes_from` with a named volume `uploads` mounted at /uploads in both services. Keep images, ports and env.""",
 {F: d(r"""
services:
  api:
    image: ghcr.io/acme/api:1.0.0
    ports:
      - "127.0.0.1:5000:5000"
    environment:
      UPLOAD_DIR: /uploads
    volumes:
      - uploads:/uploads
    depends_on:
      - worker
  worker:
    image: ghcr.io/acme/worker:1.0.0
    volumes:
      - uploads:/uploads
volumes:
  uploads:
""")},
 [VALID, Q("obsolete version key", F, "version", "missing", bug=True), Q("links removed", F, "services.*.links", "missing", bug=True), Q("container_name removed", F, "services.*.container_name", "missing", bug=True),
  Q("volumes_from removed", F, "services.*.volumes_from", "missing", bug=True), Q("api mounts uploads", F, "services.api.volumes[*]", "eq", "uploads:/uploads"), Q("worker mounts uploads", F, "services.worker.volumes[*]", "eq", "uploads:/uploads"),
  C("contains", "uploads named volume declared", file=F, regex=r"^volumes:\s*\n\s+uploads:"), Q("api depends on worker", F, "services.api.depends_on", "contains", "worker"),
  Q("api port kept", F, "services.api.ports[*]", "eq", "127.0.0.1:5000:5000", keep=True), pinned()],
 start={F: d(r"""
version: "2.4"
services:
  api:
    image: ghcr.io/acme/api:1.0.0
    container_name: acme-api
    ports:
      - "127.0.0.1:5000:5000"
    environment:
      UPLOAD_DIR: /uploads
    links:
      - worker
    volumes_from:
      - worker
  worker:
    image: ghcr.io/acme/worker:1.0.0
    container_name: acme-worker
    volumes:
      - /uploads
""")}))
