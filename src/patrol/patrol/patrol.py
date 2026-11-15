# Copyright 2026 Egor Lapin
#
# Licensed under the Apache License, Version 2.0 (the "License");

"""Patrol node for PR03 of the NSU ROS 2 course: last pose in, Twist command out."""

import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose

LINEAR_X = 0.5
ANGULAR_Z = 0.3
MAX_LINEAR_X = 0.5
MAX_ANGULAR_Z = 1.0


def clamp(value, low, high):
    """Return value limited to the inclusive [low, high] range."""
    return max(low, min(high, value))


def decide_command(pose, linear_x=LINEAR_X, angular_z=ANGULAR_Z):
    """Return a Twist command from the last pose: zero without pose, patrol circle with it."""
    cmd = Twist()
    if pose is None or math.isnan(pose.x) or math.isnan(pose.y):
        return cmd
    cmd.linear.x = clamp(linear_x, 0.0, MAX_LINEAR_X)
    cmd.angular.z = clamp(angular_z, -MAX_ANGULAR_Z, MAX_ANGULAR_Z)
    return cmd


class PatrolNode(Node):
    """Subscribe to /turtle1/pose, publish the patrol command on a 0.1 s timer."""

    def __init__(self):
        super().__init__('patrol')
        self._last_pose = None
        self._pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._sub = self.create_subscription(Pose, '/turtle1/pose', self._on_pose, 10)
        self._timer = self.create_timer(0.1, self._on_timer)
        self.get_logger().info('patrol started, waiting for /turtle1/pose')

    def _on_pose(self, msg):
        """Store the last pose; the timer does the publishing."""
        self._last_pose = msg

    def _on_timer(self):
        """Publish the command chosen from the last pose."""
        self._pub.publish(decide_command(self._last_pose))


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
