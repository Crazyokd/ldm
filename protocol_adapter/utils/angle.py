import math

# 用于浮点数比较的精度容差
_e = 1e-8


class AngleUtils:
    @staticmethod
    def radians(degrees: float) -> float:
        """将角度转换为弧度"""
        return math.radians(degrees)

    @staticmethod
    def degrees(radians: float) -> float:
        """将弧度转换为角度"""
        return math.degrees(radians)

    @staticmethod
    def normalize_180(degrees: float) -> float:
        """将角度归一化到 (-180, 180] 度"""
        degrees = degrees % 360
        if degrees > 180:  # noqa: PLR2004
            degrees -= 360
        return degrees

    @staticmethod
    def normalize_360(degrees: float) -> float:
        """将角度归一化到 [0, 360) 度"""
        return degrees % 360

    @staticmethod
    def equal_norm(angle1: float, angle2: float, threshold: float = 0) -> bool:
        return AngleUtils.delta_norm(angle1, angle2) <= threshold + _e

    @staticmethod
    def delta_norm(angle1: float, angle2: float, *, absolute=True) -> float:
        """
        返回从 angle1 到 angle2 的最短路径(顺时针正，逆时针负) (-180, 180]
        """
        delta = AngleUtils.normalize_180(angle2 - angle1)
        return abs(delta) if absolute else delta

    @staticmethod
    def delta_90n(angle: float) -> float:
        """角度相对最近的 90n 的差值 [0, 45]"""
        return min(angle % 90, 90 - angle % 90)

    @staticmethod
    def is_90n(angle: float) -> bool:
        """角度是否是 90n 规整值"""
        return angle % 90 == 0

    @staticmethod
    def to_90n(angle: float) -> int:
        """角度转换到最接近的 90n"""
        angle %= 360

        quotient: int = int(angle // 90)
        remainder: float = angle % 90

        if remainder >= 45:  # noqa: PLR2004
            quotient += 1

        if quotient == 4:  # noqa: PLR2004
            quotient = 0

        return quotient * 90
