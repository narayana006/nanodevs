from _dsl import C, Q, T, d

TASKS = []
add = TASKS.append
CT = "spec.template.spec.containers[*]"


def ctr(desc, file, path, op, value=None, kind="Deployment", **kw):
    """check applied to EVERY container of the workload(s) of that kind"""
    return Q(desc, file, path, op, value, select={"kind": kind}, each=CT, **kw)


def pod(desc, file, path, op, value=None, kind="Deployment", **kw):
    return Q(desc, file, "spec.template." + path, op, value, select={"kind": kind}, **kw)


def nolatest(f, kind="Deployment", **kw):
    return ctr("every container image has an explicit non-latest tag", f, "image", "regex", r"^[^:@\s]+(/[^:@\s]+)*:(?!latest$)[\w][\w.\-]*$|@sha256:", kind=kind, **kw)


def limits(f, kind="Deployment", **kw):
    return [ctr("memory request set on every container", f, "resources.requests.memory", "exists", kind=kind, **kw),
            ctr("cpu request set on every container", f, "resources.requests.cpu", "exists", kind=kind, **kw),
            ctr("memory limit set on every container", f, "resources.limits.memory", "exists", kind=kind, **kw)]


def probes(f, kind="Deployment", **kw):
    return [ctr("readinessProbe on every container", f, "readinessProbe", "exists", kind=kind, **kw),
            ctr("livenessProbe on every container", f, "livenessProbe", "exists", kind=kind, **kw)]


def sec(f, kind="Deployment", **kw):
    return [ctr("allowPrivilegeEscalation: false", f, "securityContext.allowPrivilegeEscalation", "eq", False, kind=kind, **kw),
            ctr("capabilities drop ALL", f, "securityContext.capabilities.drop", "contains", "ALL", kind=kind, **kw),
            ctr("readOnlyRootFilesystem: true", f, "securityContext.readOnlyRootFilesystem", "eq", True, kind=kind, **kw),
            C("q", "runs as non-root (pod or container level)", file=f, select={"kind": kind}, path="spec.template.spec.securityContext.runAsNonRoot | spec.template.spec.containers[*].securityContext.runAsNonRoot", op="eq", value=True, mode="any", **{k: v for k, v in kw.items()})]


# -------------------------------------------------------------------- write
F = "deployment.yaml"
add(T("k8s-deploy-basic", "write", "k8s", "easy", """
Write `deployment.yaml`: a Deployment `web` (namespace default, label `app: web`) with 3 replicas running `ghcr.io/acme/web:1.8.2` that listens on named container port `http` (8080).
Add a readinessProbe (HTTP GET /ready) and a livenessProbe (HTTP GET /healthz), both on the named port, resource requests (cpu 100m, memory 128Mi) and a memory limit of 256Mi.
The selector and pod template labels must match.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: default
  labels:
    app: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: ghcr.io/acme/web:1.8.2
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 256Mi
""")},
 [C("valid", "valid YAML", file=F), Q("kind Deployment apps/v1", F, "apiVersion", "eq", "apps/v1", select={"kind": "Deployment"}), Q("replicas 3", F, "spec.replicas", "eq", 3, select={"kind": "Deployment"}),
  C("k8s_selectors", "selector.matchLabels is a subset of the template labels", file=F), nolatest(F),
  ctr("container port 8080", F, "ports[*].containerPort", "eq", 8080),
  ctr("readiness path /ready", F, "readinessProbe.httpGet.path", "eq", "/ready"), ctr("liveness path /healthz", F, "livenessProbe.httpGet.path", "eq", "/healthz"),
  C("k8s_probe_ports", "probes reference declared ports", file=F), ctr("probes use the named port", F, "readinessProbe.httpGet.port | livenessProbe.httpGet.port", "eq", "http"),
  ctr("cpu request 100m", F, "resources.requests.cpu", "eq", "100m"), ctr("memory request 128Mi", F, "resources.requests.memory", "eq", "128Mi"), ctr("memory limit 256Mi", F, "resources.limits.memory", "eq", "256Mi")]))

F = "app.yaml"
add(T("k8s-deploy-service", "write", "k8s", "easy", """
Write `app.yaml` (two documents): a Deployment `api` (2 replicas, image `ghcr.io/acme/api:3.1.0`, label `app: api`, container port named `http` = 3000, requests cpu 50m/memory 64Mi, memory limit 128Mi)
and a ClusterIP Service `api` exposing port 80 that forwards to the container's named port `http`. Selectors must really match the pods.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  labels:
    app: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: ghcr.io/acme/api:3.1.0
          ports:
            - name: http
              containerPort: 3000
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: api
  labels:
    app: api
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: http
""")},
 [C("valid", "valid multi-doc YAML", file=F), C("docs", "exactly a Deployment and a Service", file=F, min=2, max=2), C("k8s_selectors", "Deployment + Service selectors match pod labels", file=F),
  C("k8s_ports_match", "Service targetPort resolves to a container port", file=F), nolatest(F), *limits(F),
  Q("service port 80", F, "spec.ports[*].port", "eq", 80, select={"kind": "Service"}), Q("service type ClusterIP", F, "spec.type", "in", ["ClusterIP", None], select={"kind": "Service"}, allow_empty=True),
  Q("replicas 2", F, "spec.replicas", "eq", 2, select={"kind": "Deployment"})]))

F = "deployment.yaml"
add(T("k8s-restricted-pod", "write", "k8s", "medium", """
Write `deployment.yaml` for Deployment `reports` (1 replica, `ghcr.io/acme/reports:0.7.0`, label `app: reports`, port 8080) that satisfies the Kubernetes *restricted* Pod Security profile:
pod runs as non-root user/group/fsGroup 10001 with `seccompProfile: RuntimeDefault`; container has `allowPrivilegeEscalation: false`, all capabilities dropped, read-only root filesystem.
The app writes scratch files to /tmp, so mount an `emptyDir` volume named `tmp` at /tmp (size limit 64Mi). Disable automatic service account token mounting. Add cpu/memory requests and a memory limit.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reports
  labels:
    app: reports
spec:
  replicas: 1
  selector:
    matchLabels:
      app: reports
  template:
    metadata:
      labels:
        app: reports
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: reports
          image: ghcr.io/acme/reports:0.7.0
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 256Mi
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            sizeLimit: 64Mi
""")},
 [C("valid", "valid YAML", file=F), C("k8s_selectors", "selectors", file=F), nolatest(F), *sec(F), pod("runAsUser 10001", F, "spec.securityContext.runAsUser", "eq", 10001),
  pod("fsGroup 10001", F, "spec.securityContext.fsGroup", "eq", 10001), pod("seccomp RuntimeDefault", F, "spec.securityContext.seccompProfile.type", "eq", "RuntimeDefault"),
  pod("no token automount", F, "spec.automountServiceAccountToken", "eq", False), ctr("emptyDir tmp mounted at /tmp", F, "volumeMounts[*]", "eq", {"name": "tmp", "mountPath": "/tmp"}, mode="any"),
  pod("emptyDir volume tmp with sizeLimit", F, "spec.volumes[*].emptyDir.sizeLimit", "eq", "64Mi"), C("k8s_refs_exist", "volumeMounts match volumes", file=F), *limits(F)]))

