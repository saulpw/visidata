.PHONY: help \
       install install-dev install-test install-all \
       test test-all test-vdx test-pytest test-smoke \
       test-roundtrip test-delimiter test-stdin test-stdin-replay \
       test-startpos test-startup-time test-perf test-macros test-zsh \
       test-individually \
       test-vgit test-vdsql \
       man zsh-completion docker \
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
	@echo "  make test-vdx          cmdlog golden tests"
	@echo "  make test-pytest       python unit tests"
	@echo "  make test-smoke        basic sanity check"
	@echo "  make test-roundtrip    format round-trip idempotence"
	@echo "  make test-delimiter    delimiter handling"
	@echo "  make test-stdin        stdin piping"
	@echo "  make test-stdin-replay stdin with replay"
	@echo "  make test-startpos     +N positioning args"
	@echo "  make test-startup-time startup < 400ms"
	@echo "  make test-perf         performance benchmarks"
	@echo "  make test-macros       macro replay"
	@echo "  make test-zsh          zsh completion generation"
	@echo "  make test-individually each test in isolation"
	@echo "  make test-vgit         vgit app tests"
	@echo "  make test-vdsql        vdsql app tests"
	@echo ""
	@echo "Build:"
	@echo "  make man               generate man pages (requires soelim, preconv, aha)"
	@echo "  make zsh-completion    generate zsh completion script"
	@echo "  make docker            build docker images"
	@echo ""
	@echo "Utility:"
	@echo "  make diff-test         show diffs from last test run"
	@echo "  make clean             remove generated files"

# Install

install:
	pip3 install .

install-dev:
	pip3 install -r dev/requirements-dev.txt
	pip3 install -e .

install-test:
	pip3 install .
	pip3 install ".[test]"

install-all:
	pip3 install ".[all]"

# Test

test: test-all

test-all:
	dev/test-all.sh

test-vdx:
	dev/test.sh

test-pytest:
	tests/test-pytest.sh

test-smoke:
	tests/test-smoke.sh

test-roundtrip:
	tests/test-roundtrip.sh

test-delimiter:
	tests/test-delimiter.sh

test-stdin:
	tests/test-stdin.sh

test-stdin-replay:
	tests/test-stdin-replay.sh

test-startpos:
	tests/test-startpos.sh

test-startup-time:
	tests/test-startup-time.sh

test-perf:
	tests/test-perf.sh

test-macros:
	tests/test-macros.sh

test-zsh:
	tests/test-zsh-syntax.sh

test-individually:
	dev/run-tests-individually.sh

test-vgit:
	vd -p visidata/apps/vgit/tests/*.vdx --batch

test-vdsql:
	cd visidata/apps/vdsql && ./test.sh

# Build

man:
	dev/mkman.sh

zsh-completion:
	python3 dev/zsh-completion.py _visidata

docker:
	dev/build-container

# Utility

diff-test:
	dev/diff-test.sh

clean:
	rm -f visidata/man/vd.1 visidata/man/visidata.1 visidata/man/vd.txt
	rm -f docs/man.md
