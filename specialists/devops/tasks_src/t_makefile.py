from _dsl import C, Q, T, d

M = "Makefile"
TASKS = []
add = TASKS.append


def PH(*t):
    return C("mk_phony", "targets declared .PHONY: " + ", ".join(t), targets=list(t))


def PLAN(desc, target, steps, **kw):
    return C("mk_plan", desc, target=target, steps=steps, **kw)


OK = C("mk_parse_ok", "recipes are tab-indented, Makefile parses")

add(T("mk-go-basic", "write", "makefile", "easy", """
Write a `Makefile` for a Go service. Variable `BINARY ?= app`. Targets: `build` (`go build -o bin/$(BINARY) ./cmd/app`), `test` (`go test ./...`), `lint` (`go vet ./...`), `check` (runs lint then test),
`clean` (`rm -rf bin`). All of them are phony. Running plain `make` must run `build` (it is the default goal). Use tabs for recipes.""",
 {M: d(r"""
BINARY ?= app

.PHONY: build test lint check clean

build:
	go build -o bin/$(BINARY) ./cmd/app

test:
	go test ./...

lint:
	go vet ./...

check: lint test

clean:
	rm -rf bin
""")},
 [OK, C("mk_default", "default goal is build", target="build"), PH("build", "test", "lint", "check", "clean"), C("mk_var", "BINARY ?= app (overridable)", name="BINARY", regex=r"^app$"), C("contains", "BINARY set with ?=", file=M, regex=r"^BINARY\s*\?=\s*app"),
  PLAN("make build", "build", [r"^go build -o bin/app \./cmd/app$"]), PLAN("make build BINARY=svc honours override", "build", [r"-o bin/svc "], overrides={"BINARY": "svc"}),
  PLAN("make check = lint then test", "check", [r"^go vet \./\.\.\.$", r"^go test \./\.\.\.$"]), PLAN("make clean", "clean", [r"^rm -rf bin$"])]))

add(T("mk-docker-release", "write", "makefile", "medium", """
Write a `Makefile` for container releases. Variables: `IMAGE ?= ghcr.io/acme/app`, `VERSION ?= $(shell git describe --tags --always --dirty)`. Phony targets: `test` (`go test ./...`), `docker-build` (`docker build -t $(IMAGE):$(VERSION) .`),
`docker-push` (needs docker-build; `docker push $(IMAGE):$(VERSION)`), and `release` which depends on `test` and `docker-push` and runs them in that order (tests first). Default goal `test`. Recipes must not echo-hide anything (no `@`).""",
 {M: d(r"""
IMAGE ?= ghcr.io/acme/app
VERSION ?= $(shell git describe --tags --always --dirty)

.PHONY: test docker-build docker-push release

test:
	go test ./...

docker-build:
	docker build -t $(IMAGE):$(VERSION) .

docker-push: docker-build
	docker push $(IMAGE):$(VERSION)

release: test docker-push
""")},
 [OK, C("mk_default", "default goal test", target="test"), PH("test", "docker-build", "docker-push", "release"), C("contains", "IMAGE ?=", file=M, regex=r"^IMAGE\s*\?=\s*ghcr\.io/acme/app\s*$"),
  C("contains", "VERSION ?= $(shell git describe ...)", file=M, regex=r"^VERSION\s*\?=\s*\$\(shell git describe --tags --always --dirty\)\s*$"),
  PLAN("release plan order", "release", [r"^go test \./\.\.\.$", r"^docker build -t ghcr\.io/acme/app:.* \.$", r"^docker push ghcr\.io/acme/app:"]),
  PLAN("override IMAGE", "docker-push", [r"^docker build -t example/x:", r"^docker push example/x:"], overrides={"IMAGE": "example/x"}),
  C("not_contains", "no @-silenced recipe lines", file=M, regex=r"^\t@", flags="m")]))

