.PHONY: run fmt
run:
	docker compose up --build

fmt:
	python -m pip install -q ruff && ruff format src
