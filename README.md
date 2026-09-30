# DashBite

DashBite is a file-based late-order machine learning demo. It simulates food-delivery orders, preprocesses raw data, trains a late-order prediction model, performs inference, and displays pipeline health through the Model Pulse dashboard.

Each pipeline stage runs as a separate process and communicates through filesystem artifacts under `data/`. The Makefile serves as the public interface for running and managing the application.

## Architecture

The DashBite pipeline follows this workflow:

```text
Simulator
   ↓
data/raw/
   ↓
Preprocessing
   ↓
data/features/
   ↓
Training
   ↓
data/models/
   ↓
Inference
   ↓
data/predictions/
   ↓
Model Pulse Dashboard
```

This filesystem-based architecture keeps the stages independent. Training publishes model checkpoints to disk, while inference consumes the latest available checkpoint. Model Pulse reads existing pipeline artifacts and does not own or modify pipeline logic.

## Local Development

Install the project:

```sh
make install
```

Individual stages can be started through the Makefile:

```sh
make simulator   # writes data/raw/
make preprocess  # writes data/features/
make train       # publishes data/models/
make infer       # writes data/predictions/
make dashboard   # reads data/ and opens Model Pulse
```

Long-lived stages can be run in separate terminals and stopped with `Ctrl+C`.

For the complete classroom stack, use the Makefile-managed background processes:

```sh
make run
tail -f .logs/simulator.log .logs/preprocess.log .logs/train.log .logs/infer.log
make stop
```

`make run` uses a 15-second default poll cadence, stores logs in `.logs/`, stores PIDs in `.logs/pids/`, and serves Model Pulse at `http://localhost:8501`.

For a faster demonstration, the polling interval can be overridden:

```sh
POLL_INTERVAL_SECONDS=1 make run
```

## Testing

Run the complete test suite locally with:

```sh
make test
```

The current test suite contains unit, regression, and integration coverage for the DashBite pipeline.

Final local verification:

```text
35 passed
```

The same test suite can also be executed inside the Docker environment:

```sh
make docker-test
```

Final containerized verification:

```text
35 passed
```

## Docker Workflow

DashBite can run as a containerized application using Docker Compose. The containerized version preserves the existing filesystem-based architecture and Makefile-managed processes.

Build the image:

```sh
make docker-build
```

Start DashBite:

```sh
make docker-up
docker compose ps
```

Model Pulse is available at:

```text
http://localhost:8501
```

The `dashbite` service becomes healthy when the Streamlit health endpoint responds successfully:

```text
http://127.0.0.1:8501/_stcore/health
```

The runtime and one-shot test service use the same Docker image, helping ensure that tests execute in the same environment as the application.

## Persistent Storage

Docker Compose uses a named `dashbite-data` volume mounted at:

```text
/app/data
```

This volume stores pipeline artifacts including raw data, processed features, model checkpoints, metrics, and predictions.

Inspect persisted artifacts with:

```sh
make docker-volume
```

Inspect runtime logs with:

```sh
docker compose logs --tail=50 dashbite
```

Stop the application while preserving the volume:

```sh
make docker-down
```

Recreating the `dashbite` container retains the artifacts stored under `/app/data`.

To remove both the containers and persisted pipeline data:

```sh
docker compose down -v
```

This is a destructive cleanup command and removes the named volume.

## Container-Readiness Improvements

The containerized version adds several improvements beyond simply packaging the application in a Docker image:

1. **Persistent data storage** — a Docker named volume preserves pipeline artifacts across container recreation.
2. **Health checking** — Docker Compose monitors the Streamlit health endpoint and reports when Model Pulse is ready.
3. **Containerized testing** — the existing pytest suite can run as a one-shot Compose service using the same image as the runtime.
4. **Graceful shutdown behavior** — managed processes receive `SIGTERM` and are given time to exit before a bounded fallback cleanup prevents orphaned pipeline processes.

These improvements make the application easier to reproduce, test, operate, and stop safely in a containerized environment.

## AI-Assisted Development Workflow

This repository was extended using a structured AI-assisted development workflow with three separate roles:

**Architect → Implementer → Reviewer**

### Architect

The Architect first inspected the existing DashBite repository without modifying the application implementation. It designed the containerization approach and documented the plan in `docs/plan.md` under:

```text
Stage 7 — Containerization and Persistent Storage
```

The plan defined the Docker architecture, persistent-storage strategy, containerized testing approach, healthcheck, documentation requirements, and manual smoke tests.

### Implementer

A separate AI-assisted implementation session then followed the architecture plan and added:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- Docker-related Makefile targets
- Docker documentation
- persistent named-volume storage
- a Model Pulse healthcheck
- containerized testing

The implementation preserved the existing pipeline, dashboard, and test architecture.

### Reviewer

A separate Reviewer session treated the implementation as an independent code review. It reran the local and containerized test suites, rebuilt and inspected the Docker environment, checked health and persistence behavior, and verified container recreation.

The review identified one shutdown issue: `make stop` sent `SIGTERM` without waiting for managed processes to exit. The shutdown logic was improved with bounded graceful waiting and a fallback cleanup to prevent orphaned processes.

Final verification confirmed:

```text
Local tests:          35 passed
Containerized tests:  35 passed
Docker build:         passed
Runtime healthcheck:  healthy
Persistent storage:   passed
Container recreation: passed
Graceful shutdown:    passed
```

## Repository Structure

```text
DashBite/
├── .github/             # CI configuration
├── dashboard/           # Model Pulse dashboard
├── docs/
│   └── plan.md          # Architecture and development plans
├── pipeline/            # Pipeline stages and shared logic
├── tests/               # Unit, regression, and integration tests
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── README.md
```

## Key Docker Commands

```sh
make docker-build       # Build the DashBite image
make docker-up          # Start the containerized application
make docker-test        # Run the test suite inside Docker
make docker-volume      # Inspect persistent artifacts
make docker-down        # Stop containers while preserving data
docker compose ps       # Inspect container and health status
docker compose logs -f dashbite
docker compose down -v  # Remove containers and persistent data
```