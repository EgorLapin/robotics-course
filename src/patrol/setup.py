from setuptools import find_packages, setup

package_name = 'patrol'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Egor Lapin',
    maintainer_email='gdegor2330@gmail.com',
    description='Patrol node: last pose in, Twist out (PR03, NSU ROS 2 course)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'patrol = patrol.patrol:main'
        ],
    },
)