F = "app.yaml"
add(T("k8s-configmap-consumption", "write", "k8s", "medium", """
Write `app.yaml` with: a ConfigMap `app-config` holding `LOG_LEVEL: info`, `FEATURE_X: "true"` and a file key `app.properties` (any 2-line content); and a Deployment `app` (`ghcr.io/acme/app:2.0.0`, label `app: app`, 2 replicas)
that loads ALL ConfigMap keys as environment variables with `envFrom`, and ALSO mounts the `app.properties` key as a read-only file at /etc/app/app.properties using a ConfigMap volume (`subPath`). All references must resolve.""",
 {F: d(r"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: info
  FEATURE_X: "true"
  app.properties: |
    mode=prod
    retries=3
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  labels:
    app: app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
        - name: app
          image: ghcr.io/acme/app:2.0.0
          envFrom:
            - configMapRef:
                name: app-config
          volumeMounts:
            - name: config
              mountPath: /etc/app/app.properties
              subPath: app.properties
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: app-config
""")},
 [C("valid", "valid YAML", file=F), Q("ConfigMap keys", F, "data.LOG_LEVEL", "eq", "info", select={"kind": "ConfigMap", "metadata.name": "app-config"}),
  Q("FEATURE_X quoted string", F, "data.FEATURE_X", "eq", "true", select={"kind": "ConfigMap"}), Q("FEATURE_X is a string, not a bool", F, "data.FEATURE_X", "type", "str", select={"kind": "ConfigMap"}),
  Q("app.properties key", F, 'data."app.properties"', "regex", r"=", select={"kind": "ConfigMap"}),
  ctr("envFrom configMapRef app-config", F, "envFrom[*].configMapRef.name", "eq", "app-config"), ctr("file mounted at /etc/app/app.properties", F, "volumeMounts[*].mountPath", "eq", "/etc/app/app.properties", mode="any"),
  ctr("subPath app.properties", F, "volumeMounts[*].subPath", "eq", "app.properties"), ctr("mount read-only", F, "volumeMounts[*].readOnly", "eq", True),
  C("k8s_refs_exist", "ConfigMap/volume refs resolve inside the file", file=F), C("k8s_selectors", "selectors", file=F), nolatest(F)]))

F = "cronjob.yaml"
add(T("k8s-cronjob-safe", "write", "k8s", "medium", """
Write `cronjob.yaml`: CronJob `db-backup` running `ghcr.io/acme/backup:1.3.0` (command `["/bin/backup", "--full"]`) every day at 02:30 UTC (`30 2 * * *`, `timeZone: Etc/UTC`).
Runs must never overlap (`concurrencyPolicy: Forbid`), keep 3 successful and 1 failed job in history, the job template retries at most 2 times (`backoffLimit: 2`), is killed after 1 hour (`activeDeadlineSeconds: 3600`),
pods use `restartPolicy: OnFailure`... NOTE: Job pods must use `OnFailure` or `Never` - pick `Never`. Add resource requests/limits and run as non-root (UID 10001).""",
 {F: d(r"""
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "30 2 * * *"
  timeZone: Etc/UTC
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 3600
      template:
        spec:
          restartPolicy: Never
          securityContext:
            runAsNonRoot: true
            runAsUser: 10001
          containers:
            - name: backup
              image: ghcr.io/acme/backup:1.3.0
              command: ["/bin/backup", "--full"]
              resources:
                requests:
                  cpu: 100m
                  memory: 128Mi
                limits:
                  memory: 512Mi
""")},
 [C("valid", "valid YAML", file=F), Q("batch/v1", F, "apiVersion", "eq", "batch/v1", select={"kind": "CronJob"}), Q("schedule", F, "spec.schedule", "eq", "30 2 * * *", select={"kind": "CronJob"}),
  Q("timeZone", F, "spec.timeZone", "eq", "Etc/UTC", select={"kind": "CronJob"}), Q("Forbid", F, "spec.concurrencyPolicy", "eq", "Forbid", select={"kind": "CronJob"}),
  Q("history limits", F, "spec.successfulJobsHistoryLimit", "eq", 3, select={"kind": "CronJob"}), Q("failed history", F, "spec.failedJobsHistoryLimit", "eq", 1, select={"kind": "CronJob"}),
  Q("backoffLimit", F, "spec.jobTemplate.spec.backoffLimit", "lte", 2, select={"kind": "CronJob"}), Q("deadline", F, "spec.jobTemplate.spec.activeDeadlineSeconds", "lte", 3600, select={"kind": "CronJob"}),
  Q("restartPolicy Never/OnFailure", F, "spec.jobTemplate.spec.template.spec.restartPolicy", "in", ["Never", "OnFailure"], select={"kind": "CronJob"}),
  Q("command", F, "spec.jobTemplate.spec.template.spec.containers[*].command", "eq", ["/bin/backup", "--full"], select={"kind": "CronJob"}),
  Q("pinned image", F, "spec.jobTemplate.spec.template.spec.containers[*].image", "regex", r":1\.3\.0$", select={"kind": "CronJob"}),
  Q("non-root", F, "spec.jobTemplate.spec.template.spec.securityContext.runAsNonRoot | spec.jobTemplate.spec.template.spec.containers[*].securityContext.runAsNonRoot", "eq", True, select={"kind": "CronJob"}, mode="any"),
  Q("memory limit", F, "spec.jobTemplate.spec.template.spec.containers[*].resources.limits.memory", "exists", select={"kind": "CronJob"})]))

F = "statefulset.yaml"
add(T("k8s-statefulset-db", "write", "k8s", "hard", """
Write `statefulset.yaml` with a headless Service `pg` (`clusterIP: None`, port 5432 named `pg`, selector `app: pg`) and a StatefulSet `pg` (3 replicas, `serviceName: pg`, image `postgres:16.3`, container port `pg`=5432).
Each replica gets its own 10Gi `ReadWriteOnce` volume from `volumeClaimTemplates` (claim name `data`, mounted at /var/lib/postgresql/data), `podManagementPolicy: OrderedReady`, `terminationGracePeriodSeconds: 60`,
a readinessProbe with an exec `pg_isready -U postgres`, and a memory request+limit of 1Gi, cpu request 250m. Password comes from Secret `pg-auth` key `password` via `secretKeyRef` (env POSTGRES_PASSWORD) - do not define the Secret and do not use a literal.""",
 {F: d(r"""
apiVersion: v1
kind: Service
metadata:
  name: pg
  labels:
    app: pg
spec:
  clusterIP: None
  selector:
    app: pg
  ports:
    - name: pg
      port: 5432
      targetPort: pg
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: pg
spec:
  serviceName: pg
  replicas: 3
  podManagementPolicy: OrderedReady
  selector:
    matchLabels:
      app: pg
  template:
    metadata:
      labels:
        app: pg
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: pg
          image: postgres:16.3
          ports:
            - name: pg
              containerPort: 5432
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pg-auth
                  key: password
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "postgres"]
            periodSeconds: 10
          resources:
            requests:
              cpu: 250m
              memory: 1Gi
            limits:
              memory: 1Gi
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
""")},
 [C("valid", "valid YAML", file=F), Q("service headless", F, "spec.clusterIP", "eq", "None", select={"kind": "Service"}), Q("serviceName pg", F, "spec.serviceName", "eq", "pg", select={"kind": "StatefulSet"}),
  C("k8s_selectors", "selectors", file=F), C("k8s_ports_match", "service targetPort exists", file=F), Q("replicas 3", F, "spec.replicas", "eq", 3, select={"kind": "StatefulSet"}),
  Q("volumeClaimTemplate data 10Gi", F, "spec.volumeClaimTemplates[*].spec.resources.requests.storage", "eq", "10Gi", select={"kind": "StatefulSet"}),
  Q("claim named data", F, "spec.volumeClaimTemplates[*].metadata.name", "eq", "data", select={"kind": "StatefulSet"}),
  Q("RWO", F, "spec.volumeClaimTemplates[*].spec.accessModes", "contains", "ReadWriteOnce", select={"kind": "StatefulSet"}),
  ctr("mounts data", F, "volumeMounts[*].name", "eq", "data", kind="StatefulSet", mode="any"), Q("grace period", F, "spec.template.spec.terminationGracePeriodSeconds", "eq", 60, select={"kind": "StatefulSet"}),
  ctr("password from secretKeyRef", F, "env[*].valueFrom.secretKeyRef.name", "eq", "pg-auth", kind="StatefulSet"), ctr("no literal POSTGRES_PASSWORD value", F, "env[*].value", "not_regex", r".", kind="StatefulSet", allow_empty=True),
  ctr("readiness exec pg_isready", F, "readinessProbe.exec.command", "regex", r"pg_isready", kind="StatefulSet"), ctr("memory request=limit 1Gi", F, "resources.limits.memory", "eq", "1Gi", kind="StatefulSet"),
  ctr("memory request 1Gi", F, "resources.requests.memory", "eq", "1Gi", kind="StatefulSet"), ctr("cpu request", F, "resources.requests.cpu", "eq", "250m", kind="StatefulSet")]))

F = "scaling.yaml"
add(T("k8s-hpa-pdb", "write", "k8s", "medium", """
Write `scaling.yaml` containing: Deployment `shop` (3 replicas, `ghcr.io/acme/shop:4.2.0`, label `app: shop`, port 8080, cpu request 200m, memory request 256Mi, memory limit 512Mi),
a HorizontalPodAutoscaler (apiVersion `autoscaling/v2`) targeting that Deployment with min 3 / max 12 replicas scaling on CPU average utilization 65%, and a PodDisruptionBudget guaranteeing at least 2 pods
available (`policy/v1`) selecting the same pods.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop
  labels:
    app: shop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shop
  template:
    metadata:
      labels:
        app: shop
    spec:
      containers:
        - name: shop
          image: ghcr.io/acme/shop:4.2.0
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              memory: 512Mi
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop
  minReplicas: 3
  maxReplicas: 12
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 65
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: shop
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: shop
""")},
 [C("valid", "valid YAML", file=F), C("k8s_selectors", "selectors", file=F), nolatest(F), *limits(F), Q("HPA apiVersion", F, "apiVersion", "eq", "autoscaling/v2", select={"kind": "HorizontalPodAutoscaler"}),
  Q("HPA target", F, "spec.scaleTargetRef.name", "eq", "shop", select={"kind": "HorizontalPodAutoscaler"}), Q("HPA target kind", F, "spec.scaleTargetRef.kind", "eq", "Deployment", select={"kind": "HorizontalPodAutoscaler"}),
  Q("min 3", F, "spec.minReplicas", "eq", 3, select={"kind": "HorizontalPodAutoscaler"}), Q("max 12", F, "spec.maxReplicas", "eq", 12, select={"kind": "HorizontalPodAutoscaler"}),
  Q("cpu 65%", F, "spec.metrics[*].resource.target.averageUtilization", "eq", 65, select={"kind": "HorizontalPodAutoscaler"}), Q("metric is cpu", F, "spec.metrics[*].resource.name", "eq", "cpu", select={"kind": "HorizontalPodAutoscaler"}),
  Q("PDB policy/v1", F, "apiVersion", "eq", "policy/v1", select={"kind": "PodDisruptionBudget"}), Q("PDB minAvailable 2", F, "spec.minAvailable", "eq", 2, select={"kind": "PodDisruptionBudget"}),
  Q("PDB selector app=shop", F, "spec.selector.matchLabels.app", "eq", "shop", select={"kind": "PodDisruptionBudget"})]))

F = "netpol.yaml"
add(T("k8s-networkpolicy-isolate", "write", "k8s", "hard", """
Write `netpol.yaml` (namespace `shop`) with two NetworkPolicies implementing zero-trust for the `app: api` pods:
1) `default-deny` - selects ALL pods in the namespace, `policyTypes: [Ingress, Egress]`, no rules (deny everything).
2) `api-allow` - selects pods labelled `app: api`: ingress only from pods labelled `app: gateway` in the same namespace on TCP 8080; egress only to pods labelled `app: db` on TCP 5432 and DNS (UDP+TCP 53) to the namespace with label `kubernetes.io/metadata.name: kube-system`.""",
 {F: d(r"""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: shop
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
  namespace: shop
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: gateway
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: db
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
""")},
 [C("valid", "valid YAML", file=F), Q("default-deny selects everything", F, "spec.podSelector", "eq", {}, select={"kind": "NetworkPolicy", "metadata.name": "default-deny"}),
  Q("default-deny both types", F, "spec.policyTypes", "eq", ["Ingress", "Egress"], select={"kind": "NetworkPolicy", "metadata.name": "default-deny"}),
  Q("default-deny has no rules", F, "spec.ingress | spec.egress", "missing", select={"kind": "NetworkPolicy", "metadata.name": "default-deny"}),
  Q("both in namespace shop", F, "metadata.namespace", "eq", "shop", select={"kind": "NetworkPolicy"}),
  Q("api-allow selects api", F, "spec.podSelector.matchLabels.app", "eq", "api", select={"kind": "NetworkPolicy", "metadata.name": "api-allow"}),
  Q("ingress from gateway", F, "spec.ingress[*].from[*].podSelector.matchLabels.app", "eq", "gateway", select={"metadata.name": "api-allow"}),
  Q("ingress port 8080/TCP", F, "spec.ingress[*].ports[*].port", "eq", 8080, select={"metadata.name": "api-allow"}),
  Q("egress to db", F, "spec.egress[*].to[*].podSelector.matchLabels.app", "eq", "db", select={"metadata.name": "api-allow"}),
  Q("egress db port 5432", F, "spec.egress[*].ports[*].port", "in", [5432, 53], select={"metadata.name": "api-allow"}),
  Q("DNS to kube-system", F, "spec.egress[*].to[*].namespaceSelector.matchLabels", "contains", "kubernetes.io/metadata.name", select={"metadata.name": "api-allow"}, mode="any"),
  Q("DNS UDP and TCP", F, "spec.egress[*].ports[*].protocol", "eq", "UDP", select={"metadata.name": "api-allow"}, mode="any"),
  Q("api-allow policyTypes both", F, "spec.policyTypes", "eq", ["Ingress", "Egress"], select={"metadata.name": "api-allow"}),
  Q("no allow-all (empty from/to) rule", F, "spec.ingress[*].from", "len_gte", 1, select={"metadata.name": "api-allow"})]))

F = "ingress.yaml"
add(T("k8s-ingress-tls", "write", "k8s", "medium", """
Write `ingress.yaml`: an Ingress (`networking.k8s.io/v1`) `shop` in namespace `shop`, `ingressClassName: nginx`, TLS for host `shop.example.com` using Secret `shop-tls`, routing `/api` (pathType Prefix) to Service `api` port 80 (by number)
and `/` (pathType Prefix) to Service `web` port named `http`. Add the annotation `nginx.ingress.kubernetes.io/ssl-redirect: "true"` (string).""",
 {F: d(r"""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
  namespace: shop
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - shop.example.com
      secretName: shop-tls
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port:
                  name: http
""")},
 [C("valid", "valid YAML", file=F), Q("networking.k8s.io/v1", F, "apiVersion", "eq", "networking.k8s.io/v1", select={"kind": "Ingress"}), Q("class nginx", F, "spec.ingressClassName", "eq", "nginx", select={"kind": "Ingress"}),
  Q("tls secret", F, "spec.tls[*].secretName", "eq", "shop-tls", select={"kind": "Ingress"}), Q("tls host", F, "spec.tls[*].hosts", "contains", "shop.example.com", select={"kind": "Ingress"}),
  Q("rule host", F, "spec.rules[*].host", "eq", "shop.example.com", select={"kind": "Ingress"}), Q("pathType set on every path", F, "spec.rules[*].http.paths[*].pathType", "eq", "Prefix", select={"kind": "Ingress"}),
  Q("/api -> api:80", F, "spec.rules[*].http.paths[*].backend.service.port.number", "eq", 80, select={"kind": "Ingress"}),
  Q("/ -> web:http", F, "spec.rules[*].http.paths[*].backend.service.port.name", "eq", "http", select={"kind": "Ingress"}),
  Q("service names", F, "spec.rules[*].http.paths[*].backend.service.name", "in", ["api", "web"], select={"kind": "Ingress"}),
  Q("ssl-redirect annotation is the string 'true'", F, 'metadata.annotations."nginx.ingress.kubernetes.io/ssl-redirect"', "eq", "true", select={"kind": "Ingress"}),
  Q("annotation type str", F, 'metadata.annotations."nginx.ingress.kubernetes.io/ssl-redirect"', "type", "str", select={"kind": "Ingress"})]))

F = "rbac.yaml"
add(T("k8s-rbac-least-privilege", "write", "k8s", "medium", """
Write `rbac.yaml` (namespace `ops`): ServiceAccount `pod-reader`, a namespaced Role `pod-reader` that allows ONLY `get`, `list`, `watch` on `pods` and `pods/log` (core API group), and a RoleBinding `pod-reader` binding the Role to the ServiceAccount.
No wildcards anywhere, no ClusterRole/ClusterRoleBinding.""",
 {F: d(r"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pod-reader
  namespace: ops
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: ops
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader
  namespace: ops
subjects:
  - kind: ServiceAccount
    name: pod-reader
    namespace: ops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
""")},
 [C("valid", "valid YAML", file=F), C("docs", "SA, Role and RoleBinding present", file=F, min=3, max=3), Q("no ClusterRole", F, "kind", "ne", "ClusterRole", mode="all", select=None),
  Q("no ClusterRoleBinding", F, "kind", "ne", "ClusterRoleBinding", select=None), Q("verbs read-only", F, "rules[*].verbs[*]", "in", ["get", "list", "watch"], select={"kind": "Role"}),
  Q("verbs include all three", F, "rules[*].verbs", "contains", "watch", select={"kind": "Role"}, mode="any"), Q("resources pods + pods/log", F, "rules[*].resources[*]", "in", ["pods", "pods/log"], select={"kind": "Role"}),
  Q("pods/log present", F, "rules[*].resources", "contains", "pods/log", select={"kind": "Role"}, mode="any"), Q("core api group", F, "rules[*].apiGroups", "contains", "", select={"kind": "Role"}, mode="any"),
  Q("no wildcard", F, "rules[*].verbs[*] | rules[*].resources[*] | rules[*].apiGroups[*]", "ne", "*", select={"kind": "Role"}),
  Q("binding subject", F, "subjects[*].name", "eq", "pod-reader", select={"kind": "RoleBinding"}), Q("binding roleRef Role", F, "roleRef.kind", "eq", "Role", select={"kind": "RoleBinding"}),
  Q("everything in ns ops", F, "metadata.namespace", "eq", "ops", select=None)]))