add(T("mk-self-documenting", "write", "makefile", "medium", """
Write a self-documenting `Makefile`: the default goal is `help`, which lists every documented target with its description by grepping the Makefile for `target: ## description` lines (use `$(MAKEFILE_LIST)`; e.g. with `grep -E` and `awk`).
Targets (each with a `## ` description comment on its line and phony): `install` (`pip install -r requirements.txt`), `test` (`pytest -q`), `lint` (`ruff check .`), `fmt` (`ruff format .`), `help`.
In recipes a literal `$` for the shell must be written `$$` (e.g. in awk programs).""",
 {M: d(r"""
.DEFAULT_GOAL := help
.PHONY: help install test lint fmt

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "%-12s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run the tests
	pytest -q

lint: ## Static checks
	ruff check .

fmt: ## Format the code
	ruff format .
""")},
 [OK, C("mk_default", "default goal help", target="help"), PH("help", "install", "test", "lint", "fmt"), C("contains", "help uses MAKEFILE_LIST", file=M, regex=r"\$\(MAKEFILE_LIST\)"),
  C("contains", "every target documented with ##", file=M, regex=r"^(install|test|lint|fmt|help):.*## \S+", count_min=5), C("contains", "awk/grep program escapes $ as $$", file=M, regex=r"\$\$"),
  PLAN("install", "install", [r"pip install -r requirements\.txt"]), PLAN("test", "test", [r"pytest -q"]), PLAN("lint", "lint", [r"ruff check \."]), PLAN("fmt", "fmt", [r"ruff format \."]),
  PLAN("help greps the makefile", "help", [r"grep .*##"])]))

add(T("mk-python-venv-stamp", "write", "makefile", "hard", """
Write a `Makefile` that builds a Python virtualenv in `.venv` incrementally with a real file target: rule `.venv/bin/activate` depends on `requirements.txt`, creates the venv (`python3 -m venv .venv`), installs requirements with the venv's pip
(`.venv/bin/pip install -r requirements.txt`) and finally `touch`es the target so make only reinstalls when requirements.txt changes. Phony `venv` target depends on it. `test` depends on the venv and runs `.venv/bin/pytest -q`.
`clean` removes `.venv`. Default goal `test`. Define `VENV := .venv` and use `$(VENV)` everywhere.""",
 {M: d(r"""
VENV := .venv

.PHONY: venv test clean

test: venv
	$(VENV)/bin/pytest -q

venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	touch $(VENV)/bin/activate

clean:
	rm -rf $(VENV)
""")},
 [OK, C("mk_default", "default goal test", target="test"), PH("venv", "test", "clean"), C("mk_var", "VENV := .venv", name="VENV", regex=r"^\.venv$"),
  C("contains", "stamp rule depends on requirements.txt", file=M, regex=r"^(\$\(VENV\)|\.venv)/bin/activate:\s*requirements\.txt\s*$"),
  PLAN("test: venv created, deps installed, stamped, then pytest", "test", [r"^python3 -m venv \.venv$", r"^\.venv/bin/pip install -r requirements\.txt$", r"^touch \.venv/bin/activate$", r"^\.venv/bin/pytest -q$"]),
  C("contains", "uses $(VENV) variable", file=M, regex=r"\$\(VENV\)", count_min=4), PLAN("clean", "clean", [r"^rm -rf \.venv$"])]))

add(T("mk-env-guard", "write", "makefile", "hard", """
Write a `Makefile` with a `deploy` target that deploys to Kubernetes for `ENV` (default `dev`). `ENV` must be one of `dev`, `staging`, `prod`; any other value must abort BEFORE anything runs using make's `$(error ...)` (e.g. via
`ifeq`/`$(filter ...)` at parse time). `deploy` runs `kubectl apply -n $(ENV) -f k8s/` and, for `prod` only, a prerequisite target `confirm-prod`... keep it simple: `deploy` always runs
`kubectl apply -n $(ENV) -f k8s/` followed by `kubectl rollout status -n $(ENV) deployment/app`. Also add phony `plan` (`kubectl diff -n $(ENV) -f k8s/`). `make` with no target runs `plan`.""",
 {M: d(r"""
ENV ?= dev

ifeq ($(filter $(ENV),dev staging prod),)
$(error ENV must be one of dev, staging, prod (got '$(ENV)'))
endif

.DEFAULT_GOAL := plan
.PHONY: plan deploy

plan:
	kubectl diff -n $(ENV) -f k8s/

deploy:
	kubectl apply -n $(ENV) -f k8s/
	kubectl rollout status -n $(ENV) deployment/app
""")},
 [OK, C("mk_default", "default goal plan", target="plan"), PH("plan", "deploy"), C("contains", "ENV ?= dev", file=M, regex=r"^ENV\s*\?=\s*dev\s*$"), C("contains", "parse-time validation with $(error", file=M, regex=r"\$\(error [^\n]*ENV"),
  C("contains", "uses filter or ifeq to validate", file=M, regex=r"\$\(filter|ifeq|ifneq"),
  PLAN("deploy dev", "deploy", [r"^kubectl apply -n dev -f k8s/$", r"^kubectl rollout status -n dev deployment/app$"]),
  PLAN("deploy prod via override", "deploy", [r"^kubectl apply -n prod -f k8s/$", r"^kubectl rollout status -n prod deployment/app$"], overrides={"ENV": "prod"}),
  PLAN("plan", "plan", [r"^kubectl diff -n dev -f k8s/$"])]))

