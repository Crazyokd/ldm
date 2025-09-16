from dataclasses import dataclass
from enum import IntEnum, Enum

"""
- 充电桩:
    异常告警
    状态上报
    充电任务

- 小车告警:
    地码识别
    地码缺失
    货码异常
    举升重量

- 点检: 适配器中采集上报
    噪音
    震动
    电机: (举升,行走,转向): 温度，电流, 转速
    高架堆垛 精度
"""


"""
点检任务通过 LDM 下发，任务完成信号上报给 LDM，只传点检结果到 LEM 系统。

== 高架/堆垛 AGV 精度点检 (待定)
    斯坦德 3 代高架 AGV：checkType = “0022”
    杭叉 3 代高架 AGV：checkType = “0023”
    堆垛 AGV 点检类型 checkType = “010”
    斯坦德 1 代堆垛 AGV：checkType = “0102”

== AGV 噪音点检结果 > 30Hz
    - 点检类型 checkType = “020”
    斯坦德 3 代高架 AGV checkType = “0202”
    斯坦德 1 代堆垛 AGV checkType = “0203”

== AGV 振动点检类型 checkType = “030”   > 10hz
    斯坦德 3 代高架 AGV checkType = “0303
    斯坦德 1 代堆垛 AGV checkType = “0304”

== AGV 电机电流、转速、温度: > 30 Hz, 时间同步

    - 举升电机点检类型 checkType = “004”
    斯坦德 4 代顶升 AGV（2023 年框架）checkType = “0043”
    斯坦德 3 代高架 AGV checkType = “0046”
    斯坦德 1 代堆垛 AGV checkType = “0047”

    - 行走电机点检类型 checkType = “005”
    斯坦德 4 代顶升 AGV（2023 年框架）checkType = “0053”
    斯坦德 3 代高架 AGV checkType = “0056”
    斯坦德 1 代堆垛 AGV checkType = “0057”

    - 转向电机点检类型 checkType = “006”
    斯坦德 3 代高架 AGV checkType = “0063”
    斯坦德 1 代堆垛 AGV checkType = “0064”
"""


class AlarmMainType(IntEnum):
    pass


class AlarmMinorType(IntEnum):
    pass


class AutoCheckAction(Enum):
    Init = 'init'
    AgvMove = 'agvMove'
    AgvRotate = 'agvRotate'
    LiftRotate = 'liftRotate'
    LiftUpDown = 'liftUpDown'
    ForkUpDown = 'forkUpDown'
    ForkOutIn = 'forkOutIn'
    ForkSidesway = 'forkSidesway'

    def __str__(self):
        return self.value

    def get_check_types(self):
        checktypes = [AutoCheckType.Noise_g3, AutoCheckType.Vibration_g3]
        if self == AutoCheckAction.AgvMove:
            checktypes.append(AutoCheckType.Propel_g3)
        elif self == AutoCheckAction.AgvRotate:
            checktypes.append(AutoCheckType.Propel_g3)  # 差速旋转，还是行走电机
            checktypes.append(AutoCheckType.Steering_g3)  # 转向电机暂时没有
        elif self in (AutoCheckAction.LiftUpDown, AutoCheckAction.LiftRotate):
            checktypes.append(AutoCheckType.Lift_g3)
        return checktypes


class AutoCheckType(Enum):
    Steering_g3 = '0063'
    Steering_g1 = '0064'
    Propel_g4 = '0053'
    Propel_g3 = '0056'
    Propel_g1 = '0057'
    Lift_g4 = '0043'
    Lift_g3 = '0046'
    Lift_g1 = '0047'
    Vibration_g3 = '0303'
    Vibration_g1 = '0304'
    Noise_g1 = '0203'
    Noise_g3 = '0202'

    def __str__(self):
        return self.value

    def get_motor_type(self) -> str:
        if self.name.startswith('Lift_'):
            return 'lift'
        elif self.name.startswith('Propel_'):
            return 'propel'
        elif self.name.startswith('Steering_'):
            return 'steering'
        else:
            return ''

    def is_vibration_check(self) -> bool:
        return self.name.startswith('Vibration_')

    def is_noise_check(self) -> bool:
        return self.name.startswith('Noise_')


class AutoCheckResult(IntEnum):
    Ok = 0
    Fail = 1