F = "deployment.yaml"
add(T("k8s-zero-downtime-rollout", "write", "k8s", "hard", """
Write `deployment.yaml`: Deployment `checkout` (4 replicas, `ghcr.io/acme/checkout:6.0.1`, label `app: checkout`, port named `http` 8080) configured for zero-downtime rollouts:
`RollingUpdate` with `maxUnavailable: 0` and `maxSurge: 1`, `minReadySeconds: 10`, a startupProbe (GET /healthz, failureThreshold 30, periodSeconds 2), readinessProbe (GET /ready), livenessProbe (GET /healthz),
a `preStop` exec hook `sleep 10` so endpoints drain before SIGTERM, `terminationGracePeriodSeconds: 45`, and a `topologySpreadConstraints` entry spreading pods over `kubernetes.io/hostname` (maxSkew 1, `whenUnsatisfiable: ScheduleAnyway`)
selecting the app's pods. Add requests (cpu 200m, memory 256Mi) and a memory limit 512Mi.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  labels:
    app: checkout
spec:
  replicas: 4
  minReadySeconds: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: checkout
  template:
    metadata:
      labels:
        app: checkout
    spec:
      terminationGracePeriodSeconds: 45
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: checkout
      containers:
        - name: checkout
          image: ghcr.io/acme/checkout:6.0.1
          ports:
            - name: http
              containerPort: 8080
          startupProbe:
            httpGet:
              path: /healthz
              port: http
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            periodSeconds: 10
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "10"]
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              memory: 512Mi
""")},
 [C("valid", "valid YAML", file=F), C("k8s_selectors", "selectors", file=F), nolatest(F), C("k8s_probe_ports", "probe ports", file=F), *limits(F),
  Q("maxUnavailable 0", F, "spec.strategy.rollingUpdate.maxUnavailable", "eq", 0, select={"kind": "Deployment"}), Q("maxSurge 1", F, "spec.strategy.rollingUpdate.maxSurge", "eq", 1, select={"kind": "Deployment"}),
  Q("RollingUpdate", F, "spec.strategy.type", "eq", "RollingUpdate", select={"kind": "Deployment"}), Q("minReadySeconds", F, "spec.minReadySeconds", "eq", 10, select={"kind": "Deployment"}),
  ctr("startupProbe failureThreshold 30", F, "startupProbe.failureThreshold", "eq", 30), ctr("startupProbe period 2", F, "startupProbe.periodSeconds", "eq", 2),
  ctr("readiness /ready", F, "readinessProbe.httpGet.path", "eq", "/ready"), ctr("liveness /healthz", F, "livenessProbe.httpGet.path", "eq", "/healthz"),
  ctr("preStop sleep", F, "lifecycle.preStop.exec.command", "regex", r"sleep.*10"), pod("grace period 45", F, "spec.terminationGracePeriodSeconds", "eq", 45),
  pod("spread by hostname", F, "spec.topologySpreadConstraints[*].topologyKey", "eq", "kubernetes.io/hostname"), pod("maxSkew 1", F, "spec.topologySpreadConstraints[*].maxSkew", "eq", 1),
  pod("ScheduleAnyway", F, "spec.topologySpreadConstraints[*].whenUnsatisfiable", "eq", "ScheduleAnyway"), pod("spread selects app", F, "spec.topologySpreadConstraints[*].labelSelector.matchLabels.app", "eq", "checkout")]))

