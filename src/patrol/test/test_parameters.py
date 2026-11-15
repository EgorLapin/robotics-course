# Copyright 2026 Egor Lapin
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""Unit tests for PR04 parameter validation and timer math of the patrol node."""

import math

from patrol.patrol import decide_command
from patrol.patrol import DEFAULTS
from patrol.patrol import PARAM_BOUNDS
from patrol.patrol import timer_period
from patrol.patrol import validate_param


def ok(name, value):
    """Shortcut: True if (name, value) passes validation."""
    passed, _ = validate_param(name, value, PARAM_BOUNDS[name])
    return passed


class TestValidateParam:
    """validate_param must reject non-finite and out-of-range values."""

    def test_defaults_are_valid(self):
        for name, value in DEFAULTS.items():
            assert ok(name, value)

    def test_zero_hz_rejected(self):
        assert not ok('publish_hz', 0.0)

    def test_negative_hz_rejected(self):
        assert not ok('publish_hz', -3.0)

    def test_nan_hz_rejected(self):
        assert not ok('publish_hz', math.nan)

    def test_inf_hz_rejected(self):
        assert not ok('publish_hz', math.inf)

    def test_hz_ten_to_five_ok(self):
        assert ok('publish_hz', 10.0)
        assert ok('publish_hz', 5.0)

    def test_hz_bounds_inclusive(self):
        assert ok('publish_hz', 1.0)
        assert ok('publish_hz', 30.0)
        assert not ok('publish_hz', 0.999)
        assert not ok('publish_hz', 30.001)

    def test_speed_range(self):
        assert ok('linear_speed', 0.0)
        assert ok('linear_speed', 1.0)
        assert not ok('linear_speed', 1.5)
        assert not ok('linear_speed', -0.1)

    def test_turn_rate_range(self):
        assert ok('turn_rate', -1.0)
        assert ok('turn_rate', 1.0)
        assert not ok('turn_rate', 1.2)

    def test_bool_rejected(self):
        # True is an int in Python — parameters must be real numbers.
        assert not ok('publish_hz', True)


class TestTimerPeriod:
    """Timer period is 1/publish_hz for validated values."""

    def test_period_ten(self):
        assert abs(timer_period(10.0) - 0.1) < 1e-12

    def test_period_change_ten_to_five(self):
        assert abs(timer_period(5.0) - 0.2) < 1e-12
        assert timer_period(5.0) == 2.0 * timer_period(10.0)


class TestDecideCommandParams:
    """decide_command uses parameter values and still clamps to actuator limits."""

    def _pose(self):
        class P:
            x = 1.0
            y = 2.0
        return P()

    def test_parameters_applied(self):
        cmd = decide_command(self._pose(), linear_x=0.2, angular_z=-0.4)
        assert cmd.linear.x == 0.2
        assert cmd.angular.z == -0.4

    def test_clamped_to_limits(self):
        cmd = decide_command(self._pose(), linear_x=1.0, angular_z=1.0)
        assert cmd.linear.x == 0.5
        assert cmd.angular.z == 1.0
