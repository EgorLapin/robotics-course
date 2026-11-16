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

"""Sensor listener for PR05: subscribe to sensor_pose with QoS from a parameter."""

# With parameter reliability:=reliable this listener is INCOMPATIBLE with the
# best-effort pose_relay publisher: the topic stays visible in ros2 topic list
# but no sample is ever delivered. With reliability:=best_effort the same node
# receives the stream.

from patrol.pose_relay import reliability_from_str
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSProfile
from turtlesim.msg import Pose


def make_subscriber_qos(reliability_name):
    """Return a volatile keep_last(10) QoS profile with the given reliability."""
    return QoSProfile(
        history=QoSHistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=reliability_from_str(reliability_name),
        durability=QoSDurabilityPolicy.VOLATILE,
    )


class SensorListenerNode(Node):
    """Subscribe to the relative topic sensor_pose and count deliveries."""

    def __init__(self):
        super().__init__('sensor_listener')
        self.declare_parameter('reliability', 'best_effort')
        self._reliability = str(self.get_parameter('reliability').value)
        self._count = 0
        qos = make_subscriber_qos(self._reliability)
        self._sub = self.create_subscription(Pose, 'sensor_pose', self._on_pose, qos)
        self.get_logger().info(f'sensor_listener: subscribing to sensor_pose with '
                               f'reliability={self._reliability}')

    def _on_pose(self, msg):
        """Count one delivered sample; log every tenth."""
        self._count += 1
        if self._count % 10 == 1:
            self.get_logger().info(
                f'sensor_listener: sample #{self._count} x={msg.x:.3f} y={msg.y:.3f}')


def main(args=None):
    """Create the listener node and spin until Ctrl+C."""
    rclpy.init(args=args)
    node = SensorListenerNode()
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