add(T("mk-convert-build-script", "convert", "makefile", "medium", """
Convert `build.sh` into a `Makefile` with equivalent, individually runnable steps: phony targets `deps`, `lint`, `test`, `build`, `package`, `all`. Dependencies: `lint` and `test` need `deps`; `build` needs both; `package` needs `build`; `all` needs `package` (and is the default goal).
Each target runs the corresponding command from the script (in the same form). `clean` removes `dist` and `node_modules`. Use a `NODE ?= node` style variable only if you want to, but commands must read exactly as in the script.""",
 {M: d(r"""
.DEFAULT_GOAL := all
.PHONY: all deps lint test build package clean

all: package

deps:
	npm ci

lint: deps
	npx eslint .

test: deps
	npm test

build: lint test
	npm run build

package: build
	tar -czf dist.tar.gz dist

clean:
	rm -rf dist node_modules
""")},
 [OK, C("mk_default", "default goal all", target="all"), PH("all", "deps", "lint", "test", "build", "package", "clean"),
  PLAN("all runs the whole chain in order", "all", [r"^npm ci$", r"^npx eslint \.$", r"^npm test$", r"^npm run build$", r"^tar -czf dist\.tar\.gz dist$"]),
  PLAN("deps runs only npm ci", "deps", [r"^npm ci$"], forbid=[r"eslint", r"npm test"]), PLAN("lint pulls in deps only", "lint", [r"^npm ci$", r"^npx eslint \.$"], forbid=[r"npm test", r"tar "]),
  PLAN("build needs lint and test", "build", [r"^npm ci$", r"^npx eslint \.$|^npm test$", r"^npm run build$"]), PLAN("npm ci runs once", "build", [r"^npm ci$"], forbid=[]),
  PLAN("clean", "clean", [r"^rm -rf dist node_modules$"])],
 start={"build.sh": d(r"""
#!/bin/sh
set -e
npm ci
npx eslint .
npm test
npm run build
tar -czf dist.tar.gz dist
""")}))

add(T("mk-convert-npm-scripts", "convert", "makefile", "medium", """
Convert the `scripts` in `package.json` into a Makefile (the team is moving to a language-agnostic task runner). Phony targets with identical commands: `dev`, `build`, `test`, `lint`, `format`, plus `ci` that runs lint, test, build in that order.
`build` must be run before `start` (`start` depends on `build`). Default goal `dev`.""",
 {M: d(r"""
.DEFAULT_GOAL := dev
.PHONY: dev build start test lint format ci

dev:
	vite --port 5173

build:
	tsc -b && vite build

start: build
	node server/index.js

test:
	vitest run --coverage

lint:
	eslint . --max-warnings 0

format:
	prettier --write .

ci: lint test build
""")},
 [OK, C("mk_default", "default goal dev", target="dev"), PH("dev", "build", "start", "test", "lint", "format", "ci"), PLAN("dev", "dev", [r"^vite --port 5173$"]), PLAN("build", "build", [r"^tsc -b && vite build$"]),
  PLAN("start builds first", "start", [r"^tsc -b && vite build$", r"^node server/index\.js$"]), PLAN("test", "test", [r"^vitest run --coverage$"]), PLAN("lint", "lint", [r"^eslint \. --max-warnings 0$"]),
  PLAN("format", "format", [r"^prettier --write \.$"]), PLAN("ci order", "ci", [r"^eslint \. --max-warnings 0$", r"^vitest run --coverage$", r"^tsc -b && vite build$"])],
 start={"package.json": d(r"""
{
  "name": "webapp",
  "scripts": {
    "dev": "vite --port 5173",
    "build": "tsc -b && vite build",
    "start": "node server/index.js",
    "test": "vitest run --coverage",
    "lint": "eslint . --max-warnings 0",
    "format": "prettier --write ."
  }
}
""")}))

