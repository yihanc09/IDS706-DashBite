.PHONY: install test smoke-foundation simulator preprocess train infer dashboard run stop clean-data

SHELL := /bin/sh
LOG_DIR := .logs
PID_DIR := $(LOG_DIR)/pids
POLL_INTERVAL_SECONDS ?= 15

.ONESHELL:

install:
	python -m pip install -e .

test:
	python -m pytest

smoke-foundation:
	python -c "from pipeline.config import load_config; from pipeline.paths import ensure_data_dirs; print(load_config()); print(*ensure_data_dirs().values(), sep='\\n')"

simulator:
	python -m pipeline.simulator

preprocess:
	python -m pipeline.preprocess

train:
	python -m pipeline.train

infer:
	python -m pipeline.infer

dashboard:
	streamlit run dashboard/app.py --server.port 8501

run:
	mkdir -p "$(LOG_DIR)" "$(PID_DIR)"
	start_stage() { \
		name="$$1"; shift; \
		pid_file="$(PID_DIR)/$$name.pid"; \
		if [ -f "$$pid_file" ] && kill -0 "$$(cat "$$pid_file")" 2>/dev/null; then \
			echo "$$name already running (PID $$(cat "$$pid_file"))"; \
			return; \
		fi; \
		rm -f "$$pid_file"; \
		echo "Starting $$name"; \
		nohup env POLL_INTERVAL_SECONDS="$(POLL_INTERVAL_SECONDS)" "$$@" \
			> "$(LOG_DIR)/$$name.log" 2>&1 < /dev/null & \
		echo $$! > "$$pid_file"; \
	}; \
	start_stage simulator python -m pipeline.simulator; \
	start_stage preprocess python -m pipeline.preprocess; \
	start_stage train python -m pipeline.train --loop; \
	start_stage infer python -m pipeline.infer; \
	start_stage dashboard streamlit run dashboard/app.py --server.port 8501 --server.headless true; \
	echo "DashBite is running; logs: $(LOG_DIR), PIDs: $(PID_DIR)"

stop:
	if [ -d "$(PID_DIR)" ]; then \
		for pid_file in "$(PID_DIR)"/*.pid; do \
			[ -f "$$pid_file" ] || continue; \
			pid="$$(cat "$$pid_file")"; \
			case "$$pid" in ''|*[!0-9]*) echo "Ignoring invalid PID file $$pid_file";; *) \
				if kill -0 "$$pid" 2>/dev/null; then \
					echo "Stopping $$(basename "$$pid_file" .pid) (PID $$pid)"; \
					kill "$$pid" 2>/dev/null || true; \
				fi ;; \
			esac; \
			rm -f "$$pid_file"; \
		done; \
	fi
	@echo "DashBite stopped"

clean-data:
	rm -rf data/raw data/features data/models data/predictions data/quality
