.PHONY: help \
       install install-dev install-test install-all \
       test test-all test-vgit test-vdsql \
       build man zsh-completion docker \
       setup-hooks setup-vscode lint \
       diff-test clean

help:
	@echo "Install:"
	@echo "  make install           pip install visidata"
	@echo "  make install-dev       editable install with dev deps"
	@echo "  make install-test      install with test deps"
	@echo "  make install-all       install with all optional deps"
	@echo ""
	@echo "Test:"
	@echo "  make test              run all tests (same as test-all)"
	@echo ""
	@echo "Build:"
	@echo "  make man               generate man pages (requires soelim, preconv, aha)"
	@echo "  make zsh-completion    generate zsh completion script"
	@echo "  make docker            build docker images"
	@echo ""
	@echo "Setup:"
	@echo "  make setup-hooks       configure git to use dev/hooks"
	@echo "  make setup-vscode      copy devcontainer configs to .vscode/"
	@echo ""
	@echo "Utility:"
	@echo "  make lint              run ruff linter"
	@echo "  make diff-test         show diffs from last test run"
	@echo "  make clean             remove generated files"

install:
	pip3 install .

install-dev:
	pip3 install -r dev/requirements-dev.txt
	pip3 install -e .

install-test:
	pip3 install ".[test]"

install-all:
	pip3 install ".[all]"

test: test-all

test-all:
	dev/test-all.sh

test-vgit:
	vd --config tests/.visidatarc -p visidata/apps/vgit/tests/*.vdx --batch

test-vdsql:
	cd visidata/apps/vdsql && ./test.sh

build: man zsh-completion

man:
	dev/mkman.sh

zsh-completion:
	python3 dev/zsh-completion.py _visidata

docker:
	dev/build-container

# Setup

setup-hooks:
	git config core.hooksPath dev/hooks

setup-vscode:
	mkdir -p .vscode
	cp .devcontainer/launch.json .vscode/launch.json
	cp .devcontainer/settings.json .vscode/settings.json

# Utility

lint:
	ruff check .

diff-test:
	dev/diff-test.sh

clean:
	rm -f visidata/man/vd.1 visidata/man/visidata.1 visidata/man/vd.txt
	rm -f docs/man.md
