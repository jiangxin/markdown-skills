# Trampoline: python3 build.py (copied from templates/build.py).
# Copy this file to the deck root as Makefile, with build.py beside it.
#
#   make slides          HTML for slides/ -> build/slides/
#   make ppt slides      PPTX for that directory
#   make pdf slides      PDF for that directory
#   make html            HTML for [deck] slides
#   make serve           preview (default [deck] slides)

.DEFAULT_GOAL := help

QUALITY := help lint fmt test fonts
FORMATS := html ppt pdf serve
EXTRA := $(filter-out $(QUALITY) $(FORMATS),$(MAKECMDGOALS))

.PHONY: $(QUALITY) $(FORMATS)

$(QUALITY):
	python3 build.py $@

$(FORMATS):
	python3 build.py $@ $(EXTRA)

ifneq ($(EXTRA),)
.PHONY: $(EXTRA)
$(EXTRA):
	$(if $(filter $(FORMATS),$(MAKECMDGOALS)),@:,python3 build.py html $@)
endif
