# CKA Exam Prep Kit - build helpers
#
# Typical update loop:
#   1. edit anki/cka-cards.tsv
#   2. make            # rebuild deck + sync docs/, then verify
#   3. review the diff, then commit (you own all commits)
#
# No dependencies beyond Python 3 (stdlib only).

PYTHON  ?= python3
TSV      = anki/cka-cards.tsv
DECK     = anki/CKA-Deck.apkg
DOCS_TSV = docs/cka-cards.tsv
PORT    ?= 8000

.DEFAULT_GOAL := all

.PHONY: all build verify check-sync serve clean help

## all: build the deck, sync docs/, then verify everything (default)
all: build verify check-sync
	@echo "OK: deck built, docs/ synced, verified. Review the diff and commit."

## build: rebuild the .apkg and sync docs/cka-cards.tsv from the source TSV
build:
	$(PYTHON) anki/build_apkg.py

## verify: check the .apkg is a valid zip + sqlite with matching card counts
verify:
	$(PYTHON) anki/verify_apkg.py $(DECK) $(TSV)

## check-sync: fail if docs/cka-cards.tsv drifted from the source TSV
check-sync:
	@if ! diff -q $(TSV) $(DOCS_TSV) >/dev/null; then \
		echo "FAIL: $(DOCS_TSV) is out of sync. Run 'make build' and commit it."; \
		exit 1; \
	fi
	@echo "OK: docs/ card copy in sync."

## serve: preview the web reviewer locally (Ctrl-C to stop)
serve:
	@echo "Serving docs/ at http://localhost:$(PORT)/  (Ctrl-C to stop)"
	@cd docs && $(PYTHON) -m http.server $(PORT)

## clean: remove Python build artifacts
clean:
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -f anki/*.tmp
	@echo "cleaned."

## help: list available targets
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  /'
