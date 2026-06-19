init:
	python3 -m pip install --user pylint black poetry pipenv bandit mypy flake8

venv:
	python3 -m venv venv

conda:
	conda create -n tweekz python=3.12 pip -y && \
	conda activate tweekz && conda install -c conda-forge pylint black poetry pipenv bandit mypy flake8 -y && \	
	pip install -r requirements.txt

install:
	pip install -r requirements.txt

lint:
	flake8 src/ --config=.flake8

lint-report:
	flake8 src/ --config=.flake8 --count --statistics

docstrings:
	interrogate src/ -v

test:
	pytest tests/ --cov=src --cov-report=term-missing -v

db-up:
	docker compose up -d

db-down:
	docker compose down

db-load:
	python -m src.db.cli --data-path data/anonymized

db-load-fast:
	python -m src.db.cli --data-path data/anonymized --skip-topics

ci: lint docstrings test

