BIN = .venv/bin

install:
	python3 -m venv .venv
	$(BIN)/pip install -e ".[dev]"
	$(BIN)/pre-commit install

lint:
	$(BIN)/ruff check .
	$(BIN)/mypy src

format:
	$(BIN)/black .
	$(BIN)/ruff check --fix .

test:
	$(BIN)/pytest tests/ -v

demo:
	$(BIN)/python examples/demo.py
