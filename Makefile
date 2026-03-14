.PHONY: help test test-coverage clean install install-dev format format-check lint check lint-fix pre-commit-install pre-commit-run ci-check

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Run tests
	pytest -v

test-coverage: ## Run tests with coverage
	pytest --cov=schoonmaker --cov-report=html

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov

install: ## Install this project's runtime deps
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

format: ## Format code with black (fix in place). Then run 'make lint' — black may leave lines >79 chars; flake8 E501 requires all lines ≤79.
	black schoonmaker/ tests/ --line-length=79

format-check: ## Check formatting with black (no fix, fails if invalid)
	black schoonmaker/ tests/ --line-length=79 --check

lint: ## Lint with flake8 (E501: max line length 79). Run after 'make format' to catch long comments/docstrings.
	flake8 schoonmaker/ tests/

check: format-check lint ## Run all checks (format check + lint, no auto-fix)

lint-fix: ## Auto-fix linting issues where possible (autopep8 then black so black wins)
	autopep8 --in-place --recursive --aggressive --aggressive schoonmaker/ tests/
	black schoonmaker/ tests/ --line-length=79

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

ci-check: pre-commit-run test ## Run all CI checks
