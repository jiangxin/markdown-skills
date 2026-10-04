.DEFAULT_GOAL := help

SKILL_ROOT := $(abspath .)

.PHONY: help html ppt pdf serve test lint fmt fonts

help:
	@echo "Targets (run from skills/markdown-slides):"
	@echo "  make html    build HTML (set DOC= or a single type=slides dir)"
	@echo "  make ppt     build PPTX via scripts/build-pptx.js"
	@echo "  make pdf     export PDF via scripts/export-pdf.js"
	@echo "  make serve   serve build/ locally"
	@echo "  make fmt     format Python with ruff"
	@echo "  make lint    ruff + markdownlint-cli2"
	@echo "  make test    run unit tests"
	@echo "  make fonts   download Google Fonts into .cache (once per theme)"
	@echo "Pass DECK_ROOT to select a deck directory. The default is this skill."
	@echo "Pass DOC to select a document directory (build/<dir>/)."
	@echo "When DECK_ROOT is another deck, lint also checks that deck's README*.md and slides/*.md / example-slides/*.md."

fonts:
	python3 scripts/embed_fonts.py

html:
	DECK_ROOT="$(DECK_ROOT)" DOC="$(DOC)" python3 scripts/build-slides.py

ppt:
	DECK_ROOT="$(DECK_ROOT)" DOC="$(DOC)" node scripts/build-pptx.js

pdf:
	DECK_ROOT="$(DECK_ROOT)" DOC="$(DOC)" node scripts/export-pdf.js

serve:
	DECK_ROOT="$(DECK_ROOT)" DOC="$(DOC)" python3 scripts/serve.py

fmt:
	@command -v ruff >/dev/null || { echo "ruff is required: https://docs.astral.sh/ruff/" >&2; exit 1; }
	ruff format scripts tests templates/build.py

EXTRA_MD :=
ifneq ($(DECK_ROOT),)
ifneq ($(abspath $(DECK_ROOT)),$(SKILL_ROOT))
EXTRA_MD := $(wildcard $(DECK_ROOT)/README.md) $(wildcard $(DECK_ROOT)/README.zh.md) $(wildcard $(DECK_ROOT)/AGENTS.md) $(wildcard $(DECK_ROOT)/slides/*.md) $(wildcard $(DECK_ROOT)/example-slides/*.md)
endif
endif

lint:
	@command -v ruff >/dev/null || { echo "ruff is required: https://docs.astral.sh/ruff/" >&2; exit 1; }
	ruff check scripts tests templates/build.py
	ruff format --check scripts tests templates/build.py
	@if [ ! -d node_modules/markdownlint-cli2 ]; then \
		echo "run npm install in skills/markdown-slides (markdownlint-cli2)" >&2; \
		exit 1; \
	fi
	npx --no-install markdownlint-cli2 $(EXTRA_MD)

test:
	@if [ -d skills/markdown-slides/tests ]; then \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s skills/markdown-slides/tests; \
	else \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s tests; \
	fi
