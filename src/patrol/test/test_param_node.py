# Copyright 2026 Egor Lapin
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""Node-level tests: parameter changes recreate the timer; bad values change nothing."""

import math

from patrol.patrol import PatrolNode
import rclpy
from rclpy.parameter import Parameter


def make_node():
    """Init rclpy and return a fresh PatrolNode."""
    rclpy.init()
    return PatrolNode()


def destroy(node):
    """Destroy node and shutdown rclpy."""
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def set_hz(node, value):
    """Call the real parameter service path for publish_hz."""
    p = Parameter(name='publish_hz', type_=Parameter.Type.DOUBLE, value=value)
    return node.set_parameters([p])[0]


def test_change_hz_recreates_single_timer():
    """10 -> 5 Hz: new timer with 0.2 s period, the old one destroyed, one left."""
    node = make_node()
    try:
        old = node._timer
        result = set_hz(node, 5.0)
        assert result.successful
        assert node._timer is not old
        # прежний таймер уничтожен (destroy_timer): его handle больше не жив,
        # а в списке таймеров узла ровно один объект — двух таймеров не осталось.
        assert old not in list(node.timers)
        assert len(list(node.timers)) == 1
        assert abs(node._timer.timer_period_ns - 200_000_000) < 1_000_000
        assert node._values['publish_hz'] == 5.0
    finally:
        destroy(node)


def test_zero_hz_rejected_state_unchanged():
    """0 Hz rejected: same timer, old value and rate preserved."""
    node = make_node()
    try:
        before = node._timer
        period_before = before.timer_period_ns
        result = set_hz(node, 0.0)
        assert not result.successful
        assert 'publish_hz' in result.reason
        assert node._timer is before
        assert not before.is_canceled()
        assert node._timer.timer_period_ns == period_before
        assert node._values['publish_hz'] == 10.0
        assert len(list(node.timers)) == 1
    finally:
        destroy(node)


def test_negative_and_nan_rejected_state_unchanged():
    """-3 and NaN rejected too; state still untouched."""
    node = make_node()
    try:
        before = node._timer
        for bad in (-3.0, math.nan, math.inf):
            result = set_hz(node, bad)
            assert not result.successful
        assert node._timer is before
        assert node._values['publish_hz'] == 10.0
    finally:
        destroy(node)


def test_speed_and_turn_accepted_and_used():
    """linear_speed/turn_rate propagate into the node values."""
    node = make_node()
    try:
        p1 = Parameter(name='linear_speed', type_=Parameter.Type.DOUBLE, value=0.2)
        p2 = Parameter(name='turn_rate', type_=Parameter.Type.DOUBLE, value=-0.4)
        results = node.set_parameters([p1, p2])
        assert all(r.successful for r in results)
        assert node._values['linear_speed'] == 0.2
        assert node._values['turn_rate'] == -0.4
    finally:
        destroy(node)
