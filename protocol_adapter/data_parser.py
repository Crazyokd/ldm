import json
import pathlib
import logging

_logger = logging.getLogger(__name__)

MAP_DIR = '/sros/map'


def read_file(file_path):
    if file_path == '' or not pathlib.Path(file_path).exists():
        raise OSError(f'file not exist: {file_path}')
    return pathlib.Path(file_path).read_text()


class DMCodeParser:
    dmcode_list = []

    def __init__(self):
        pass

    @classmethod
    def is_dmcode_damaged(cls, code):
        for dmcode in cls.dmcode_list:
            if dmcode['dmcode_id'] == code:
                return dmcode['damaged']
        return False

    @classmethod
    def get_dmcode_list(cls, map_name: str) -> None:
        """
        获取地图中的所有二维码信息
        :param map_name: 地图名
        :return: None
        """
        if not map_name:
            _logger.error(f'map name is valid: {map_name}')
            return
        try:
            file_path = f'{MAP_DIR}/{map_name}.info'
            file_content = read_file(file_path)
            dat = json.loads(file_content, encoding='utf-8')
            dm_code = dat['dm_code']
            location = dm_code['location']
            for key in location:
                info = location[key]
                cls.dmcode_list.append(
                    {
                        'dmcode_id': info['code_id'],
                        'x': float(info['world_pose']['x']),
                        'y': float(info['world_pose']['y']),
                        'yaw': float(info['world_pose']['yaw']),
                        'weight': int(info['weight']),
                        'recorded': info['recorded'] == 'True',
                        'damaged': info['damaged'] == 'True',
                    }
                )
        except BaseException as e:
            _logger.warning(f'parse qrcode file error, map_name is {map_name}: {e}')
