PYTHON ?= .venv/bin/python
BOOTSTRAP_PYTHON ?= python3
DATAHUB_GMS ?= http://localhost:8080

.PHONY: install run quickstart graph fixture demo demo-generic test clean

install:
	$(BOOTSTRAP_PYTHON) -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt

run:
	$(PYTHON) -m streamlit run app.py

quickstart:
	datahub docker quickstart

## Charge les jeux officiels du hackathon et fait tourner la Sentinelle dessus.
demo-generic:
	datahub datapack load nyc-taxi
	python agents/sentinelle.py --server $(DATAHUB_GMS) --platform postgres --apply

## Construit le graphe agricole dans DataHub.
graph:
	$(PYTHON) catalog/build_graph.py --server $(DATAHUB_GMS) --token $$DATAHUB_TOKEN

## Fige le graphe pour la demo hors ligne (aucun serveur requis).
fixture:
	$(PYTHON) catalog/build_fixture.py --output fixtures/graph.json

## Demo agricole : detection, cascade sur le lineage, rapport d'impact.
demo: fixture
	$(PYTHON) -m streamlit run app.py --server.headless true

test:
	$(PYTHON) -m pytest -q

clean:
	find reports -type f -name '*.json' -delete
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
