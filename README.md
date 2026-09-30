# DashBite

DashBite is a file-based late-order ML demo. Each stage is a separate process
and the Makefile is the public interface:

```sh
make install
make simulator   # writes data/raw/
make preprocess  # writes data/features/
make train       # publishes data/models/
make infer       # writes data/predictions/
make dashboard   # reads data/ and opens Model Pulse
```

Run the long-lived stages in separate terminals and stop them with `Ctrl+C`.
Training publishes a checkpoint; inference and Model Pulse consume artifacts
already on disk and do not need training to remain running.

For the complete durable classroom stack, use the Makefile-managed background
jobs:

```sh
make run
tail -f .logs/simulator.log .logs/preprocess.log .logs/train.log .logs/infer.log
make stop
```

`make run` uses a 15-second default poll cadence, keeps logs in `.logs/`, PIDs
in `.logs/pids/`, and serves Model Pulse at
<http://localhost:8501>. Override the cadence for a faster demo with, for
example, `POLL_INTERVAL_SECONDS=1 make run`.

## Docker workflow

The Compose runtime uses the same Makefile-managed processes and filesystem
handoffs as the local demo. It exposes Model Pulse at
<http://localhost:8501> and stores all pipeline artifacts in the named
`dashbite-data` volume mounted at `/app/data`.

Build and start the runtime:

```sh
make docker-build
make docker-up
docker compose ps
```

The `dashbite` service is healthy when its Streamlit endpoint at
`http://127.0.0.1:8501/_stcore/health` responds successfully. Run the existing
pytest suite in the same image with the one-shot test service:

```sh
make docker-test
```

Inspect persisted artifacts and service logs with:

```sh
make docker-volume
docker compose logs --tail=50 dashbite
```

Stop the services while preserving the named volume:

```sh
make docker-down
```

Recreating the `dashbite` container without removing the volume preserves
files under `/app/data`. To remove the persisted pipeline artifacts as well,
use the explicit destructive cleanup command:

```sh
docker compose down -v
```
