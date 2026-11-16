"""Structure checks for the PR06 Ackermann model (xacro -> URDF)."""
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

XACRO = Path(__file__).parents[1] / 'urdf' / 'vehicle.urdf.xacro'


@pytest.fixture(scope='module')
def robot():
    """Expand the xacro once and return the URDF root element."""
    out = subprocess.run(['xacro', str(XACRO)], capture_output=True, text=True, check=True)
    return ET.fromstring(out.stdout)


def joints_by_child(root):
    return {j.find('child').get('link'): j for j in root.findall('joint')}


def test_fixed_sensors_parent_is_base_link(robot):
    joints = joints_by_child(robot)
    for name in ('camera_link', 'lidar_link', 'imu_link'):
        assert joints[name].find('parent').get('link') == 'base_link', name


def test_links_present(robot):
    names = {lnk.get('name') for lnk in robot.findall('link')}
    expected = {
        'base_link', 'camera_link', 'lidar_link', 'imu_link',
        'front_left_knuckle', 'front_right_knuckle',
        'front_left_wheel', 'front_right_wheel',
        'rear_left_wheel', 'rear_right_wheel',
    }
    assert expected <= names


def test_wheel_chain(robot):
    joints = joints_by_child(robot)
    for side in ('left', 'right'):
        steer = joints[f'front_{side}_knuckle']
        assert steer.get('type') == 'revolute'
        assert steer.find('parent').get('link') == 'base_link'
        assert joints[f'front_{side}_wheel'].find('parent').get('link') == f'front_{side}_knuckle'
        assert joints[f'rear_{side}_wheel'].find('parent').get('link') == 'base_link'


def test_dimensions_are_si_from_kit(robot):
    body = robot.find("link[@name='base_link']")
    size = body.find('visual/geometry/box').get('size').split()
    assert size == ['1.05', '0.52', '0.22']
    wheel = robot.find("link[@name='front_left_wheel']")
    cyl = wheel.find('visual/geometry/cylinder')
    assert cyl.get('radius') == '0.12' and cyl.get('length') == '0.07'


def test_inertias_physical(robot):
    for link in robot.findall('link'):
        inertial = link.find('inertial')
        assert inertial is not None, link.get('name')
        mass = float(inertial.find('mass').get('value'))
        assert mass > 0.0
        m = {n: float(inertial.find('inertia').get(n)) for n in ('ixx', 'iyy', 'izz')}
        assert m['ixx'] + m['iyy'] >= m['izz'] - 1e-9
        assert m['ixx'] + m['izz'] >= m['iyy'] - 1e-9
        assert m['iyy'] + m['izz'] >= m['ixx'] - 1e-9


@pytest.mark.skipif(shutil.which('check_urdf') is None, reason='urdfdom-tools not installed')
def test_check_urdf_accepts():
    urdf = subprocess.run(['xacro', str(XACRO)], capture_output=True, text=True, check=True)
    res = subprocess.run(['check_urdf', '-'], input=urdf.stdout, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
