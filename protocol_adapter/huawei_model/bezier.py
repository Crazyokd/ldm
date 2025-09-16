import numpy as np
from typing import Tuple


class CubicBezier:
    """三阶贝塞尔"""

    def __init__(self, p0, p1, p2, p3):
        # 初始化控制点
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)

    def curve(self, t):
        """计算三阶贝塞尔曲线的点"""
        return (
            (1 - t) ** 3 * self.p0
            + 3 * (1 - t) ** 2 * t * self.p1
            + 3 * (1 - t) * t**2 * self.p2
            + t**3 * self.p3
        )

    def derivative(self, t):
        """计算三阶贝塞尔曲线的一阶导数"""
        dP0 = 3 * (1 - t) ** 2 * (self.p1 - self.p0)
        dP1 = 6 * (1 - t) * t * (self.p2 - self.p1)
        dP2 = 3 * t**2 * (self.p3 - self.p2)
        return dP0 + dP1 + dP2

    def second_derivative(self, t):
        """计算三阶贝塞尔曲线的二阶导数"""
        d2P0 = -6 * (1 - t) * (self.p1 - self.p0)
        d2P1 = 6 * (1 - 2 * t) * (self.p2 - self.p1)
        d2P2 = 6 * t * (self.p3 - self.p2)
        return d2P0 + d2P1 + d2P2

    def curvature(self, t):
        """计算曲率"""
        B_prime = self.derivative(t)
        B_double_prime = self.second_derivative(t)

        # 计算叉积（二维向量的叉积）
        cross_product = np.abs(np.cross(B_prime, B_double_prime))

        # 计算一阶导数的模长
        B_prime_length = np.linalg.norm(B_prime)

        # 计算曲率
        if B_prime_length == 0:
            return 0
        else:
            return cross_product / (B_prime_length**3)

    def plot_curve_and_curvature(self):
        import matplotlib.pyplot as plt

        """绘制贝塞尔曲线和曲率"""
        t_values = np.linspace(0, 1, 1000)

        # 计算曲线点和曲率
        curve_points = np.array([self.curve(t) for t in t_values])
        curvatures = np.array([self.curvature(t) for t in t_values])

        # 绘制贝塞尔曲线
        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(curve_points[:, 0], curve_points[:, 1], label='Bezier Curve')
        plt.scatter(
            [self.p0[0], self.p1[0], self.p2[0], self.p3[0]],
            [self.p0[1], self.p1[1], self.p2[1], self.p3[1]],
            color='red',
            label='Control Points',
        )
        # 绘制控制点之间的连线
        control_points = np.array([self.p0, self.p1, self.p2, self.p3])
        plt.plot(control_points[:, 0], control_points[:, 1], 'r--', label='Control Point Lines')

        # 设置坐标轴等比例
        plt.axis('equal')

        plt.legend()
        plt.title('Cubic Bezier Curve')
        plt.xlabel('x')
        plt.ylabel('y')

        # 绘制曲率
        plt.subplot(1, 2, 2)
        plt.plot(t_values, curvatures, label='Curvature')
        plt.title('Curvature of Bezier Curve')
        plt.xlabel('t')
        plt.ylabel('Curvature')
        plt.legend()

        plt.tight_layout()
        plt.show()


class QuinticBezier:
    """五阶贝塞尔曲线"""

    def __init__(self, p0, p1, p2, p3, p4, p5):
        # 初始化控制点
        self.p0 = np.array(p0)
        self.p1 = np.array(p1)
        self.p2 = np.array(p2)
        self.p3 = np.array(p3)
        self.p4 = np.array(p4)
        self.p5 = np.array(p5)

    def curve(self, t):
        """计算五阶贝塞尔曲线的点"""
        return (
            (1 - t) ** 5 * self.p0
            + 5 * (1 - t) ** 4 * t * self.p1
            + 10 * (1 - t) ** 3 * t**2 * self.p2
            + 10 * (1 - t) ** 2 * t**3 * self.p3
            + 5 * (1 - t) * t**4 * self.p4
            + t**5 * self.p5
        )

    def derivative(self, t):
        """计算五阶贝塞尔曲线的一阶导数"""
        dP0 = 5 * (1 - t) ** 4 * (self.p1 - self.p0)
        dP1 = 20 * (1 - t) ** 3 * t * (self.p2 - self.p1)
        dP2 = 30 * (1 - t) ** 2 * t**2 * (self.p3 - self.p2)
        dP3 = 20 * (1 - t) * t**3 * (self.p4 - self.p3)
        dP4 = 5 * t**4 * (self.p5 - self.p4)
        return dP0 + dP1 + dP2 + dP3 + dP4

    def second_derivative(self, t):
        """计算五阶贝塞尔曲线的二阶导数"""
        d2P0 = 20 * (1 - t) ** 3 * (self.p2 - 2 * self.p1 + self.p0)
        d2P1 = 60 * (1 - t) ** 2 * t * (self.p3 - 2 * self.p2 + self.p1)
        d2P2 = 60 * (1 - t) * t**2 * (self.p4 - 2 * self.p3 + self.p2)
        d2P3 = 20 * t**3 * (self.p5 - 2 * self.p4 + self.p3)
        return d2P0 + d2P1 + d2P2 + d2P3

    def curvature(self, t):
        """计算曲率"""
        B_prime = self.derivative(t)
        B_double_prime = self.second_derivative(t)

        # 计算叉积（二维向量的叉积）
        cross_product = np.abs(np.cross(B_prime, B_double_prime))

        # 计算一阶导数的模长
        B_prime_length = np.linalg.norm(B_prime)

        # 计算曲率
        if B_prime_length == 0:
            return 0
        else:
            return cross_product / (B_prime_length**3)

    def plot_curve_and_curvature(self):
        """绘制贝塞尔曲线和曲率"""
        import matplotlib.pyplot as plt

        t_values = np.linspace(0, 1, 1000)

        # 计算曲线点和曲率
        curve_points = np.array([self.curve(t) for t in t_values])
        curvatures = np.array([self.curvature(t) for t in t_values])

        # 绘制贝塞尔曲线
        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(curve_points[:, 0], curve_points[:, 1], label='Bezier Curve')
        plt.scatter(
            [self.p0[0], self.p1[0], self.p2[0], self.p3[0], self.p4[0], self.p5[0]],
            [self.p0[1], self.p1[1], self.p2[1], self.p3[1], self.p4[1], self.p5[1]],
            color='red',
            label='Control Points',
        )
        # 绘制控制点之间的连线
        control_points = np.array([self.p0, self.p1, self.p2, self.p3, self.p4, self.p5])
        plt.plot(control_points[:, 0], control_points[:, 1], 'r--', label='Control Point Lines')

        # 设置坐标轴等比例
        plt.axis('equal')

        plt.legend()
        plt.title('5th Degree Bezier Curve')
        plt.xlabel('x')
        plt.ylabel('y')

        # 绘制曲率
        plt.subplot(1, 2, 2)
        plt.plot(t_values, curvatures, label='Curvature')
        plt.title('Curvature of Bezier Curve')
        plt.xlabel('t')
        plt.ylabel('Curvature')
        plt.legend()

        plt.tight_layout()
        plt.show()


