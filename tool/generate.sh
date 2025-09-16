#!/bin/bash

# NOTE: 暂时保留，建议使用: make venv && make build

cd $(dirname $0)/.. # 切工作目录

generate_version_py() {
	echo "generate protocol-adapter version.py ..."

	branch_name=$(git rev-parse --abbrev-ref HEAD)
	git_desc_info="$(git describe --long --tags)"

	cat - >./protocol_adapter/version.py <<EOF
version_package = '$(echo $git_desc_info | sed 's/^v\([^-]*\)\(-[^-]*\)*-\(.*\)-g.*/\1-rc\3/')'
version_details = '${git_desc_info} $(date +%Y%m%d.%H%M%S) ${branch_name}'
EOF
}

generate_protobuf_py() {
	echo "generate protobuf *_pb2.py* ..."

	out_dir="$(realpath -L ./protocol_adapter/protobuf_wrapper/)"
	proto_dir="$(realpath -L ../core/proto/)"

	# 容器中暂时使用默认的 protoc
	if [ -d "${PROTOC_DIR}" -a -f "${PROTOC_DIR}/protoc" ]; then
		protoc_cmd=("${PROTOC_DIR}/protoc")
	else
		protoc_cmd=(uv run python -m grpc_tools.protoc)
	fi

	# 同时生成 pyi 文件，协助类型提示
	protoc_args=(-I"${proto_dir}" --python_out="${out_dir}" --pyi_out="${out_dir}")

	# 顺序生成 monitor, main 的 protobuf 源码
	for name in monitor main; do
		"${protoc_cmd[@]}" "${protoc_args[@]}" "${proto_dir}/$name.proto"
	done

	# 配合包结构调整导入
	sed -i 's/^\(import monitor_pb2 as .*\)/from protocol_adapter.protobuf_wrapper \1/' $out_dir/main_pb2.py*
}

generate_version_py
generate_protobuf_py
