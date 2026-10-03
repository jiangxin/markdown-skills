.DEFAULT_GOAL := help

SKILL_ROOT := $(abspath .)

.PHONY: help html pdf serve test lint fmt

help:
	@echo "Targets (run from skills/markdown-pages):"
	@echo "  make html    build HTML (set SLIDES= or PAGES= or a single type=pages dir)"
	@echo "  make pdf     export PDF from the one-file HTML"
	@echo "  make serve   serve is not this skill; use the deck trampoline"
	@echo "  make fmt     format Python with ruff"
	@echo "  make lint    ruff + markdownlint-cli2"
	@echo "  make test    run unit tests"
	@echo "Pass DECK_ROOT to select a deck directory. The default is this skill."
	@echo "Pass SLIDES or PAGES to select a book directory (build/<dir>/)."
	@echo "When DECK_ROOT is another deck, lint also checks that deck's README*.md and pages/*.md."

html:
	DECK_ROOT="$(DECK_ROOT)" SLIDES="$(SLIDES)" python3 scripts/build-pages.py

pdf:
	@echo "pdf: not implemented yet (later steps add PDF export)"

serve:
	@echo "serve: use the deck-root trampoline (make serve); this skill does not host build/"

RUFF_PATHS := tests
ifneq ($(wildcard scripts),)
RUFF_PATHS += scripts
endif

fmt:
	@command -v ruff >/dev/null || { echo "ruff is required: https://docs.astral.sh/ruff/" >&2; exit 1; }
	ruff format $(RUFF_PATHS)

EXTRA_MD :=
ifneq ($(DECK_ROOT),)
ifneq ($(abspath $(DECK_ROOT)),$(SKILL_ROOT))
EXTRA_MD := $(wildcard $(DECK_ROOT)/README.md) $(wildcard $(DECK_ROOT)/README.zh.md) $(wildcard $(DECK_ROOT)/AGENTS.md) $(wildcard $(DECK_ROOT)/pages/*.md)
endif
endif

lint:
	@command -v ruff >/dev/null || { echo "ruff is required: https://docs.astral.sh/ruff/" >&2; exit 1; }
	ruff check $(RUFF_PATHS)
	ruff format --check $(RUFF_PATHS)
	@if [ ! -d node_modules/markdownlint-cli2 ]; then \
		echo "run npm install in skills/markdown-pages (markdownlint-cli2)" >&2; \
		exit 1; \
	fi
	npx --no-install markdownlint-cli2 $(EXTRA_MD)

test:
	@if [ -d skills/markdown-pages/tests ]; then \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s skills/markdown-pages/tests; \
	else \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s tests; \
	fi