# -------------------------------------------------------------------- fix
F = "app.yaml"
add(T("k8s-fix-selector-mismatch", "fix", "k8s", "easy", """
`kubectl apply` is rejected: "selector does not match template labels". Even after that, the Service has no endpoints. Fix the manifests so the Deployment is valid and the Service routes to its pods.
Keep the names, image, replicas and ports; do not change the pod template labels `app: inventory` / `tier: backend` - fix the selectors.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory
spec:
  replicas: 2
  selector:
    matchLabels:
      app: inventory
      tier: backend
  template:
    metadata:
      labels:
        app: inventory
        tier: backend
    spec:
      containers:
        - name: inventory
          image: ghcr.io/acme/inventory:1.1.0
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: inventory
spec:
  selector:
    app: inventory
  ports:
    - port: 80
      targetPort: 8080
""")},
 [C("valid", "valid", file=F), C("k8s_selectors", "Deployment selector != template labels; Service selector matches nothing", file=F, bug=True),
  Q("template labels kept", F, "spec.template.metadata.labels.tier", "eq", "backend", select={"kind": "Deployment"}, keep=True), Q("template label app kept", F, "spec.template.metadata.labels.app", "eq", "inventory", select={"kind": "Deployment"}, keep=True),
  Q("replicas kept", F, "spec.replicas", "eq", 2, select={"kind": "Deployment"}, keep=True), Q("service port kept", F, "spec.ports[*].port", "eq", 80, select={"kind": "Service"}, keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inventory
spec:
  replicas: 2
  selector:
    matchLabels:
      app: inventory-service
  template:
    metadata:
      labels:
        app: inventory
        tier: backend
    spec:
      containers:
        - name: inventory
          image: ghcr.io/acme/inventory:1.1.0
          ports:
            - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: inventory
spec:
  selector:
    app: inventory-svc
  ports:
    - port: 80
      targetPort: 8080
""")}))

F = "deployment.yaml"
add(T("k8s-fix-latest-no-limits", "fix", "k8s", "easy", """
A noisy-neighbour incident: this Deployment has no resource requests/limits and pulls a floating tag. Fix it: pin the image to `ghcr.io/acme/crawler:2.3.4`, add cpu+memory requests (100m / 128Mi)
and a memory limit (256Mi), and set `imagePullPolicy: IfNotPresent`. Everything else stays.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: crawler
  template:
    metadata:
      labels:
        app: crawler
    spec:
      containers:
        - name: crawler
          image: ghcr.io/acme/crawler:2.3.4
          imagePullPolicy: IfNotPresent
          args: ["--workers", "4"]
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 256Mi
""")},
 [C("valid", "valid", file=F), nolatest(F, bug=True), ctr("memory request", F, "resources.requests.memory", "eq", "128Mi", bug=True), ctr("cpu request", F, "resources.requests.cpu", "eq", "100m", bug=True),
  ctr("memory limit", F, "resources.limits.memory", "eq", "256Mi", bug=True), ctr("IfNotPresent", F, "imagePullPolicy", "eq", "IfNotPresent", bug=True),
  ctr("args kept", F, "args", "eq", ["--workers", "4"], keep=True), Q("replicas kept", F, "spec.replicas", "eq", 2, select={"kind": "Deployment"}, keep=True), C("k8s_selectors", "selectors", file=F, keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: crawler
  template:
    metadata:
      labels:
        app: crawler
    spec:
      containers:
        - name: crawler
          image: ghcr.io/acme/crawler:latest
          args: ["--workers", "4"]
""")}))

