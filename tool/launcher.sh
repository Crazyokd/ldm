#!/bin/bash

SROS_ROOT=/sros
ADAPTER_ROOT="${SROS_ROOT}/protocol_adapter/"

# 调试开关，切项目目录后执行，观察执行流程
DEBUG=false
$DEBUG && ADAPTER_ROOT="$PWD" && D_ECHO=echo || D_ECHO=

# 更新后第一次启动是否需要初始化
RUN_INIT_STEP=true
UPDATE_RECORD="$ADAPTER_ROOT/.update.log"

[ -d "$ADAPTER_ROOT" ] && cd "$ADAPTER_ROOT" || exit 1
echo "run protocol adapter .."

run_only_once() {
	echo "run the init steps .."

	$DEBUG && return 2

	# echo "临时处理 dns 问题 .."
	# dn="lemdevice.make.huawei.com"
	# grep -q "$dn" /etc/hosts ||
	# 	echo "10.28.96.101  $dn" >>/etc/hosts

	echo "清理历史版本 .."
	rm -rf \
		${SROS_ROOT}/protocol-adapter/ \
		${SROS_ROOT}/protocol_adapter/{run.sh,main.py} \
		${SROS_ROOT}/log/ldm-protocol-adapter \
		${SROS_ROOT}/log/ldm_protocol_adapter

	echo "numpy 依赖安装 .."
	python_version=$(python3 -V 2>&1 | awk '{print $2}')
	python_dir=python"${python_version:0:3}"
	#此处传安装包进去安装，因为源文件60M会不方便
	numpy_path=/usr/lib/python3.8/site-packages/numpy-1.24.2-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
	echo "${python_dir}"
	if python3 -c "import numpy" >/dev/null 2>&1; then
		echo "Numpy installed"
	elif [ "$python_dir" = "python3.8" ] && [ -f "${numpy_path}" ]; then
		echo "installing numpy"
		pip3 install ${numpy_path}
	fi

	echo "reboot in 5s .."
	sleep 5 && sync && reboot
}

match_last_update_version() {
	[ -f "$UPDATE_RECORD" ] && [ -n "$(tail -1 "$UPDATE_RECORD" | grep "$1: done")" ]
}

check_run_init_steps() {
	# 源码获取版本信息
	local version="$(grep version_details protocol_adapter/version.py | grep --only-matching "'.*'")"

	# 检查是否已经初始化
	match_last_update_version "$version" && RUN_INIT_STEP=false

	# 准备执行初始化
	$RUN_INIT_STEP && {
		echo "${version}: done" >>"$UPDATE_RECORD"

		# 检查是否跳过初始化设置成功，避免意外无限重启
		match_last_update_version "$version" && run_only_once
	}
}

check_run_init_steps
$D_ECHO python3 adapter_main.py --log-dir /sros/log --log-level info
