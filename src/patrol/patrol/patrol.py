# Copyright 2026 Egor Lapin
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""Patrol node for PR04 of the NSU ROS 2 course: parameters drive the command and timer."""

import math

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose

LINEAR_X = 0.5
ANGULAR_Z = 0.3
MAX_LINEAR_X = 0.5
MAX_ANGULAR_Z = 1.0

DEFAULTS = {'linear_speed': 0.5, 'turn_rate': 0.3, 'publish_hz': 10.0}
PARAM_BOUNDS = {'linear_speed': (0.0, 1.0), 'turn_rate': (-1.0, 1.0), 'publish_hz': (1.0, 30.0)}


def clamp(value, low, high):
    """Return value limited to the inclusive [low, high] range."""
    return max(low, min(high, value))


def validate_param(name, value, bounds):
    """Return (ok, reason) for a proposed parameter value (finite number within bounds)."""
    low, high = bounds
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False, 'not a number'
    if not math.isfinite(value):
        return False, 'not a finite number (NaN/inf)'
    if value < low or value > high:
        return False, f'out of range [{low}, {high}]'
    return True, ''


def timer_period(publish_hz):
    """Return the timer period in seconds for a validated publish_hz."""
    return 1.0 / publish_hz


def decide_command(pose, linear_x=LINEAR_X, angular_z=ANGULAR_Z):
    """Return a Twist command from the last pose: zero without pose, patrol circle with it."""
    cmd = Twist()
    if pose is None or math.isnan(pose.x) or math.isnan(pose.y):
        return cmd
    cmd.linear.x = clamp(linear_x, 0.0, MAX_LINEAR_X)
    cmd.angular.z = clamp(angular_z, -MAX_ANGULAR_Z, MAX_ANGULAR_Z)
    return cmd


class PatrolNode(Node):
    """Subscribe to /turtle1/pose; parameters set the Twist and the timer rate."""

    def __init__(self):
        super().__init__('patrol')
        self._last_pose = None
        for name, default in DEFAULTS.items():
            self.declare_parameter(name, default)
        self._values = {}
        for name, bounds in PARAM_BOUNDS.items():
            value = self.get_parameter(name).value
            ok, reason = validate_param(name, value, bounds)
            if ok:
                self._values[name] = float(value)
            else:
                self._values[name] = DEFAULTS[name]
                self.get_logger().warn(
                    f'initial {name}={value} rejected ({reason}), using {DEFAULTS[name]}')
        self._pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._sub = self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        self._timer = None
        self._restart_timer()
        self._param_cb = self.add_on_set_parameters_callback(self._on_set_parameters)

    def _on_pose(self, msg):
        """Store the last pose; the timer does the publishing."""
        self._last_pose = msg

    def _on_timer(self):
        """Publish the command built from parameters and the last pose."""
        cmd = decide_command(
            self._last_pose,
            linear_x=self._values['linear_speed'],
            angular_z=self._values['turn_rate'])
        self._pub.publish(cmd)

    def _on_set_parameters(self, params):
        """Validate every proposed value BEFORE touching timer or state."""
        for p in params:
            if p.name in PARAM_BOUNDS:
                ok, reason = validate_param(p.name, p.value, PARAM_BOUNDS[p.name])
                if not ok:
                    return SetParametersResult(
                        successful=False,
                        reason=f'{p.name}={p.value} rejected: {reason}')
        hz_changed = False
        for p in params:
            if p.name in PARAM_BOUNDS:
                self._values[p.name] = float(p.value)
                if p.name == 'publish_hz':
                    hz_changed = True
        if hz_changed:
            self._restart_timer()
        return SetParametersResult(successful=True)

    def _restart_timer(self):
        """Recreate the timer with period 1/publish_hz; the old timer is cancelled."""
        if self._timer is not None:
            self._timer.cancel()
            self.destroy_timer(self._timer)
        period = timer_period(self._values['publish_hz'])
        self._timer = self.create_timer(period, self._on_timer)
        self.get_logger().info(
            f'timer recreated: period {period:.4f} s (publish_hz={self._values["publish_hz"]})')


def main(args=None):
    """Create the node and spin until Ctrl+C."""
    rclpy.init(args=args)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