add(T("k8s-fix-probes", "fix", "k8s", "medium", """
Rollouts of this Deployment hang: pods never become Ready and are restarted in a loop. The app listens on 8080 (named port `http`) and serves `/ready` and `/healthz`; it needs up to 60 s to start.
Fix the probes: readiness must hit `/ready`, liveness `/healthz`, both on the correct (named) port, and slow startup must not be killed by liveness - add a startupProbe (failureThreshold 30, periodSeconds 2) for `/healthz`.
Do not simply delete probes.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ledger
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ledger
  template:
    metadata:
      labels:
        app: ledger
    spec:
      containers:
        - name: ledger
          image: ghcr.io/acme/ledger:5.0.2
          ports:
            - name: http
              containerPort: 8080
          startupProbe:
            httpGet:
              path: /healthz
              port: http
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            periodSeconds: 10
""")},
 [C("valid", "valid", file=F), C("k8s_probe_ports", "probe ports not declared (80)", file=F, bug=True), ctr("readiness path /ready", F, "readinessProbe.httpGet.path", "eq", "/ready", bug=True),
  ctr("liveness path /healthz", F, "livenessProbe.httpGet.path", "eq", "/healthz", bug=True), ctr("startupProbe present", F, "startupProbe.httpGet.path", "eq", "/healthz", bug=True),
  ctr("startup budget >= 60s", F, "startupProbe.failureThreshold", "gte", 30), ctr("startup period", F, "startupProbe.periodSeconds", "gte", 2),
  ctr("probes on port 8080 or http", F, "readinessProbe.httpGet.port | livenessProbe.httpGet.port | startupProbe.httpGet.port", "in", ["http", 8080]), ctr("image kept", F, "image", "eq", "ghcr.io/acme/ledger:5.0.2", keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ledger
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ledger
  template:
    metadata:
      labels:
        app: ledger
    spec:
      containers:
        - name: ledger
          image: ghcr.io/acme/ledger:5.0.2
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /
              port: 80
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 3
            failureThreshold: 1
""")}))

add(T("k8s-fix-privileged-pod", "fix", "k8s", "medium", """
This DaemonSet-style agent was deployed as a Deployment with full host access ("it just worked"). The agent only needs to read its own config and open outbound connections.
Fix the pod spec: no privileged mode, no hostNetwork/hostPID/hostIPC, no root user, no hostPath volumes, no added capabilities (drop ALL), no privilege escalation, read-only root filesystem.
Keep image, name, and replicas.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent
  template:
    metadata:
      labels:
        app: agent
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
      containers:
        - name: agent
          image: ghcr.io/acme/agent:0.4.1
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
""")},
 [C("valid", "valid", file=F), ctr("privileged", F, "securityContext.privileged", "falsy", bug=True, allow_empty=True), pod("hostNetwork", F, "spec.hostNetwork", "falsy", bug=True, allow_empty=True),
  pod("hostPID", F, "spec.hostPID", "falsy", bug=True, allow_empty=True), pod("hostIPC", F, "spec.hostIPC", "falsy", allow_empty=True), pod("hostPath volumes", F, "spec.volumes[*].hostPath", "missing", bug=True),
  *[x for x in sec(F)], ctr("no added caps", F, "securityContext.capabilities.add", "missing", bug=True), ctr("image kept", F, "image", "eq", "ghcr.io/acme/agent:0.4.1", keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: agent
  template:
    metadata:
      labels:
        app: agent
    spec:
      hostNetwork: true
      hostPID: true
      containers:
        - name: agent
          image: ghcr.io/acme/agent:0.4.1
          securityContext:
            privileged: true
            runAsUser: 0
            capabilities:
              add: ["SYS_ADMIN", "NET_ADMIN"]
          volumeMounts:
            - name: host-root
              mountPath: /host
      volumes:
        - name: host-root
          hostPath:
            path: /
""")}))

