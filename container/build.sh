#!/bin/bash

IMAGE_NAME="uv_build"

cd "$(dirname "$0")/.."

build_image() {
	podman build --rm -t ${IMAGE_NAME} ./container/
}

build_with_container() {
	podman run --rm -it --env-file container/build.env \
		-v ${PWD}/..:/cc -v cache:/cache ${IMAGE_NAME} \
		bash /cc/protocol_adapter/container/build.sh make_in_container
}

make_in_container() {
	# bypass git safe.directory issue
	git config --global --add safe.directory "/cc"

	# cache uv python download manually
	mkdir -p /cache/.uv_python ~/.local/share/uv/ && ln -s /cache/.uv_python ~/.local/share/uv/python

	# set LD_LIBRARY_PATH for nuitka to auto copy libpython.so
	PY_LIBDIR="$(uv run python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")"
	export LD_LIBRARY_PATH+=":$PY_LIBDIR"

	# use dedicate dir for the build
	export OUT_DIR="out.cc"

	# build with make
	make venv
	make binary
	make binary-dist

	# repack with doc
	local GET_VERSION="from importlib.metadata import version; print(version('protocol_adapter'))"
	local PRJ_VERSION="$(uv run python -c "${GET_VERSION}")"
	mv $OUT_DIR/dist.bin.tar.zst $OUT_DIR/protocol_adapter-${PRJ_VERSION}-bin.tar.zst

	# 清理不同环境下的缓存
	rm -rf .venv
}

"$@"