def verify_curvature_is_robot_acceptable(bezier: CubicBezier) -> Tuple[bool, float, float]:
    """确保曲率是机器人可接受的，当检查不通过时返回t和t处的曲率"""
    ACCEPTABLE_CURVATURE = 10  # 运动控制可以接受的曲率（10对于半径0.1m）
    for i in range(1000):
        t = i / 1000.0
        # 规划出来的路径曲率不能过大，过大运动控制无法走，也会产生各种奇怪的旋转
        curvature = bezier.curvature(t)
        if curvature > ACCEPTABLE_CURVATURE:
            return False, t, float(curvature)
    return True, 0, 0


# evaluates cubic bezier at t, return point
def q(ctrlPoly, t):
    return (
        (1.0 - t) ** 3 * ctrlPoly[0]
        + 3 * (1.0 - t) ** 2 * t * ctrlPoly[1]
        + 3 * (1.0 - t) * t**2 * ctrlPoly[2]
        + t**3 * ctrlPoly[3]
    )


# 5阶取点
def q5(ctrlPoly, t):
    return (
        (1.0 - t) ** 5 * ctrlPoly[0]
        + 5 * (1.0 - t) ** 4 * t * ctrlPoly[1]
        + 10 * (1.0 - t) ** 3 * t**2 * ctrlPoly[2]
        + 10 * (1.0 - t) ** 2 * t**3 * ctrlPoly[3]
        + 5 * (1.0 - t) * t**4 * ctrlPoly[4]
        + t**5 * ctrlPoly[5]
    )


# 5阶求导
def qprime5(ctrlPoly, t):
    return 5 * (
        (1.0 - t) ** 4 * (ctrlPoly[1] - ctrlPoly[0])
        + 4 * (1.0 - t) ** 3 * t * (ctrlPoly[2] - ctrlPoly[1])
        + 6 * (1.0 - t) ** 2 * t**2 * (ctrlPoly[3] - ctrlPoly[2])
        + 4 * (1.0 - t) * t**3 * (ctrlPoly[4] - ctrlPoly[3])
        + t**4 * (ctrlPoly[5] - ctrlPoly[4])
    )


# 5阶2阶导数
def qprimeprime5(ctrlPoly, t):
    tmp_points = ctrlPoly.copy()
    for i in range(0, 2):
        for j in range(0, len(ctrlPoly) - i - 1):
            tmp_points[j] = tmp_points[j + 1] - tmp_points[j]
    return 5 * 4 * get_point(tmp_points[:4], t)


# evaluates cubic bezier first derivative at t, return point
def qprime(ctrlPoly, t):
    return (
        3 * (1.0 - t) ** 2 * (ctrlPoly[1] - ctrlPoly[0])
        + 6 * (1.0 - t) * t * (ctrlPoly[2] - ctrlPoly[1])
        + 3 * t**2 * (ctrlPoly[3] - ctrlPoly[2])
    )


# evaluates cubic bezier second derivative at t, return point
def qprimeprime(ctrlPoly, t):
    return 6 * (1.0 - t) * (ctrlPoly[2] - 2 * ctrlPoly[1] + ctrlPoly[0]) + 6 * (t) * (
        ctrlPoly[3] - 2 * ctrlPoly[2] + ctrlPoly[1]
    )


# from any bezier
def get_point(control_points, t):
    if len(control_points) == 4:
        return q(control_points, t)
    if len(control_points) == 6:
        return q5(control_points, t)
    tmp_points = control_points.copy()
    for i in range(1, len(tmp_points)):
        for j in range(0, len(tmp_points) - i):
            tmp_points[j] = tmp_points[j] * (1 - t) + tmp_points[j + 1] * t
    return tmp_points[0]


if __name__ == '__main__':
    bezier = CubicBezier([1, 0], [1, 1.3], [-1, 1.3], [-1, 0])
    bezier.plot_curve_and_curvature()
