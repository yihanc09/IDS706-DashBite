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
