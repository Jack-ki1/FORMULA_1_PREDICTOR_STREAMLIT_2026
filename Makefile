.PHONY: install test lint format migrate-db dashboard predict quality

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/f1_predictor --cov-fail-under=80

lint:
	ruff check src/ tests/
	mypy src/f1_predictor/

format:
	ruff format src/ tests/

migrate-db:
	python main.py migrate-db

dashboard:
	python -m streamlit run app.py

predict:
	python main.py predict --race monaco --sims 10000

quality:
	python main.py quality-check
