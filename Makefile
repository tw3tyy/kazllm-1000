# Reproduce the manuscript from the saved logs.
#   make results   recompute every number, table and figure (seed 42, ~1 min)
#   make paper     results + compile paper/main.pdf
#   make test      run the automated checks
PYTHON ?= python3

.PHONY: results paper test clean-paper

results:
	$(PYTHON) -m paper.analysis.run

paper: results
	cd paper && latexmk -pdf -interaction=nonstopmode main.tex

test:
	$(PYTHON) -m unittest discover -s tests -v

clean-paper:
	cd paper && latexmk -C main.tex
