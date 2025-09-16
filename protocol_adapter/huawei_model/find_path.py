import numpy as np

from protocol_adapter.huawei_model import bezier


def dist_point_2_line(point, control_points):
    line_s = control_points[0]
    line_e = control_points[-1]
    s2p = point - line_s
    e2p = point - line_e
    s2e = line_e - line_s
    if np.dot(s2e, s2p) < 0:
        return np.dot(s2p, s2p) ** 0.5, 0
    if np.dot(-s2e, e2p) < 0:
        return np.dot(e2p, e2p) ** 0.5, 1
    dist_pow2 = np.dot(s2p, s2p) - np.dot(s2p, s2e) ** 2 / np.dot(s2e, s2e)
    return dist_pow2**0.5, 0.5


def dist_point_2_bezier(point, control_points):
    if len(control_points) != 6:
        return -1, -1
    s2p = point - control_points[0]
    s2e = control_points[-1] - control_points[0]
    init_t = np.dot(s2p, s2e) / np.dot(s2e, s2e)
    if not is_possible_inner_point(point, control_points) or init_t < 0 or init_t > 1:
        dist2s = np.dot(control_points[0] - point, control_points[0] - point) ** 0.5
        dist2e = np.dot(control_points[-1] - point, control_points[-1] - point) ** 0.5
        if dist2s < dist2e:
            return dist2s, 0
        else:
            return dist2e, 1
    return tow_div_root_find5(control_points, point, init_t)


# 初步判断是否适合拟合贝塞尔
# 控制点如果是任意的，可以判断点是否在控制点组成的凸包内，原理是凸包内任意两点确定的线段属于凸包
# 目前ldm控制点都是水平或竖直的，可以简化判断
def is_possible_inner_point(point_i, control_points):
    control_point_min = control_points[0].copy() - 200
    control_point_max = control_points[0].copy() + 200
    for point in control_points:
        if point[0] < control_point_min[0]:
            control_point_min[0] = point[0] - 200  # 偏离所有路径20cm以上直接报错
        if point[1] < control_point_min[1]:
            control_point_min[1] = point[1] - 200
        if point[0] > control_point_max[0]:
            control_point_max[0] = point[0] + 200
        if point[1] > control_point_max[1]:
            control_point_max[1] = point[1] + 200
    return (
        point_i[0] <= control_point_max[0]
        and point_i[0] >= control_point_min[0]
        and point_i[1] <= control_point_max[1]
        and point_i[1] >= control_point_min[1]
    )


def tow_div_root_find5(bez, point, t):
    u = t
    dot_u, d, q_v = cal_dot(bez, point, u)
    dot_u_s, d_s, q_v_s = cal_dot(bez, point, 0)
    dot_u_e, d_e, q_v_e = cal_dot(bez, point, 1)
    ret_d, ret_u = np.dot(d, d) ** 0.5, u
    if ret_d == 0.0 or abs(dot_u / ret_d / np.dot(q_v, q_v) ** 0.5) < 0.0006:
        return ret_d, ret_u
    u_s = 0
    u_e = 1
    if normal_digit(dot_u) * normal_digit(dot_u_s) < 0:
        u_e = u
    elif normal_digit(dot_u) * normal_digit(dot_u_e) < 0:
        u_s = u
    else:
        for i in range(0, 10):
            dot_i, d_i, q_v_i = cal_dot(bez, point, i / 10)
            if normal_digit(dot_u) * normal_digit(dot_i) < 0:
                if i / 10 < u:
                    u_s, u_e = i / 10, u
                else:
                    u_s, u_e = u, i / 10
                break

    for i in range(0, 18):
        u_mid = (u_s + u_e) / 2
        dot_u_mid, d_mid, q_mid = cal_dot(bez, point, u_mid)
        if normal_digit(dot_u_mid) * normal_digit(dot_u_s) <= 0:
            u_e = u_mid
        elif normal_digit(dot_u_mid) * normal_digit(dot_u_e) <= 0:
            u_s = u_mid
        else:
            print('eror, i ', i)
            return ret_d, ret_u
        ret_u = u_mid
        dot_mid, d_mid, q_v_mid = cal_dot(bez, point, u_mid)
        ret_d = np.dot(d_mid, d_mid) ** 0.5
        sin_dot_angle = abs(dot_mid / ret_d / np.dot(q_v_mid, q_v_mid) ** 0.5)
        if ret_d == 0 or sin_dot_angle < 0.0006:
            return ret_d, ret_u
    return ret_d, ret_u


def cal_dot(bez, point, u):
    d = bezier.q5(bez, u) - point
    qprime5_v = bezier.qprime5(bez, u)
    return np.dot(d, qprime5_v), d, qprime5_v


def normal_digit(digit):
    if digit > 0.0:
        return 1
    elif digit < 0.0:
        return -1
    else:
        return 0


# 实际收敛速度比二分法还慢
def newtonRaphsonRootFind5(bez, point, t):
    """
    Newton's root finding algorithm calculates f(x)=0 by reiterating
    x_n+1 = x_n - f(x_n)/f'(x_n)

    We are trying to find curve parameter u for some point p that minimizes
    the distance from that point to the curve. Distance point to curve is d=q(u)-p.
    At minimum distance the point is perpendicular to the curve.
    We are solving
    f = (q(u)-p )* q'(u) = 0
    with
    f' = q'(u) * q'(u) + (q(u)-p) * q''(u)

    gives
    u_n+1 = u_n - |q(u_n)-p * q'(u_n)| / |q'(u_n)**2 + q(u_n)-p * q''(u_n)|
    """
    u = t
    len_d = -1
    for i in range(0, 100):
        d = bezier.q5(bez, u) - point
        qprime5_v = bezier.qprime5(bez, u)
        qprime5prime5_v = bezier.qprimeprime5(bez, u)
        numerator = np.dot(d, qprime5_v)
        denominator = (qprime5prime5_v * qprime5prime5_v + d * qprime5prime5_v).sum()
        len_d = np.dot(d, d) ** 0.5
        len_v = np.dot(qprime5_v, qprime5_v) ** 0.5

        if len_d == 0.0 or abs(np.dot(d, qprime5_v) / len_d / len_v) < 0.006 or denominator == 0.0:
            print('will return')
            break
        u = u - numerator / denominator
    return len_d, u
