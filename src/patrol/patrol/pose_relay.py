# Copyright 2026 Egor Lapin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sensor relay for PR05: forward the turtlesim pose as a best-effort stream."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSReliabilityPolicy
from turtlesim.msg import Pose

# A real sensor is best effort: a stale sample is worse than no sample.
SENSOR_QOS = QoSProfile(
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    durability=QoSDurabilityPolicy.VOLATILE,
)


def reliability_from_str(name):
    """Return the QoS reliability policy for 'reliable' or 'best_effort'."""
    normalized = str(name).strip().lower().replace('-', '_').replace(' ', '_')
    if normalized == 'reliable':
        return QoSReliabilityPolicy.RELIABLE
    if normalized == 'best_effort':
        return QoSReliabilityPolicy.BEST_EFFORT
    raise ValueError(f'unknown reliability profile: {name!r}')


class PoseRelayNode(Node):
    """Read /turtle1/pose and publish it on the relative topic sensor_pose."""

    def __init__(self):
        super().__init__('pose_relay')
        self._pub = self.create_publisher(Pose, 'sensor_pose', SENSOR_QOS)
        self._sub = self.create_subscription(Pose, '/turtle1/pose', self._forward, 10)
        self.get_logger().info('pose_relay: /turtle1/pose -> sensor_pose (best effort)')

    def _forward(self, msg):
        """Forward the received pose unchanged; the QoS profile does the rest."""
        self._pub.publish(msg)


def main(args=None):
    """Create the relay node and spin until Ctrl+C."""
    rclpy.init(args=args)
    node = PoseRelayNode()
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
