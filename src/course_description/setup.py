"""Setup for the course_description package (PR06)."""
import glob
import os

from setuptools import setup

package_name = 'course_description'


def data(sub):
    path = os.path.join('share', package_name, os.path.basename(sub))
    return (path, sorted(glob.glob(os.path.join(sub, '*'))))


setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        data('launch'),
        data('urdf'),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Egor Lapin',
    maintainer_email='gdegor2330@gmail.com',
    description='Ackermann vehicle URDF/Xacro description for PR06',
    license='Apache-2.0',
    tests_require=['pytest'],
)
