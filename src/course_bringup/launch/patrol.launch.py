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

"""
Bring up the PR05 system: patrol + pose_relay + sensor_listener in a namespace.

One command brings up the /robot_a system:
    ros2 launch course_bringup patrol.launch.py \
        namespace:=robot_a subscriber_reliability:=reliable record:=false
The recorder runs only when record is 'true' (IfCondition, never a plain Python if).
Node topics stay relative; only the cmd_vel output is remapped to the global turtlesim.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Return the PR05 launch description with namespace/QoS/recording arguments."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    subscriber_reliability = LaunchConfiguration('subscriber_reliability')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='robot_a',
            description='Namespace for patrol, pose_relay and sensor_listener'),
        DeclareLaunchArgument(
            'record', default_value='false',
            description="Start 'ros2 bag record' for the sensor topic ('true'/'false')"),
        DeclareLaunchArgument(
            'bag_dir', default_value='bags/pr05',
            description='Output prefix (directory) for the MCAP recording'),
        DeclareLaunchArgument(
            'subscriber_reliability', default_value='reliable',
            description='QoS reliability of sensor_listener: reliable or best_effort'),

        # One turtlesim runs globally (PR02 style).
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
            output='screen',
        ),

        # Relative cmd_vel goes to the global turtlesim; pose stays absolute.
        Node(
            package='patrol',
            executable='patrol',
            name='patrol',
            namespace=namespace,
            output='screen',
            remappings=[('cmd_vel', '/turtle1/cmd_vel')],
        ),

        # Best-effort sensor stream: /robot_a/sensor_pose lives under the namespace.
        Node(
            package='patrol',
            executable='pose_relay',
            name='pose_relay',
            namespace=namespace,
            output='screen',
        ),

        Node(
            package='patrol',
            executable='sensor_listener',
            name='sensor_listener',
            namespace=namespace,
            output='screen',
            parameters=[{'reliability': subscriber_reliability}],
        ),

        # IfCondition gates the recorder; at record:=false the process never starts.
        ExecuteProcess(
            condition=IfCondition(record),
            cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
                 '--topics', ['/', namespace, '/sensor_pose']],
            output='screen',
        ),
    ])