add(T("k8s-fix-service-wiring", "fix", "k8s", "medium", """
Traffic through this Service fails with connection refused. The container listens on 9000 (named `grpc`) and 9100 (named `metrics`). Fix the Service wiring: `grpc` service port 443 must forward to the container's
`grpc` port, and `metrics` port 9100 to `metrics`; it must select the pods; and the Service must be named `payments`. Do not change the Deployment's containerPorts.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payments
  template:
    metadata:
      labels:
        app: payments
    spec:
      containers:
        - name: payments
          image: ghcr.io/acme/payments:3.3.0
          ports:
            - name: grpc
              containerPort: 9000
            - name: metrics
              containerPort: 9100
---
apiVersion: v1
kind: Service
metadata:
  name: payments
spec:
  selector:
    app: payments
  ports:
    - name: grpc
      port: 443
      targetPort: grpc
    - name: metrics
      port: 9100
      targetPort: metrics
""")},
 [C("valid", "valid", file=F), C("k8s_ports_match", "targetPort 8443 / 'prometheus' do not exist on the container", file=F, bug=True), C("k8s_selectors", "service selector matches", file=F, bug=True),
  Q("grpc 443", F, "spec.ports[*].port", "eq", 443, select={"kind": "Service"}, mode="any"), Q("metrics 9100", F, "spec.ports[*].port", "eq", 9100, select={"kind": "Service"}, mode="any"),
  Q("service name payments", F, "metadata.name", "eq", "payments", select={"kind": "Service"}), Q("container ports untouched", F, "spec.template.spec.containers[*].ports[*].containerPort", "in", [9000, 9100], select={"kind": "Deployment"}, keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payments
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payments
  template:
    metadata:
      labels:
        app: payments
    spec:
      containers:
        - name: payments
          image: ghcr.io/acme/payments:3.3.0
          ports:
            - name: grpc
              containerPort: 9000
            - name: metrics
              containerPort: 9100
---
apiVersion: v1
kind: Service
metadata:
  name: payments
spec:
  selector:
    app: payment
  ports:
    - name: grpc
      port: 443
      targetPort: 8443
    - name: metrics
      port: 9100
      targetPort: prometheus
""")}))

add(T("k8s-fix-dangling-refs", "fix", "k8s", "hard", """
The pod is stuck in `CreateContainerConfigError` / `FailedMount`. Find and fix every broken reference inside `app.yaml`: the ConfigMap is named `web-config` (do not rename it), the PVC is `web-data`, and volumeMounts must
name volumes that exist in the pod spec. Keep each volume mounted at the same path.""",
 {F: d(r"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-config
data:
  LOG_LEVEL: info
  nginx.conf: |
    events {}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: web-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
          envFrom:
            - configMapRef:
                name: web-config
          volumeMounts:
            - name: conf
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
            - name: data
              mountPath: /var/www
      volumes:
        - name: conf
          configMap:
            name: web-config
        - name: data
          persistentVolumeClaim:
            claimName: web-data
""")},
 [C("valid", "valid", file=F), C("k8s_refs_exist", "ConfigMap/PVC names wrong, volumeMount name mismatch", file=F, bug=True),
  ctr("mount /etc/nginx/nginx.conf kept", F, "volumeMounts[*].mountPath", "eq", "/etc/nginx/nginx.conf", mode="any", keep=True), ctr("mount /var/www kept", F, "volumeMounts[*].mountPath", "eq", "/var/www", mode="any", keep=True),
  Q("ConfigMap name kept", F, "metadata.name", "eq", "web-config", select={"kind": "ConfigMap"}, keep=True), Q("PVC name kept", F, "metadata.name", "eq", "web-data", select={"kind": "PersistentVolumeClaim"}, keep=True),
  C("k8s_selectors", "selectors", file=F, keep=True)],
 start={F: d(r"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-config
data:
  LOG_LEVEL: info
  nginx.conf: |
    events {}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: web-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
          envFrom:
            - configMapRef:
                name: web-configmap
          volumeMounts:
            - name: config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
            - name: data
              mountPath: /var/www
      volumes:
        - name: conf
          configMap:
            name: web-config
        - name: data
          persistentVolumeClaim:
            claimName: web-pvc
""")}))

add(T("k8s-fix-downtime-rollout", "fix", "k8s", "hard", """
Every release causes a short outage because the single replica is torn down before the new one is ready. Fix the Deployment for zero-downtime releases: at least 2 replicas,
`RollingUpdate` with `maxUnavailable: 0` and `maxSurge` 1, a readinessProbe on `/ready` (port 8080) so traffic only reaches ready pods, and `minReadySeconds: 5`.
Add a PodDisruptionBudget `gateway` (policy/v1, minAvailable 1) in the same file. Keep image, name and labels.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 2
  minReadySeconds: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
        - name: gateway
          image: ghcr.io/acme/gateway:1.9.0
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            periodSeconds: 3
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: gateway
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: gateway
""")},
 [C("valid", "valid", file=F), Q("replicas >= 2", F, "spec.replicas", "gte", 2, select={"kind": "Deployment"}, bug=True), Q("RollingUpdate", F, "spec.strategy.type", "eq", "RollingUpdate", select={"kind": "Deployment"}, bug=True),
  Q("maxUnavailable 0", F, "spec.strategy.rollingUpdate.maxUnavailable", "eq", 0, select={"kind": "Deployment"}, bug=True), Q("maxSurge >= 1", F, "spec.strategy.rollingUpdate.maxSurge", "gte", 1, select={"kind": "Deployment"}),
  ctr("readiness /ready:8080", F, "readinessProbe.httpGet.path", "eq", "/ready", bug=True), ctr("readiness port", F, "readinessProbe.httpGet.port", "eq", 8080), Q("minReadySeconds 5", F, "spec.minReadySeconds", "eq", 5, select={"kind": "Deployment"}, bug=True),
  Q("PDB policy/v1", F, "apiVersion", "eq", "policy/v1", select={"kind": "PodDisruptionBudget"}, bug=True), Q("PDB minAvailable 1", F, "spec.minAvailable", "eq", 1, select={"kind": "PodDisruptionBudget"}),
  Q("PDB selects gateway", F, "spec.selector.matchLabels.app", "eq", "gateway", select={"kind": "PodDisruptionBudget"}), C("k8s_selectors", "selectors", file=F, keep=True), ctr("image kept", F, "image", "eq", "ghcr.io/acme/gateway:1.9.0", keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: gateway
  template:
    metadata:
      labels:
        app: gateway
    spec:
      containers:
        - name: gateway
          image: ghcr.io/acme/gateway:1.9.0
          ports:
            - containerPort: 8080
""")}))

add(T("k8s-fix-env-secrets", "fix", "k8s", "medium", """
A scanner found credentials in this manifest. Replace the literal values with references: `DB_PASSWORD` from Secret `db-credentials` key `password`, `API_TOKEN` from Secret `api-credentials` key `token`
(both via `valueFrom.secretKeyRef`). Non-secret settings (`LOG_LEVEL`, `REGION`) stay as plain values. Do not create the Secrets in this file.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
        - name: worker
          image: ghcr.io/acme/worker:1.0.5
          env:
            - name: LOG_LEVEL
              value: info
            - name: REGION
              value: eu-west-1
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: api-credentials
                  key: token
""")},
 [C("valid", "valid", file=F), C("not_contains", "literal secrets in manifest", file=F, regex=r"hunter2|ghp_[A-Za-z0-9]+|value:\s*[\"']?(sup3r|tok_)", bug=True),
  ctr("DB_PASSWORD secretKeyRef", F, "env[*].valueFrom.secretKeyRef", "eq", {"name": "db-credentials", "key": "password"}, mode="any", bug=True),
  ctr("API_TOKEN secretKeyRef", F, "env[*].valueFrom.secretKeyRef", "eq", {"name": "api-credentials", "key": "token"}, mode="any", bug=True),
  ctr("LOG_LEVEL kept", F, "env[*]", "eq", {"name": "LOG_LEVEL", "value": "info"}, mode="any", keep=True), ctr("REGION kept", F, "env[*]", "eq", {"name": "REGION", "value": "eu-west-1"}, mode="any", keep=True),
  C("docs", "only the Deployment", file=F, max=1)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
        - name: worker
          image: ghcr.io/acme/worker:1.0.5
          env:
            - name: LOG_LEVEL
              value: info
            - name: REGION
              value: eu-west-1
            - name: DB_PASSWORD
              value: hunter2
            - name: API_TOKEN
              value: ghp_9aB8cD7eF6gH5iJ4
""")}))

add(T("k8s-fix-deprecated-apis", "fix", "k8s", "medium", """
After a cluster upgrade to Kubernetes 1.30, `kubectl apply` fails with "no matches for kind Deployment in version extensions/v1beta1" (and the same for the Ingress).
Migrate both objects to the current stable APIs (`apps/v1` with the required `spec.selector`; `networking.k8s.io/v1` Ingress with `pathType`, `service.name`/`service.port.number` and `ingressClassName: nginx` replacing the old annotation).
Behaviour must stay identical: host `blog.example.com`, path `/` to Service `blog` port 80.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blog
spec:
  replicas: 2
  selector:
    matchLabels:
      app: blog
  template:
    metadata:
      labels:
        app: blog
    spec:
      containers:
        - name: blog
          image: ghcr.io/acme/blog:2.2.0
          ports:
            - containerPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blog
spec:
  ingressClassName: nginx
  rules:
    - host: blog.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: blog
                port:
                  number: 80
""")},
 [C("valid", "valid", file=F), Q("Deployment apps/v1", F, "apiVersion", "eq", "apps/v1", select={"kind": "Deployment"}, bug=True), Q("Ingress v1", F, "apiVersion", "eq", "networking.k8s.io/v1", select={"kind": "Ingress"}, bug=True),
  C("k8s_selectors", "Deployment has selector", file=F, bug=True), Q("pathType", F, "spec.rules[*].http.paths[*].pathType", "in", ["Prefix", "Exact", "ImplementationSpecific"], select={"kind": "Ingress"}, bug=True),
  Q("service.name", F, "spec.rules[*].http.paths[*].backend.service.name", "eq", "blog", select={"kind": "Ingress"}, bug=True), Q("service.port.number", F, "spec.rules[*].http.paths[*].backend.service.port.number", "eq", 80, select={"kind": "Ingress"}, bug=True),
  Q("ingressClassName", F, "spec.ingressClassName", "eq", "nginx", select={"kind": "Ingress"}, bug=True), Q("old annotation removed", F, 'metadata.annotations."kubernetes.io/ingress.class"', "missing", select={"kind": "Ingress"}),
  Q("host kept", F, "spec.rules[*].host", "eq", "blog.example.com", select={"kind": "Ingress"}, keep=True)],
 start={F: d(r"""
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: blog
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: blog
    spec:
      containers:
        - name: blog
          image: ghcr.io/acme/blog:2.2.0
          ports:
            - containerPort: 80
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: blog
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: blog.example.com
      http:
        paths:
          - path: /
            backend:
              serviceName: blog
              servicePort: 80
""")}))

add(T("k8s-fix-structure", "fix", "k8s", "hard", """
This Deployment applies without errors but silently ignores the resource limits and the environment, and the probe never runs: several fields are indented under the wrong parent.
Repair the structure so that `resources`, `env`, `ports` and `readinessProbe` belong to the container (not the pod spec), and `volumes` belong to the pod spec. Keep all values.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl
spec:
  replicas: 1
  selector:
    matchLabels:
      app: etl
  template:
    metadata:
      labels:
        app: etl
    spec:
      containers:
        - name: etl
          image: ghcr.io/acme/etl:7.1.0
          ports:
            - containerPort: 9090
          env:
            - name: MODE
              value: batch
          resources:
            requests:
              cpu: 500m
              memory: 1Gi
            limits:
              memory: 2Gi
          readinessProbe:
            tcpSocket:
              port: 9090
          volumeMounts:
            - name: scratch
              mountPath: /scratch
      volumes:
        - name: scratch
          emptyDir: {}
""")},
 [C("valid", "valid", file=F), ctr("resources inside container", F, "resources.limits.memory", "eq", "2Gi", bug=True), ctr("requests inside container", F, "resources.requests.memory", "eq", "1Gi", bug=True),
  ctr("cpu request", F, "resources.requests.cpu", "eq", "500m"), ctr("env inside container", F, "env[*].name", "eq", "MODE", bug=True), ctr("ports inside container", F, "ports[*].containerPort", "eq", 9090, bug=True),
  ctr("probe inside container", F, "readinessProbe.tcpSocket.port", "eq", 9090, bug=True), pod("volumes in pod spec", F, "spec.volumes[*].name", "eq", "scratch", keep=True),
  Q("pod spec has no stray resources/env/ports", F, "spec.template.spec.resources | spec.template.spec.env | spec.template.spec.ports | spec.template.spec.readinessProbe", "missing", bug=True),
  ctr("volumeMount kept", F, "volumeMounts[*].mountPath", "eq", "/scratch", keep=True), C("k8s_refs_exist", "volumes resolve", file=F)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl
spec:
  replicas: 1
  selector:
    matchLabels:
      app: etl
  template:
    metadata:
      labels:
        app: etl
    spec:
      containers:
        - name: etl
          image: ghcr.io/acme/etl:7.1.0
          volumeMounts:
            - name: scratch
              mountPath: /scratch
      ports:
        - containerPort: 9090
      env:
        - name: MODE
          value: batch
      resources:
        requests:
          cpu: 500m
          memory: 1Gi
        limits:
          memory: 2Gi
      readinessProbe:
        tcpSocket:
          port: 9090
      volumes:
        - name: scratch
          emptyDir: {}
""")}))

