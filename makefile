# Makefile
.PHONY: help
help:
	@echo "Commands:"
	@echo "run-api                 : Launch api in dev mode."
	@echo "docker-build            : Build docker image."
	@echo "docker-run              : Launch docker image."
	@echo "install-dev             : setup dev mode in your IDE."
	@echo "tests                   : run tests."


.PHONY: docker-build
docker-build:
	docker build -f Dockerfile -t TBA .

.PHONY: docker-run
docker-run:
	docker run -it --rm --name NAME -p 8000:8000 TBA

.PHONY: install-dev
install-dev:
	python -m pip install -e ".[dev]" --no-cache-dir
	pre-commit install
	pre-commit autoupdate

# Tests
.PHONY: tests
tests:
	python -m pytest -v --cov

# Installation
.PHONY: install
install:
	python -m pip install -e . --no-cache-dir

.PHONY: build-project
build-project: install-dev
	hatch build
