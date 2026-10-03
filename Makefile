# Trampoline: run the markdown-slides engine without copying scripts/.
# Copy this file to the deck root as Makefile.

.DEFAULT_GOAL := help

DECK_ROOT := $(abspath .)

# SKILL, else MARKDOWN_SLIDES_HOME, else [build] skill in config.ini.
# Uses the stdlib only so the deck can resolve the engine before it exists
# on PYTHONPATH. $(shell) flattens newlines, so the resolver is a pipe.
ifndef SKILL
SKILL := $(shell MARKDOWN_SLIDES_HOME="$(MARKDOWN_SLIDES_HOME)" printf '%s\n' \
	'import configparser, os, sys' \
	'from pathlib import Path' \
	'root = Path(sys.argv[1]).resolve()' \
	'raw = os.environ.get("MARKDOWN_SLIDES_HOME", "").strip()' \
	'parser = configparser.ConfigParser(interpolation=None)' \
	'ini = root / "config.ini"' \
	'ini.is_file() and parser.read(ini, encoding="utf-8")' \
	'raw = raw or parser.get("build", "skill", fallback="").strip()' \
	'if not raw:' \
	'    sys.stderr.write("set SKILL= or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini\\n")' \
	'    sys.exit(1)' \
	'path = Path(raw).expanduser()' \
	'path = path if path.is_absolute() else root / path' \
	'path = path.resolve()' \
	'ok = path.is_dir() and (path / "scripts" / "build-slides.py").is_file()' \
	'if not ok:' \
	'    sys.stderr.write("not a markdown-slides skill (missing scripts/build-slides.py): %s\\n" % raw)' \
	'    sys.exit(1)' \
	'print(path)' \
	| python3 - "$(DECK_ROOT)")
endif

.PHONY: help html ppt pdf serve lint fmt test fonts

help:
	@echo "Targets (run from the deck root):"
	@echo "  make html    build HTML via the markdown-slides skill"
	@echo "  make ppt     build PPTX"
	@echo "  make pdf     export PDF"
	@echo "  make serve   serve the deck locally"
	@echo "  make fmt     format Python in the skill"
	@echo "  make lint    ruff + markdownlint (skill, plus this deck's Markdown)"
	@echo "  make test    run the skill unit tests"
	@echo "  make fonts   vendor Google Fonts into the skill cache"
	@echo "Set SKILL or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini."

html ppt pdf serve lint fmt test fonts:
	@if [ -z "$(SKILL)" ]; then \
		echo "set SKILL= or MARKDOWN_SLIDES_HOME, or [build] skill in config.ini" >&2; \
		exit 1; \
	fi
	@if [ ! -f "$(SKILL)/scripts/build-slides.py" ]; then \
		echo "not a markdown-slides skill (missing scripts/build-slides.py): $(SKILL)" >&2; \
		exit 1; \
	fi
	$(MAKE) -C "$(SKILL)" $@ DECK_ROOT="$(DECK_ROOT)"
