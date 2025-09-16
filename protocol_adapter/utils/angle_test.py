import pytest
import math

from protocol_adapter.utils.angle import AngleUtils, _e


class TestAngleUtils:
    @pytest.mark.parametrize(
        'input_deg, expected',
        [
            (0, 0),
            (math.pi / 3, 60),
            (math.pi / 2, 90),
            (-math.pi / 4, -45),
            (math.pi, 180),
            (2 * math.pi, 360),
            (4 * math.pi, 720),
        ],
    )
    def test_radians_degrees(self, input_deg, expected):
        assert AngleUtils.degrees(input_deg) == pytest.approx(expected, abs=_e)
        assert AngleUtils.radians(expected) == pytest.approx(input_deg, abs=_e)

    @pytest.mark.parametrize(
        'input_deg, exp_180, exp_360',
        [
            (0, 0, 0),
            (90, 90, 90),
            (180, 180, 180),
            (190, -170, 190),
            (360, 0, 0),
            (450, 90, 90),
            (272, -88, 272),
            (540, 180, 180),
            (719.2, -0.8, 359.2),
            (720.1, 0.1, 0.1),
            (-90, -90, 270),
            (-180, 180, 180),
            (-190, 170, 170),
        ],
    )
    def test_normalize_180(self, input_deg, exp_180, exp_360):
        assert AngleUtils.normalize_180(input_deg) == pytest.approx(exp_180, abs=_e)
        assert AngleUtils.normalize_360(input_deg) == pytest.approx(exp_360, abs=_e)

    @pytest.mark.parametrize(
        'a1, a2, threshold, expected',
        [
            (0, 0, 0, True),
            (0.1, 360, 0.09, False),
            (0.1, -360, 0.1, True),
            (0.1, 360, 0.2, True),
            (-22.22, 44.44, 20, False),
            (-22.22, 44.44, 70, True),
        ],
    )
    def test_equal(self, a1, a2, threshold, expected):
        assert AngleUtils.equal_norm(a1, a2, threshold) == expected

    @pytest.mark.parametrize(
        'a1, a2, expected_abs, expected_signed',
        [
            (0, 0, 0, 0),
            (0, 90, 90, 90),
            (45.2, 90, 44.8, 44.8),
            (90, 0, 90, -90),
            (350, 10, 20, 20),
            (10, 350, 20, -20),
            (180, -180, 0, 0),
            (360, -180, 180, 180),
            (2.2, 2.2, 0, 0),
            (-2.2, 4.2, 6.4, 6.4),
            (2.2, -4.2, 6.4, -6.4),
        ],
    )
    def test_delta(self, a1, a2, expected_abs, expected_signed):
        assert AngleUtils.delta_norm(a1, a2) == pytest.approx(expected_abs, abs=_e)
        assert AngleUtils.delta_norm(a1, a2, absolute=False) == pytest.approx(
            expected_signed, abs=_e
        )

    @pytest.mark.parametrize(
        'angle, expected',
        [
            (0, 0),
            (44.9, 44.9),
            (45, 45),
            (45.1, 44.9),
            (89.9, 0.1),
            (90, 0),
            (100, 10),
            (135, 45),
            (200, 20),
            (360, 0),
            (-88.2, 1.8),
            (-90.2, 0.2),
            (-180, 0),
        ],
    )
    def test_delta_90n(self, angle, expected):
        assert AngleUtils.delta_90n(angle) == pytest.approx(expected, abs=_e)

    @pytest.mark.parametrize(
        'angle, expected',
        [
            (0, 0),
            (44.9, 0),
            (45, 90),
            (45.1, 90),
            (89.9, 90),
            (90, 90),
            (100, 90),
            (135, 180),
            (200, 180),
            (360, 0),
            (-88.2, 270),
            (-90.2, 270),
            (-180, 180),
        ],
    )
    def test_to_90n(self, angle, expected):
        assert AngleUtils.to_90n(angle) == pytest.approx(expected, abs=_e)
