.DEFAULT_GOAL := help

.PHONY: help html ppt pdf serve test

help:
	@echo "Targets (run from skills/markdown-slides):"
	@echo "  make html    build HTML via scripts/build-slides.py"
	@echo "  make ppt     build PPTX via scripts/build-pptx.js"
	@echo "  make pdf     export PDF via scripts/export-pdf.js"
	@echo "  make serve   serve the deck locally"
	@echo "  make test    run unit tests"
	@echo "Pass DECK_ROOT to select a deck directory. The default is this skill."

html:
	DECK_ROOT="$(DECK_ROOT)" python3 scripts/build-slides.py

ppt:
	DECK_ROOT="$(DECK_ROOT)" node scripts/build-pptx.js

pdf:
	DECK_ROOT="$(DECK_ROOT)" node scripts/export-pdf.js

serve:
	DECK_ROOT="$(DECK_ROOT)" python3 scripts/serve.py

test:
	@if [ -d skills/markdown-slides/tests ]; then \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s skills/markdown-slides/tests; \
	else \
		DECK_ROOT="$(DECK_ROOT)" python3 -m unittest discover -s tests; \
	fi
