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

"""Tests for the pure decide_command() function of the patrol node (PR03)."""

import math

from patrol.patrol import decide_command
from turtlesim.msg import Pose


def make_pose(x=5.5, y=5.5, theta=0.0):
    pose = Pose()
    pose.x = x
    pose.y = y
    pose.theta = theta
    return pose


def test_no_pose_returns_zero_command():
    cmd = decide_command(None)
    assert cmd.linear.x == 0.0
    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0
    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0
    assert cmd.angular.z == 0.0


def test_normal_pose_returns_patrol_command():
    cmd = decide_command(make_pose())
    assert cmd.linear.x == 0.5
    assert cmd.angular.z == 0.3
    assert cmd.linear.y == 0.0 and cmd.linear.z == 0.0


def test_nan_pose_is_treated_as_missing():
    pose = make_pose()
    pose.x = float('nan')
    cmd = decide_command(pose)
    assert cmd.linear.x == 0.0
    assert cmd.angular.z == 0.0


def test_command_is_limited():
    cmd = decide_command(make_pose(), linear_x=2.0, angular_z=-5.0)
    assert cmd.linear.x == 0.5
    assert cmd.angular.z == -1.0
    cmd = decide_command(make_pose(), linear_x=-1.0, angular_z=5.0)
    assert cmd.linear.x == 0.0
    assert cmd.angular.z == 1.0


def test_pose_far_from_start_still_patrols():
    # Патруль — круг: координаты не влияют на команду, важен сам факт позы.
    cmd = decide_command(make_pose(x=1.0, y=10.0, theta=math.pi))
    assert cmd.linear.x == 0.5
    assert cmd.angular.z == 0.3
