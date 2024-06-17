# Reading dotenv
DOTENV ?=.env
ifneq (, $(DOTENV))
ifneq (,$(wildcard ./$(DOTENV)))
	include $(DOTENV)
	export
endif
endif

.PHONY:install.pre-commit
install.pre-commit:
	pre-commit install


.PHONY: install.deps
install.deps:
	poetry install

.PHONY:
install: install.deps install.pre-commit

.PHONY: lint
lint:
	ruff check .
	pyright

.PHONY: test
test:
	pytest
