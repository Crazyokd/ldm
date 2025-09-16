import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from hatchling.metadata.plugin.interface import MetadataHookInterface
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class Utils:
    @classmethod
    def check_command_output(cls, cmd: str, **kwargs) -> str:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True, **kwargs
        ).stdout.strip()


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata['version'] = Utils.check_command_output(
            r"git describe --long --tags | sed 's/^v\([^-]*\)\(-[^-]*\)*-\(.*\)-g.*/\1-rc\3/'"
        )


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        # skip on: Building wheel from source distribution...
        if not Path(self.directory).is_relative_to(Path(self.root)):
            return

        self.generate_version_py()
        self.generate_protobuf_py()

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        if self.target_name == 'wheel' and Path(self.directory).is_relative_to(Path(self.root)):
            self.generate_binary_with_nuitka()

    def generate_version_py(self):
        self.app.display_info('> generate version py ..')

        timestamp = datetime.now().strftime('%Y%m%d.%H%M%S')
        branch_name = Utils.check_command_output('git rev-parse --abbrev-ref HEAD')
        git_desc_info = Utils.check_command_output('git describe --long --tags')

        Path(self.config['autogen']['version_py']).write_text(
            f"version_package = '{self.metadata.version}'\n"
            f"version_details = '{git_desc_info} {timestamp} {branch_name}'\n"
        )

    def generate_protobuf_py(self):
        self.app.display_info('> generate protobuf code ..')

        autogen = self.config['autogen']
        proto_dir, out_dir = autogen['proto_dir'], autogen['proto_out_dir']

        protoc_cmd = 'uv run python -m grpc_tools.protoc'.split()
        protoc_args = [
            f'--proto_path={proto_dir}',
            f'--python_out={out_dir}',
            f'--pyi_out={out_dir}',
        ]

        # genetate py code from proto
        for proto_file in autogen['proto_files']:
            # it's already in uv venv, grpc_tools is in another venv
            subprocess.run(
                protoc_cmd + protoc_args + [f'{proto_dir}/{proto_file}'], check=True, env={}
            )

        # post hack for the package layout
        re_from = r'^\(import monitor_pb2 as .*\)'
        re_to = r'from protocol_adapter.protobuf_wrapper \1'
        Utils.check_command_output(f'sed -i "s/{re_from}/{re_to}/" {out_dir}/main_pb2.py*')

    def generate_binary_with_nuitka(self):
        self.app.display_info('> generate binary with nuitka ..')

        nuitka_conf = self.config['nuitka']
        copy_from = Utils.check_command_output(
            'uv pip show nuitka|grep "^Location:"', env={}
        ).split()[1]

        cmd_args = (
            'uv run nuitka'.split()
            + nuitka_conf['args']
            + '--show-memory --show-progress --follow-imports'.split()
            + [
                f'--output-dir={self.directory}',
                f'--report={self.directory}/{nuitka_conf["report"]}',
            ]
            + [f'--nofollow-import-to={x}' for x in nuitka_conf['nofollow']]
            + [f'--include-module={x}' for x in nuitka_conf['module_extra']]
            + [f'--include-raw-dir={copy_from}/{x}={x}' for x in nuitka_conf['module_copy']]
            + [f'--noinclude-data-files={x}' for x in nuitka_conf['exclude_copy']]
            + [f'--enable-plugins={x}' for x in nuitka_conf['plugins']]
            + [nuitka_conf['entry']]
        )

        # for nested `uv run nuitka`
        env = os.environ.copy()
        env.pop('VIRTUAL_ENV')

        # run and count the time
        t_0 = datetime.now()
        subprocess.run(cmd_args, check=True, env=env)
        d_t = datetime.now() - t_0

        self.app.display_info(f'=> build time: {d_t.seconds // 60}m{d_t.seconds % 60}s')
