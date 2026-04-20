# Local K8s Dev Setup — kind + Podman + Local Registry

## Context

The triage-scheduler README documents a Dockerfile and K8s manifests inline, but none exist as actual files. No `gunicorn` in `requirements.txt`, no `k8s/` directory. This phase materializes all deployment artifacts and adds a local kind cluster + container registry so the full build→push→deploy→verify flow can be tested without any hosted services. The app connects to a host-side Podman Postgres (not in-cluster).

Eventually this will deploy to a real dev K8s cluster, so we use Kustomize overlays from the start.

---

## Branch

```
git checkout -b infra/local-k8s-setup
```
(off `docs/readme-and-claude-init`)

---

## Decisions

| Choice | Decision | Rationale |
|--------|----------|-----------|
| K8s tool | **kind** | Upstream K8s, uses Podman, ~30s startup |
| Registry | **Local registry** container on `localhost:5001` | kind has native support; no auth needed |
| Container runtime | **Podman** (existing) | `KIND_EXPERIMENTAL_PROVIDER=podman` |
| Manifest structure | **Kustomize overlays** | User's team uses Kustomize; avoids migration later |
| Database | **Host Podman Postgres** | Simpler; app connects via host gateway |
| Scope | **Infra setup only** | Files + configs; manual step execution |

---

## Part 1: Dockerfile

Create `Dockerfile` at project root.

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV FLASK_APP=wsgi:app
EXPOSE 8080
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
```

Add `.dockerignore` to exclude dev artifacts:
```
.venv/
.git/
.env
__pycache__/
*.pyc
tests/
.pytest_cache/
.claude/
node_modules/
```

Add `gunicorn==21.2.0` to `requirements.txt`.

---

## Part 2: Kustomize layout

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── migrate-job.yaml
└── overlays/
    └── local/
        ├── kustomization.yaml       # patches image to localhost:5001
        ├── kind-cluster.yaml        # kind config (registry + port mapping)
        ├── kind-registry.sh         # creates registry container + kind cluster
        └── secrets.yaml             # dev secrets (plain text, gitignored in prod)
```

### `k8s/base/kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - ingress.yaml
```
(migrate-job not in default resources — applied manually before deploy)

### `k8s/base/deployment.yaml`
- 2 replicas
- Image: `triage-scheduler:latest` (base — overlay patches to registry)
- Env from Secret: `DATABASE_URL`, `SECRET_KEY`, `ADMIN_PASSWORD`
- `FLASK_ENV=production`
- containerPort 8080
- Liveness: `GET / :8080` every 30s
- Readiness: `GET / :8080` every 10s

### `k8s/base/service.yaml`
- ClusterIP, port 80 → targetPort 8080

### `k8s/base/ingress.yaml`
- nginx ingress class
- host: `triage.local`
- path `/` → service port 80

### `k8s/base/migrate-job.yaml`
- `restartPolicy: Never`
- Command: `flask db upgrade`
- Same env vars from Secret

### `k8s/overlays/local/kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
  - secrets.yaml
images:
  - name: triage-scheduler
    newName: localhost:5001/triage-scheduler
    newTag: latest
```

### `k8s/overlays/local/secrets.yaml`
Dev-only Secret with base64-encoded values:
- `DATABASE_URL`: `postgresql://triage:triage@host.docker.internal:5432/triage_scheduler_dev`
  (kind maps `host.docker.internal` → host network where Podman Postgres runs)
- `SECRET_KEY`: `local-dev-key`
- `ADMIN_PASSWORD`: `admin`

