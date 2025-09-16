"""Python implementation of
Algorithm for Automatically Fitting Digitized Curves
by Philip J. Schneider
"Graphics Gems", Academic Press, 1990
"""

import logging
import numpy as np
from protocol_adapter.huawei_model import bezier

_logger = logging.getLogger(__name__)


# Fit one (ore more) Bezier curves to a set of points
def fitCurve(points, maxError):
    leftTangent = normalize(points[1] - points[0])
    rightTangent = normalize(points[-2] - points[-1])
    return fitCubic(points, leftTangent, rightTangent, maxError)


def fitCurveIsometricPara(points):
    u = []
    for i in range(0, len(points)):
        u.append(i / (len(points) - 1))
    leftTangent = normalize(points[1] - points[0])
    rightTangent = normalize(points[-2] - points[-1])
    return [generateBezier(points, u, leftTangent, rightTangent)]


# 针对5阶贝塞尔的拟合算法，传入参数是控制点
# 原理：用两条3阶贝塞尔拟合，第一条贝塞尔起点为原贝塞尔起点，且方向导数相等，终点为原贝塞尔的参数0.5对应的点，且方向导数相等
# 同时满足第一条贝塞尔参数为0.5时与原贝塞尔参数为0.25时重合。第二条贝塞尔以同样方式拟合
def fit_5_bezier_sqlit2(points):
    if len(points) != 6:
        return []
    try:
        p00 = points[0]
        p01 = np.zeros(2)
        p02 = np.zeros(2)
        p03 = bezier.q5(points, 0.5)
        prime00 = bezier.qprime5(points, 0)
        prime03 = bezier.qprime5(points, 0.5)
        p_mid = bezier.q5(points, 0.25)
        A = [
            [prime00[1], -prime00[0], 0, 0],
            [0, 0, prime03[1], -prime03[0]],
            [3.0, 0.0, 3.0, 0.0],
            [0.0, 3.0, 0.0, 3.0],
        ]
        A = np.array(A)
        b = [
            [prime00[1] * p00[0] - prime00[0] * p00[1]],
            [prime03[1] * p03[0] - prime03[0] * p03[1]],
            [8.0 * p_mid[0] - p00[0] - p03[0]],
            [8.0 * p_mid[1] - p00[1] - p03[1]],
        ]
        b = np.array(b)
        X1 = np.linalg.solve(A, b)
        p01[0] = X1[0].item()
        p01[1] = X1[1].item()
        p02[0] = X1[2].item()
        p02[1] = X1[3].item()

        p10 = p03
        p11 = np.zeros(2)
        p12 = np.zeros(2)
        p13 = points[5]
        prime10 = bezier.qprime5(points, 0.5)
        prime13 = bezier.qprime5(points, 1.0)
        p_mid = bezier.q5(points, 0.75)
        A2 = [
            [prime10[1], -prime10[0], 0, 0],
            [0, 0, prime13[1], -prime13[0]],
            [3.0, 0.0, 3.0, 0.0],
            [0.0, 3.0, 0.0, 3.0],
        ]
        A2 = np.array(A2)
        b2 = [
            [prime10[1] * p10[0] - prime10[0] * p10[1]],
            [prime13[1] * p13[0] - prime13[0] * p13[1]],
            [8.0 * p_mid[0] - p10[0] - p13[0]],
            [8.0 * p_mid[1] - p10[1] - p13[1]],
        ]
        b2 = np.array(b2)
        X2 = np.linalg.solve(A2, b2)
        p11[0] = X2[0].item()
        p11[1] = X2[1].item()
        p12[0] = X2[2].item()
        p12[1] = X2[3].item()
    except:
        return []
    bezier1_enddir = p03 - p02
    bezier2_stardir = p11 - p10
    if np.dot(bezier1_enddir, bezier2_stardir) < 0:
        return []

    return [[p00, p01, p02, p03], [p10, p11, p12, p13]]


def fit_5_bezier_sqlit1(points):
    if len(points) != 6:
        return []
    p00 = points[0]
    p01 = np.zeros(2)
    p02 = np.zeros(2)
    p03 = points[5]
    prime00 = bezier.qprime5(points, 0)
    prime03 = bezier.qprime5(points, 1.0)
    p_mid = bezier.q5(points, 0.5)
    A = [
        [prime00[1], -prime00[0], 0, 0],
        [0, 0, prime03[1], -prime03[0]],
        [3.0, 0.0, 3.0, 0.0],
        [0.0, 3.0, 0.0, 3.0],
    ]
    A = np.array(A)
    np.set_printoptions(precision=8)
    b = [
        [prime00[1] * p00[0] - prime00[0] * p00[1]],
        [prime03[1] * p03[0] - prime03[0] * p03[1]],
        [8.0 * p_mid[0] - p00[0] - p03[0]],
        [8.0 * p_mid[1] - p00[1] - p03[1]],
    ]
    b = np.array(b).astype(float)
    try:
        X1 = np.linalg.solve(A, b)
    except Exception as e:
        _logger.error(e)
        return []
    p01[0] = X1[0].item()
    p01[1] = X1[1].item()
    p02[0] = X1[2].item()
    p02[1] = X1[3].item()

    return [[p00, p01, p02, p03]]