add(T("mk-fix-tabs-phony", "fix", "makefile", "easy", """
`make` prints `*** missing separator` and, after that is fixed, `make test` says "'test' is up to date" because a `test/` directory exists. Fix the Makefile: recipes must use tabs, the clashing/non-file targets are phony,
and plain `make` should build the application (put `all` first or set the default goal). Keep the commands.""",
 {M: d(r"""
.PHONY: all build test clean

all: build

build:
	cc -o app main.c

test: build
	./app --selftest

clean:
	rm -f app
""")},
 [C("mk_parse_ok", "recipes indented with spaces ('missing separator')", bug=True), PH("test", "clean", "build", "all"), C("mk_default", "default goal builds the app", target="all", bug=True),
  PLAN("build command kept", "build", [r"^cc -o app main\.c$"]), PLAN("test runs selftest after build", "test", [r"^cc -o app main\.c$", r"^\./app --selftest$"]), PLAN("clean", "clean", [r"^rm -f app$"])],
 start={M: "build:\n    cc -o app main.c\n\ntest: build\n    ./app --selftest\n\nclean:\n    rm -f app\n\nall: build\n"}))

add(T("mk-fix-shell-vars", "fix", "makefile", "hard", """
This Makefile mis-handles shell vs make syntax. Problems: `$HOME` and `$(date +%s)`-style shell expansions are eaten by make (needs `$$`), each recipe line runs in its own shell so the `cd` has no effect on the next line,
and the build number is recomputed lazily every time it is referenced (`=` instead of `:=`). Fix: `BUILD := $(shell date +%s)` evaluated once, the `cd sub` and `make` joined into one shell command (`cd sub && $(MAKE)`), and the shell variables escaped
(`$$HOME`, `$$(...)`). Targets `info` and `sub` stay phony.""",
 {M: d(r"""
BUILD := $(shell date +%s)

.PHONY: info sub

info:
	@echo "home=$$HOME build=$(BUILD) user=$$(id -un)"

sub:
	cd sub && $(MAKE)
""")},
 [C("mk_parse_ok", "parses", keep=True), C("contains", "BUILD evaluated once with :=", file=M, regex=r"^BUILD\s*:=\s*\$\(shell date \+%s\)\s*$", bug=True), C("contains", "shell variable escaped as $$HOME", file=M, regex=r"\$\$HOME", bug=True),
  C("not_contains", "unescaped $HOME / $(id", file=M, regex=r"(?<!\$)\$HOME|(?<!\$)\$\(id", bug=True), C("contains", "cd joined with the following command", file=M, regex=r"cd sub\s*(&&|;)\s*\$\(MAKE\)|cd sub\s*\\\s*\n\s*&&", bug=True),
  PH("info", "sub"), PLAN("sub plan has combined command", "sub", [r"^cd sub && .*make|^cd sub && \S*"]), C("not_contains", "cd on its own recipe line", file=M, regex=r"^\tcd sub\s*$", bug=True)],
 start={M: d(r"""
BUILD = $(shell date +%s)

.PHONY: info sub

info:
	@echo "home=$HOME build=$(BUILD) user=$(id -un)"

sub:
	cd sub
	$(MAKE)
""")}))