# -------------------------------------------------------------------- harden
add(T("k8s-harden-deployment", "harden", "k8s", "hard", """
Harden this Deployment for a regulated cluster without changing the application: pinned image `ghcr.io/acme/portal:8.4.1`, cpu+memory requests (200m/256Mi) and memory limit (512Mi), liveness and readiness probes (HTTP, port 8080, `/healthz` and `/ready`),
pod-level `runAsNonRoot`, `runAsUser: 10001` and `seccompProfile: RuntimeDefault`, container `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, capabilities drop ALL, and no automounted service account token.
The app needs a writable /tmp: give it an emptyDir. Ports/labels/replicas unchanged.""",
 {F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portal
spec:
  replicas: 3
  selector:
    matchLabels:
      app: portal
  template:
    metadata:
      labels:
        app: portal
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: portal
          image: ghcr.io/acme/portal:8.4.1
          ports:
            - name: http
              containerPort: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: http
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              memory: 512Mi
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
""")},
 [C("valid", "valid", file=F), nolatest(F, bug=True), *[x for x in limits(F)], *probes(F), *sec(F), pod("seccomp", F, "spec.securityContext.seccompProfile.type", "eq", "RuntimeDefault"),
  pod("runAsUser 10001", F, "spec.securityContext.runAsUser", "eq", 10001), pod("no SA token", F, "spec.automountServiceAccountToken", "eq", False),
  ctr("writable /tmp via emptyDir", F, "volumeMounts[*].mountPath", "eq", "/tmp", mode="any"), pod("tmp emptyDir exists", F, "spec.volumes[*].emptyDir", "exists"), C("k8s_refs_exist", "volume refs", file=F),
  C("k8s_probe_ports", "probe ports", file=F), C("k8s_selectors", "selectors", file=F, keep=True), Q("replicas kept", F, "spec.replicas", "eq", 3, select={"kind": "Deployment"}, keep=True)],
 start={F: d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: portal
spec:
  replicas: 3
  selector:
    matchLabels:
      app: portal
  template:
    metadata:
      labels:
        app: portal
    spec:
      containers:
        - name: portal
          image: ghcr.io/acme/portal
          ports:
            - name: http
              containerPort: 8080
""")}))

