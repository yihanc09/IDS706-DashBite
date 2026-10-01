# DashBite

DashBite is a file-based late-order machine learning demo. It simulates food-delivery orders, preprocesses raw data, trains a late-order prediction model, performs inference, and displays pipeline health through the Model Pulse dashboard.

Each pipeline stage runs as a separate process and communicates through filesystem artifacts under `data/`. The Makefile serves as the public interface for running and managing the application.

## Project Architecture

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

The final implementation focuses on:
- Docker containerization
- Docker Compose orchestration
- persistent pipeline storage
- application health checking
- containerized testing
- reproducible setup and runtime commands
- safe process management and shutdown behavior

## Installation

### Local setup

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

1. **Persistent data storage** 

The primary container-readiness improvement is a Docker named volume mounted at:

```sh
/app/data
```

DashBite's raw data, features, models, predictions, and other pipeline artifacts therefore survive normal container recreation.

This improvement fits the existing architecture because data/ was already the shared boundary between pipeline stages. I chose persistence at this boundary rather than introducing a new database or storage service.

2. **Health checking** 

Docker Compose checks the Model Pulse Streamlit health endpoint:

```sh
/_stcore/health
```

This distinguishes a container that is merely running from an application that is actually ready to serve the dashboard.

3. **Containerized testing** 

The existing pytest suite can run through a one-shot Compose test service using the containerized application environment.

4. **Graceful shutdown behavior** 

The container workflow preserves the application's existing process ownership and provides explicit lifecycle commands so that managed processes can be stopped cleanly without leaving unnecessary background processes.

These improvements make the application easier to reproduce, test, operate, and stop safely in a containerized environment.

## Manual Smoke Test

After completing and reviewing the Builder implementation, I manually tested the project before beginning the Tester stage.

I followed the documented setup and container workflow rather than relying only on the Builder's reported results.

I manually checked:

- the documented installation/setup commands
- the local test suite
- the Docker image build
- the containerized test suite
- Docker Compose startup
- container health status
- Model Pulse in a web browser
- creation of pipeline artifacts
- persistent storage across container recreation
- container shutdown behavior

## Result 

```sh
Local tests:             35 passed
Docker image build:      passed
Containerized tests:     35 passed
Compose runtime:         healthy
Model Pulse dashboard:   accessible at localhost:8501
Pipeline artifacts:      produced successfully
Volume persistence:      verified across container recreation
Shutdown:                verified
```

## AI-Assisted Development Workflow

This repository was extended using a structured AI-assisted development workflow with three separate roles:

**Architect → Builder → Tester**

The complete visible conversations are preserved under:

docs/transcripts/
├── yc570_architect.txt
├── yc570_builder.txt
└── yc570_tester.txt

### Architect

The Architect first inspected the existing DashBite repository without modifying the application implementation. It designed the containerization approach and documented the plan in `docs/plan.md` under:

```text
Stage 7 — Containerization and Persistent Storage
```

Its responsibilities included identifying:

- project and containerization requirements
- proposed changes
- important files
- architectural boundaries
- risks and design concerns
- automated testing strategy
- manual verification steps

I reviewed the Architect's plan before implementation rather than accepting its first response automatically.

One correction I requested was to make **persistent storage through a Docker named volume the primary container-readiness improvement**. This matched DashBite's existing filesystem architecture better than adding unnecessary infrastructure.

I also verified that the new containerization stage appeared in the correct chronological position after the existing stages in `docs/plan.md`.

### Builder

A separate AI-assisted implementation session then followed the architecture plan. Its responsibilities included:

- creating the Docker configuration
- creating the Compose configuration
- implementing persistent storage
- implementing the healthcheck
- supporting containerized testing
- updating the Makefile where necessary
- updating project documentation
- running automated implementation checks
- explaining important implementation decisions

The implementation preserved the existing pipeline, dashboard, and test architecture. I reviewed the Builder's generated files and changes before proceeding to the manual smoke test.

### Tester

After I completed the manual smoke test, a separate Reviewer session treated the implementation as an independent code review. It reran the local and containerized test suites, rebuilt and inspected the Docker environment, checked health and persistence behavior, and verified container recreation. The Tester:

- compared the implementation against `docs/plan.md`
- inspected and/or ran the test suite
- checked typical and meaningful edge-case behavior
- verified the documented setup instructions
- reviewed Docker and Compose behavior
- identified incomplete or incorrect work
- recommended corrections where necessary

The test identified one shutdown issue: `make stop` sent `SIGTERM` without waiting for managed processes to exit. The shutdown logic was improved with bounded graceful waiting and a fallback cleanup to prevent orphaned processes.

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

## AI Recommendations and My Judgment

The AI agents were used to support development, but their recommendations were not treated as automatically correct.

I accepted the Architect's recommendation to use a **Docker named volume for persistent pipeline storage**. This was appropriate because DashBite already uses filesystem artifacts as the interface between its pipeline stages. Mounting `/app/data` to persistent Docker storage improves container readiness while preserving the existing architecture. I also accepted the healthcheck design because checking the Model Pulse health endpoint provides a more meaningful readiness signal than simply checking whether the container process exists. 

I did not accept the Architect plan without review. I specifically refined the plan so that persistent storage was explicitly the primary container-readiness improvement, with health checking and other container features serving as supporting improvements. This made the implementation goal more focused and aligned it with DashBite's existing file-based design. I also checked the organization of `docs/plan.md` and required Stage 7 to remain chronologically after Stages 1–6.

I independently verified the final result rather than relying solely on AI-generated summaries.

My verification included:

1. Reviewing the Architect's plan before implementation.
2. Reviewing the Builder's generated files and implementation decisions.
3. Running the documented local test command.
4. Building the Docker image myself.
5. Running the pytest suite inside Docker.
6. Starting the application with Docker Compose.
7. Inspecting the Compose health status.
8. Opening Model Pulse in a browser.
9. Inspecting generated pipeline artifacts.
10. Verifying that artifacts survived container recreation.
11. Testing application/container shutdown.
12. Reviewing the Tester recommendations before accepting any corrections.
13. Rerunning relevant checks after final corrections.

### Final Verification

```text
Local tests:             35 passed
Containerized tests:     35 passed
Docker build:            passed
Compose configuration:   valid
Runtime healthcheck:     healthy
Model Pulse:             accessible
Pipeline output:         verified
Persistent storage:      verified
Shutdown behavior:       verified
```

## Repository Structure

```text
DashBite/
├── .github/                 # CI configuration
├── dashboard/               # Model Pulse dashboard
├── data/                    # Local pipeline data
├── docs/
│   ├── plan.md              # Architect implementation plan
│   └── transcripts/
│       ├── yc570_architect.txt
│       ├── yc570_builder.txt
│       └── yc570_tester.txt
├── pipeline/                # ML pipeline stages and shared logic
├── tests/                   # Automated tests
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