def fitCubic(points, leftTangent, rightTangent, error, u=[]):
    # Use heuristic if region only has two points in it
    if len(points) == 2:
        dist = np.linalg.norm(points[0] - points[1]) / 3.0
        bezCurve = [
            points[0],
            points[0] + leftTangent * dist,
            points[1] + rightTangent * dist,
            points[1],
        ]
        return [bezCurve]

    # Parameterize points, and attempt to fit curve
    if u == []:
        print('u == []')
        u = chordLengthParameterize(points)
    bezCurve = generateBezier(points, u, leftTangent, rightTangent)
    # Find max deviation of points to fitted curve
    maxError, splitPoint = computeMaxError(points, bezCurve, u)
    if maxError < error:
        print('maxError:', maxError)
        return [bezCurve]

    # just find one bezier
    # if maxError < error**2:
    for _ in range(20):
        uPrime = reparameterize(bezCurve, points, u)
        bezCurve = generateBezier(points, uPrime, leftTangent, rightTangent)
        maxError, splitPoint = computeMaxError(points, bezCurve, uPrime)
        if maxError < error:
            return [bezCurve]
        u = uPrime

    # Fitting failed -- split at max error point and fit recursively
    beziers = []
    centerTangent = normalize(points[splitPoint - 1] - points[splitPoint + 1])
    beziers += fitCubic(points[: splitPoint + 1], leftTangent, centerTangent, error)
    beziers += fitCubic(points[splitPoint:], -centerTangent, rightTangent, error)

    return beziers


def generateBezier(points, parameters, leftTangent, rightTangent):
    bezCurve = [points[0], None, None, points[-1]]

    # compute the A's
    A = np.zeros((len(parameters), 2, 2))
    for i, u in enumerate(parameters):
        A[i][0] = leftTangent * 3 * (1 - u) ** 2 * u
        A[i][1] = rightTangent * 3 * (1 - u) * u**2

    # Create the C and X matrices
    C = np.zeros((2, 2))
    X = np.zeros(2)

    for i, (point, u) in enumerate(zip(points, parameters)):
        C[0][0] += np.dot(A[i][0], A[i][0])
        C[0][1] += np.dot(A[i][0], A[i][1])
        C[1][0] += np.dot(A[i][0], A[i][1])
        C[1][1] += np.dot(A[i][1], A[i][1])

        tmp = point - bezier.q([points[0], points[0], points[-1], points[-1]], u)

        X[0] += np.dot(A[i][0], tmp)
        X[1] += np.dot(A[i][1], tmp)

    # Compute the determinants of C and X
    det_C0_C1 = C[0][0] * C[1][1] - C[1][0] * C[0][1]
    det_C0_X = C[0][0] * X[1] - C[1][0] * X[0]
    det_X_C1 = X[0] * C[1][1] - X[1] * C[0][1]

    # Finally, derive alpha values
    alpha_l = 0.0 if det_C0_C1 == 0 else det_X_C1 / det_C0_C1
    alpha_r = 0.0 if det_C0_C1 == 0 else det_C0_X / det_C0_C1

    # If alpha negative, use the Wu/Barsky heuristic (see text) */
    # (if alpha is 0, you get coincident control points that lead to
    # divide by zero in any subsequent NewtonRaphsonRootFind() call. */
    segLength = np.linalg.norm(points[0] - points[-1])
    epsilon = 1.0e-6 * segLength
    if alpha_l < epsilon or alpha_r < epsilon:
        # fall back on standard (probably inaccurate) formula, and subdivide further if needed.
        bezCurve[1] = bezCurve[0] + leftTangent * (segLength / 3.0)
        bezCurve[2] = bezCurve[3] + rightTangent * (segLength / 3.0)

    else:
        # First and last control points of the Bezier curve are
        # positioned exactly at the first and last data points
        # Control points 1 and 2 are positioned an alpha distance out
        # on the tangent vectors, left and right, respectively
        bezCurve[1] = bezCurve[0] + leftTangent * alpha_l
        bezCurve[2] = bezCurve[3] + rightTangent * alpha_r

    return bezCurve


def reparameterize(bezier, points, parameters):
    return [newtonRaphsonRootFind(bezier, point, u) for point, u in zip(points, parameters)]


def newtonRaphsonRootFind(bez, point, u):
    """
    Newton's root finding algorithm calculates f(x)=0 by reiterating
    x_n+1 = x_n - f(x_n)/f'(x_n)

    We are trying to find curve parameter u for some point p that minimizes
    the distance from that point to the curve. Distance point to curve is d=q(u)-p.
    At minimum distance the point is perpendicular to the curve.
    We are solving
    f = (q(u)-p )* q'(u) = 0
    with
    f' = q'(u) * q'(u) + q(u)-p * q''(u)

    gives
    u_n+1 = u_n - |q(u_n)-p * q'(u_n)| / |q'(u_n)**2 + q(u_n)-p * q''(u_n)|
    """
    d = bezier.q(bez, u) - point
    numerator = (d * bezier.qprime(bez, u)).sum()
    denominator = (bezier.qprime(bez, u) ** 2 + d * bezier.qprimeprime(bez, u)).sum()

    if denominator == 0.0:
        return u
    else:
        return u - numerator / denominator


def chordLengthParameterize(points):
    u = [0.0]
    for i in range(1, len(points)):
        u.append(u[i - 1] + float(np.linalg.norm(points[i] - points[i - 1])))

    for i, _ in enumerate(u):
        u[i] = u[i] / u[-1]

    return u


# todo: should use newton root find caculate the min dist
def computeMaxError(points, bez, parameters):
    maxDist = 0.0
    splitPoint = len(points) / 2
    for i, (point, u) in enumerate(zip(points, parameters)):
        dist = np.linalg.norm(bezier.q(bez, u) - point) ** 2
        if dist > maxDist:
            maxDist = dist
            splitPoint = i

    return maxDist, splitPoint


def normalize(v):
    return v / np.linalg.norm(v)