add(T("k8s-harden-rbac", "harden", "k8s", "hard", """
This RBAC grants far too much: the CI service account is bound to cluster-admin and a wildcard ClusterRole. The deployer only needs to manage Deployments (get, list, watch, update, patch) and read ConfigMaps/Pods in
namespace `staging`. Replace the broad grants with a namespaced Role `deployer` (in `staging`) containing exactly that, bound via a RoleBinding to ServiceAccount `ci-deployer` (namespace `staging`).
Remove the ClusterRoleBinding and the wildcard ClusterRole entirely. No `*` anywhere.""",
 {"rbac.yaml": d(r"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-deployer
  namespace: staging
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: staging
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["configmaps", "pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer
  namespace: staging
subjects:
  - kind: ServiceAccount
    name: ci-deployer
    namespace: staging
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: deployer
""")},
 [C("valid", "valid", file="rbac.yaml"), Q("no ClusterRoleBinding", "rbac.yaml", "kind", "ne", "ClusterRoleBinding", bug=True), Q("no ClusterRole", "rbac.yaml", "kind", "ne", "ClusterRole", bug=True),
  Q("no wildcards", "rbac.yaml", "rules[*].verbs[*] | rules[*].resources[*] | rules[*].apiGroups[*]", "ne", "*", select={"kind": ["Role", "ClusterRole"]}, bug=True),
  Q("no cluster-admin", "rbac.yaml", "roleRef.name", "ne", "cluster-admin", select={"kind": ["RoleBinding", "ClusterRoleBinding"]}, bug=True),
  Q("Role deployer in staging", "rbac.yaml", "metadata.namespace", "eq", "staging", select={"kind": "Role", "metadata.name": "deployer"}),
  Q("deployments verbs", "rbac.yaml", "rules[*].verbs", "contains", "patch", select={"kind": "Role"}, mode="any"),
  Q("deployments resource in apps", "rbac.yaml", "rules[*].resources", "contains", "deployments", select={"kind": "Role"}, mode="any"),
  Q("no delete/create verbs", "rbac.yaml", "rules[*].verbs[*]", "in", ["get", "list", "watch", "update", "patch"], select={"kind": "Role"}),
  Q("reads configmaps and pods", "rbac.yaml", "rules[*].resources[*]", "in", ["deployments", "configmaps", "pods"], select={"kind": "Role"}),
  Q("binds to ci-deployer", "rbac.yaml", "subjects[*].name", "eq", "ci-deployer", select={"kind": "RoleBinding"}), Q("RoleBinding refs Role deployer", "rbac.yaml", "roleRef.name", "eq", "deployer", select={"kind": "RoleBinding"})],
 start={"rbac.yaml": d(r"""
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-deployer
  namespace: staging
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: deployer-everything
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ci-deployer-admin
subjects:
  - kind: ServiceAccount
    name: ci-deployer
    namespace: staging
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
""")}))

add(T("k8s-harden-namespace", "harden", "k8s", "hard", """
Write the hardened `namespace.yaml` for tenant namespace `team-a` (currently just a bare Namespace). It must enforce the *restricted* Pod Security Standard (labels `pod-security.kubernetes.io/enforce: restricted`, `.../enforce-version: latest`, and `.../warn: restricted`),
include a ResourceQuota `compute` (requests.cpu 8, requests.memory 16Gi, limits.memory 32Gi, pods "50") and a LimitRange `defaults` that gives containers a default memory request of 128Mi, default memory limit of 256Mi and default cpu request 100m.
All objects in namespace `team-a` (the Namespace object itself excluded).""",
 {"namespace.yaml": d(r"""
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute
  namespace: team-a
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.memory: 32Gi
    pods: "50"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: defaults
  namespace: team-a
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        memory: 256Mi
""")},
 [C("valid", "valid", file="namespace.yaml"), Q("PSS enforce restricted", "namespace.yaml", 'metadata.labels."pod-security.kubernetes.io/enforce"', "eq", "restricted", select={"kind": "Namespace"}, bug=True),
  Q("enforce-version", "namespace.yaml", 'metadata.labels."pod-security.kubernetes.io/enforce-version"', "eq", "latest", select={"kind": "Namespace"}, bug=True),
  Q("warn restricted", "namespace.yaml", 'metadata.labels."pod-security.kubernetes.io/warn"', "eq", "restricted", select={"kind": "Namespace"}),
  Q("quota requests.cpu", "namespace.yaml", 'spec.hard."requests.cpu"', "eq", 8, select={"kind": "ResourceQuota", "metadata.name": "compute"}, bug=True),
  Q("quota requests.memory", "namespace.yaml", 'spec.hard."requests.memory"', "qty_lte", "16Gi", select={"kind": "ResourceQuota"}), Q("quota limits.memory", "namespace.yaml", 'spec.hard."limits.memory"', "qty_lte", "32Gi", select={"kind": "ResourceQuota"}),
  Q("quota pods 50", "namespace.yaml", "spec.hard.pods", "eq", 50, select={"kind": "ResourceQuota"}),
  Q("limitrange default request memory", "namespace.yaml", "spec.limits[*].defaultRequest.memory", "eq", "128Mi", select={"kind": "LimitRange", "metadata.name": "defaults"}, bug=True),
  Q("limitrange default limit memory", "namespace.yaml", "spec.limits[*].default.memory", "eq", "256Mi", select={"kind": "LimitRange"}), Q("limitrange default cpu request", "namespace.yaml", "spec.limits[*].defaultRequest.cpu", "eq", "100m", select={"kind": "LimitRange"}),
  Q("limitrange type Container", "namespace.yaml", "spec.limits[*].type", "eq", "Container", select={"kind": "LimitRange"}),
  Q("quota in team-a", "namespace.yaml", "metadata.namespace", "eq", "team-a", select={"kind": ["ResourceQuota", "LimitRange"]})],
 start={"namespace.yaml": d(r"""
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
""")}))

# -------------------------------------------------------------------- convert
add(T("k8s-convert-compose", "convert", "k8s", "medium", """
Convert the compose service in `docker-compose.yml` into Kubernetes manifests in `app.yaml`: a Deployment `catalog` (replicas 2) and a Service `catalog` (ClusterIP, port 80 -> container port 5000).
Carry over image, env vars, command, restart behaviour (Deployments always restart), the healthcheck (as readiness + liveness probes on `/health`) and the `mem_limit` (as memory limit). Compose `ports: 5000` is the container port.""",
 {"app.yaml": d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog
  labels:
    app: catalog
spec:
  replicas: 2
  selector:
    matchLabels:
      app: catalog
  template:
    metadata:
      labels:
        app: catalog
    spec:
      containers:
        - name: catalog
          image: ghcr.io/acme/catalog:2.7.1
          command: ["python", "-m", "catalog", "--bind", "0.0.0.0:5000"]
          ports:
            - name: http
              containerPort: 5000
          env:
            - name: MODE
              value: production
            - name: CACHE_TTL
              value: "300"
          readinessProbe:
            httpGet:
              path: /health
              port: http
          livenessProbe:
            httpGet:
              path: /health
              port: http
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 256Mi
---
apiVersion: v1
kind: Service
metadata:
  name: catalog
spec:
  type: ClusterIP
  selector:
    app: catalog
  ports:
    - port: 80
      targetPort: http
""")},
 [C("valid", "valid", file="app.yaml"), C("k8s_selectors", "selectors", file="app.yaml"), C("k8s_ports_match", "ports", file="app.yaml"), nolatest("app.yaml"),
  Q("replicas 2", "app.yaml", "spec.replicas", "eq", 2, select={"kind": "Deployment"}), ctr("image", "app.yaml", "image", "eq", "ghcr.io/acme/catalog:2.7.1"),
  ctr("command", "app.yaml", "command | args", "regex", r"python.*-m.*catalog"), ctr("MODE env", "app.yaml", "env[*]", "eq", {"name": "MODE", "value": "production"}, mode="any"),
  ctr("CACHE_TTL env as string", "app.yaml", "env[*]", "eq", {"name": "CACHE_TTL", "value": "300"}, mode="any"),
  ctr("env values are strings", "app.yaml", "env[*].value", "type", "str"),
  ctr("readiness /health", "app.yaml", "readinessProbe.httpGet.path", "eq", "/health"), ctr("liveness /health", "app.yaml", "livenessProbe.httpGet.path", "eq", "/health"),
  ctr("memory limit 256Mi", "app.yaml", "resources.limits.memory", "qty_lte", "256Mi"), ctr("limit set", "app.yaml", "resources.limits.memory", "exists"),
  Q("service port 80", "app.yaml", "spec.ports[*].port", "eq", 80, select={"kind": "Service"})],
 start={"docker-compose.yml": d(r"""
services:
  catalog:
    image: ghcr.io/acme/catalog:2.7.1
    command: ["python", "-m", "catalog", "--bind", "0.0.0.0:5000"]
    environment:
      MODE: production
      CACHE_TTL: "300"
    ports:
      - "5000"
    restart: always
    mem_limit: 256m
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://127.0.0.1:5000/health"]
      interval: 10s
      timeout: 3s
      retries: 3
""")}))

add(T("k8s-convert-pod-to-deployment", "convert", "k8s", "easy", """
`pod.yaml` is a bare Pod that disappears when its node fails. Convert it to a Deployment in `deployment.yaml` (name `scraper`, 2 replicas) keeping the container spec (image, args, env, resources) intact.
The Deployment must have a proper selector matching the pod template labels.""",
 {"deployment.yaml": d(r"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraper
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scraper
  template:
    metadata:
      labels:
        app: scraper
    spec:
      containers:
        - name: scraper
          image: ghcr.io/acme/scraper:0.3.2
          args: ["--interval", "60"]
          env:
            - name: TARGET
              value: https://example.com
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              memory: 128Mi
""")},
 [C("valid", "valid", file="deployment.yaml"), Q("kind Deployment", "deployment.yaml", "apiVersion", "eq", "apps/v1", select={"kind": "Deployment"}), C("k8s_selectors", "selectors", file="deployment.yaml"),
  Q("replicas 2", "deployment.yaml", "spec.replicas", "eq", 2, select={"kind": "Deployment"}), ctr("image kept", "deployment.yaml", "image", "eq", "ghcr.io/acme/scraper:0.3.2"),
  ctr("args kept", "deployment.yaml", "args", "eq", ["--interval", "60"]), ctr("env kept", "deployment.yaml", "env[*]", "eq", {"name": "TARGET", "value": "https://example.com"}, mode="any"),
  ctr("resources kept", "deployment.yaml", "resources.limits.memory", "eq", "128Mi"), ctr("requests kept", "deployment.yaml", "resources.requests.cpu", "eq", "50m"),
  Q("no leftover Pod", "deployment.yaml", "kind", "ne", "Pod", select=None)],
 start={"pod.yaml": d(r"""
apiVersion: v1
kind: Pod
metadata:
  name: scraper
  labels:
    app: scraper
spec:
  containers:
    - name: scraper
      image: ghcr.io/acme/scraper:0.3.2
      args: ["--interval", "60"]
      env:
        - name: TARGET
          value: https://example.com
      resources:
        requests:
          cpu: 50m
          memory: 64Mi
        limits:
          memory: 128Mi
""")}))