add(T("mk-fix-always-rebuilds", "fix", "makefile", "hard", """
`make` recompiles everything every time and ignores header changes. Fix the Makefile to be incremental: `app` must depend on the object files and link them (use `$@` / `$^`), a pattern rule `%.o: %.c` compiles with `$<`/`$@`
(and objects depend on `util.h`), file targets (`app`, objects) must NOT be declared phony, and only `all`, `clean` remain phony. Keep `CC ?= cc`, `CFLAGS ?= -O2 -Wall`. Default goal: `all`, which builds `app`.""",
 {M: d(r"""
CC ?= cc
CFLAGS ?= -O2 -Wall
OBJS := main.o util.o

.PHONY: all clean

all: app

app: $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c util.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f app $(OBJS)
""")},
 [C("mk_parse_ok", "parses", keep=True), C("not_contains", "file targets declared phony", file=M, regex=r"^\.PHONY:.*\b(app|main\.o|util\.o|%\.o)\b", bug=True), PH("all", "clean"),
  C("contains", "app depends on objects", file=M, regex=r"^app:\s*(\$\(OBJS\)|main\.o util\.o)", bug=True), C("contains", "link uses automatic variables", file=M, regex=r"-o \$@ \$\^", bug=True),
  C("contains", "pattern rule for objects", file=M, regex=r"^%\.o:\s*%\.c", bug=True), C("contains", "objects depend on util.h", file=M, regex=r"^%\.o:.*util\.h"), C("contains", "compile uses $< and $@", file=M, regex=r"-c \$< -o \$@", bug=True),
  C("mk_default", "default goal all", target="all"), C("contains", "CC and CFLAGS overridable", file=M, regex=r"^CC\s*\?=\s*cc[\s\S]*^CFLAGS\s*\?=\s*-O2 -Wall", keep=True)],
 start={M: d(r"""
CC ?= cc
CFLAGS ?= -O2 -Wall

.PHONY: all app main.o util.o clean

all: app

app:
	$(CC) $(CFLAGS) -c main.c -o main.o
	$(CC) $(CFLAGS) -c util.c -o util.o
	$(CC) $(CFLAGS) -o app main.o util.o

clean:
	rm -f app main.o util.o
""")}))

add(T("mk-harden-shell-flags", "harden", "makefile", "medium", """
Harden this Makefile so failures are not silently swallowed: use bash with strict flags (`SHELL := bash`, `.SHELLFLAGS := -eu -o pipefail -c`), delete half-written targets when a recipe fails (`.DELETE_ON_ERROR:`),
warn about undefined variables (`MAKEFLAGS += --warn-undefined-variables`) and drop the `-` prefixes that ignore errors on important commands (keep the `-` only on `rm -f` cleanup if you like - `rm -f` already ignores missing files, so it is not needed).
Targets and commands stay: `report.txt` is produced by `sort data.txt | uniq -c > report.txt`; `all: report.txt`; `clean` removes it.""",
 {M: d(r"""
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
.DELETE_ON_ERROR:
.PHONY: all clean

all: report.txt

report.txt: data.txt
	sort data.txt | uniq -c > report.txt

clean:
	rm -f report.txt
""")},
 [C("mk_parse_ok", "parses", keep=True), C("contains", "SHELL := bash", file=M, regex=r"^SHELL\s*:?=\s*(/bin/|/usr/bin/)?bash\s*$", bug=True), C("contains", "strict shell flags", file=M, regex=r"^\.SHELLFLAGS\s*:?=\s*-[a-z]*e[a-z]*u[a-z]*\s+-o pipefail\s+-c|^\.SHELLFLAGS\s*:?=\s*-eu -o pipefail -c", bug=True),
  C("mk_target", ".DELETE_ON_ERROR declared", target=".DELETE_ON_ERROR", bug=True), C("contains", "warn undefined variables", file=M, regex=r"MAKEFLAGS\s*\+?=.*--warn-undefined-variables", bug=True),
  C("not_contains", "no error-ignoring '-' recipe prefixes on the pipeline", file=M, regex=r"^\t-\s*sort", bug=True), PH("all", "clean"), C("mk_default", "default goal all", target="all"),
  PLAN("report command kept", "report.txt", [r"^sort data\.txt \| uniq -c > report\.txt$"], keep=True)],
 start={M: d(r"""
.PHONY: all clean

all: report.txt

report.txt: data.txt
	-sort data.txt | uniq -c > report.txt

clean:
	-rm -f report.txt
""")}))
