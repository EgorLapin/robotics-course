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

"""Pure tests for the QoS helpers used by pose_relay and sensor_listener (PR05)."""

from patrol.pose_relay import reliability_from_str
from patrol.pose_relay import SENSOR_QOS
from patrol.sensor_listener import make_subscriber_qos
import pytest
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy


def test_reliability_from_str_accepts_both_profiles():
    assert reliability_from_str('reliable') is QoSReliabilityPolicy.RELIABLE
    assert reliability_from_str('best_effort') is QoSReliabilityPolicy.BEST_EFFORT


def test_reliability_from_str_normalizes_spelling():
    assert reliability_from_str('Best-Effort') is QoSReliabilityPolicy.BEST_EFFORT
    assert reliability_from_str(' RELIABLE ') is QoSReliabilityPolicy.RELIABLE


def test_reliability_from_str_rejects_garbage():
    with pytest.raises(ValueError):
        reliability_from_str('best effort only sometimes')
    with pytest.raises(ValueError):
        reliability_from_str(None)


def test_sensor_qos_is_best_effort_volatile():
    assert SENSOR_QOS.reliability is QoSReliabilityPolicy.BEST_EFFORT
    assert SENSOR_QOS.durability is QoSDurabilityPolicy.VOLATILE
    assert SENSOR_QOS.depth == 10


def test_subscriber_qos_matches_requested_reliability():
    reliable = make_subscriber_qos('reliable')
    best = make_subscriber_qos('best_effort')
    assert reliable.reliability is QoSReliabilityPolicy.RELIABLE
    assert best.reliability is QoSReliabilityPolicy.BEST_EFFORT
    # Both are volatile keep_last(10): only reliability toggles in the experiment.
    for qos in (reliable, best):
        assert qos.durability is QoSDurabilityPolicy.VOLATILE
        assert qos.depth == 10
