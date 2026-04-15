# Triage Scheduler

A weekly triage rotation tool for platform teams. Assigns team members to triage duty across multiple apps using a fair, label-rotating round-robin algorithm with vacation hold support.

## Features

- **Fair rotation** — label-rotating round-robin ensures every member covers every app equally over a full cycle
- **Vacation holds** — pointer holds at a vacationing member's position; they get priority on return
- **Cool-down** — no member is assigned two consecutive weeks
- **Public calendar** — read-only macOS-style monthly calendar at `/`
- **Admin panel** — roster, app, availability, and schedule management at `/manage`

---

## Tech Stack

- **Python 3.10+** / Flask 3.x
- **PostgreSQL** (dev/prod) · SQLite in-memory (tests)
- **SQLAlchemy 2** + Flask-Migrate (Alembic)
- **Bootstrap 5** via CDN

---

## Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL (or Podman/Docker for a containerised DB)
- `pip`

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/rraffi/triage-scheduler.git
cd triage-scheduler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://localhost/triage_scheduler_dev
SECRET_KEY=change-me
ADMIN_PASSWORD=change-me
```

### 3. Start a local PostgreSQL instance

**With Podman (rootless):**

```bash
podman run -d \
  --name triage-postgres \
  -e POSTGRES_USER=triage \
  -e POSTGRES_PASSWORD=triage \
  -e POSTGRES_DB=triage_scheduler_dev \
  -p 5432:5432 \
  postgres:16
```

Update `DATABASE_URL` accordingly:

```env
DATABASE_URL=postgresql://triage:triage@localhost/triage_scheduler_dev
```

### 4. Run migrations

```bash
flask db upgrade
```

### 5. Seed the database

Creates the Platform Team, default apps, and sample members:

```bash
flask seed-db
```

### 6. Run the development server

```bash
flask run --port 5001
```

Visit `http://localhost:5001` for the public calendar, or `http://localhost:5001/manage` for the admin panel.

**Admin credentials:** use the `ADMIN_PASSWORD` value from your `.env`.

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `flask seed-db` | Create team, apps, and sample members |
| `flask schedule-week` | Run and persist one week of scheduling |
| `flask schedule-preview` | Dry-run preview (no DB write) |
| `flask db upgrade` | Apply pending migrations |

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database — no Postgres required.

---

## Project Structure

```
triage-scheduler/
├── src/                        # Pure scheduling algorithm (no Flask deps)
│   ├── models.py               # Domain dataclasses
│   └── scheduler.py            # Label-rotating round-robin algorithm
├── app/                        # Flask web layer
│   ├── admin/                  # Admin blueprint (/manage)
│   ├── main/                   # Public blueprint (/)
│   ├── db_models/              # SQLAlchemy ORM models
│   ├── services/               # Service layer (scheduler_service.py)
│   └── templates/              # Jinja2 templates (Bootstrap 5)
├── migrations/                 # Alembic migration scripts
├── tests/                      # pytest test suite
├── config.py                   # Dev / Test / Prod config classes
├── wsgi.py                     # WSGI entry point
└── .env.example                # Environment variable template
```

---

## Kubernetes Deployment

### Container image

Create a `Dockerfile` at the project root:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=wsgi:app
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8080", "--workers", "2"]
```

Add `gunicorn` to `requirements.txt` for production:

```bash
echo "gunicorn==21.2.0" >> requirements.txt
```

Build and push:

```bash
docker build -t your-registry/triage-scheduler:latest .
docker push your-registry/triage-scheduler:latest
```

### Secrets

Create a Kubernetes Secret for sensitive values:

```bash
kubectl create secret generic triage-scheduler-secrets \
  --from-literal=DATABASE_URL="postgresql://user:pass@postgres-host/triage_scheduler" \
  --from-literal=SECRET_KEY="your-secret-key" \
  --from-literal=ADMIN_PASSWORD="your-admin-password"
```

### Deployment manifest

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

### Database migrations on deploy

Run migrations as a Kubernetes Job before the Deployment rolls out:

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

### Seed on first deploy

Run once after the migration job:

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

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | `dev-secret-key` | Flask session signing key |
| `ADMIN_PASSWORD` | Yes | `admin` | Password for `/manage` admin panel |
| `FLASK_ENV` | No | `development` | `development` or `production` |
