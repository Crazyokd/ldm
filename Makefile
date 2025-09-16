OUT_DIR ?= out
PY_VERSION ?= 3.13

# ci related
COV_REPORT_DIR := coverage_report

.PHONY: venv build binary binary-dist pack-dist-src test clean distclean

venv:
	rm -f uv.lock
	uv venv -p ${PY_VERSION}
	uv sync --all-extras

build:
	uv sync --all-extras
	uv build -o ${OUT_DIR}

binary:
	uv sync --all-extras
	uv build --wheel -o ${OUT_DIR}

binary-dist:
	cp doc/adapter_mock.adoc ${OUT_DIR}/readme_mock.adoc
	ln -s lib/main.bin ${OUT_DIR}/adapter
	tar -acf ${OUT_DIR}/dist.bin.tar.zst \
		--exclude="*.py[ic]" --exclude="__pycache__" \
		config --xform='s,^main.dist,lib,' -C ${OUT_DIR}/ \
		main.dist adapter readme_mock.adoc
	rm ${OUT_DIR}/adapter

pack-dist-src:
	./tool/generate.sh
	mkdir -p ${OUT_DIR}
	tar -acf ${OUT_DIR}/dist.src.tar.zst \
		--exclude="*_test.py" --exclude="*_mock.py" --exclude="*.py[ic]" --exclude="__pycache__" \
		config protocol_adapter --xform='s,^tool/launcher.sh,adapter,;s,^main.py,adapter_main.py,' \
		main.py tool/launcher.sh

pack-dist-bin-mock:
	./container/build.sh build_with_container
	sudo chown -R $$(id -u):$$(id -g) .

test: build
	uv run coverage run -m pytest --junitxml ${COV_REPORT_DIR}/junit.xml -s -x .
	uv run coverage xml --skip-empty
	uv run coverage report --skip-empty --precision=2

clean:
	@find . -name __pycache__ -type d -exec rm -rfv {} \+
	@rm -rfv ./protocol_adapter/version.py ./protocol_adapter/protobuf_wrapper/*_pb2.py*
	@rm -rfv .coverage coverage.xml ${COV_REPORT_DIR}

distclean: clean
	@rm -rfv ${OUT_DIR}
	@rm -rfv .venv