### `k8s/overlays/local/kind-cluster.yaml`
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
  - |-
    [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:5001"]
      endpoint = ["http://kind-registry:5001"]
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
        protocol: TCP
```
NodePort 30080 mapped to host 8080 so the app is reachable at `localhost:8080`.

### `k8s/overlays/local/kind-registry.sh`
Shell script that:
1. Creates a registry container (`kind-registry` on port 5001) via Podman if not running
2. Creates the kind cluster with `kind-cluster.yaml` config using Podman provider
3. Connects registry container to kind network
4. Applies the configmap to tell kind about the registry

---

## Part 3: Host connectivity

For the app in kind to reach host Podman Postgres:
- `DATABASE_URL` uses `host.docker.internal` — kind supports this on macOS
- Podman Postgres must bind to `0.0.0.0:5432` (the existing `podman run` command from the README already does `-p 5432:5432`)

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `Dockerfile` | **Create** |
| `.dockerignore` | **Create** |
| `requirements.txt` | **Modify** — add `gunicorn==21.2.0` |
| `k8s/base/kustomization.yaml` | **Create** |
| `k8s/base/deployment.yaml` | **Create** |
| `k8s/base/service.yaml` | **Create** |
| `k8s/base/ingress.yaml` | **Create** |
| `k8s/base/migrate-job.yaml` | **Create** |
| `k8s/overlays/local/kustomization.yaml` | **Create** |
| `k8s/overlays/local/secrets.yaml` | **Create** |
| `k8s/overlays/local/kind-cluster.yaml` | **Create** |
| `k8s/overlays/local/kind-registry.sh` | **Create** |

---

## Reference: Deployment Manifests (from README)

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=wsgi:app
EXPOSE 8080
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
```

### Secrets (imperative — for one-off/production use)

```bash
kubectl create secret generic triage-scheduler-secrets \
  --from-literal=DATABASE_URL="postgresql://user:pass@postgres-host/triage_scheduler" \
  --from-literal=SECRET_KEY="your-secret-key" \
  --from-literal=ADMIN_PASSWORD="your-admin-password"
```

### Deployment + Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: triage-scheduler
spec:
  replicas: 2
  selector:
    matchLabels:
      app: triage-scheduler
  template:
    metadata:
      labels:
        app: triage-scheduler
    spec:
      containers:
        - name: triage-scheduler
          image: your-registry/triage-scheduler:latest
          ports:
            - containerPort: 8080
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: triage-scheduler-secrets
                  key: DATABASE_URL
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: triage-scheduler-secrets
                  key: SECRET_KEY
            - name: ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: triage-scheduler-secrets
                  key: ADMIN_PASSWORD
            - name: FLASK_ENV
              value: production
---
apiVersion: v1
kind: Service
metadata:
  name: triage-scheduler
spec:
  selector:
    app: triage-scheduler
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

### Migration Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: triage-scheduler-migrate
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          image: your-registry/triage-scheduler:latest
          command: ["flask", "db", "upgrade"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: triage-scheduler-secrets
                  key: DATABASE_URL
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: triage-scheduler-secrets
                  key: SECRET_KEY
```

### Seed (one-shot)

```bash
kubectl run seed --rm -it \
  --image=your-registry/triage-scheduler:latest \
  --restart=Never \
  --env="DATABASE_URL=..." \
  --env="SECRET_KEY=..." \
  -- flask seed-db
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: triage-scheduler
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
    - host: triage.your-domain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: triage-scheduler
                port:
                  number: 80
```

---

## Manual Verification Steps

After implementation, the user runs these manually:

```bash
# 1. Install tools
brew install kind kubectl

# 2. Start Podman Postgres (if not running)
podman run -d --name triage-postgres \
  -e POSTGRES_USER=triage -e POSTGRES_PASSWORD=triage \
  -e POSTGRES_DB=triage_scheduler_dev \
  -p 5432:5432 postgres:16

# 3. Create kind cluster + local registry
bash k8s/overlays/local/kind-registry.sh

# 4. Build and push image
podman build -t localhost:5001/triage-scheduler:latest .
podman push localhost:5001/triage-scheduler:latest

# 5. Apply secrets + run migration
kubectl apply -k k8s/overlays/local/
kubectl apply -f k8s/base/migrate-job.yaml
kubectl wait --for=condition=complete job/triage-scheduler-migrate --timeout=60s

# 6. Seed (one-shot)
kubectl run seed --rm -it --restart=Never \
  --image=localhost:5001/triage-scheduler:latest \
  --env="DATABASE_URL=postgresql://triage:triage@host.docker.internal:5432/triage_scheduler_dev" \
  --env="SECRET_KEY=local-dev-key" \
  -- flask seed-db

# 7. Verify
kubectl get pods
kubectl port-forward svc/triage-scheduler 8080:80
# Visit http://localhost:8080

# 8. Teardown
kind delete cluster --name triage-scheduler
podman stop kind-registry && podman rm kind-registry
```
