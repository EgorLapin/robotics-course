# Robotics course workspace (ROS 2)

Учебный workspace курса «Робототехника · ROS 2» (НГУ, https://ros.lms.ci.nsu.ru).
Корень репозитория одновременно является colcon-workspace: пакеты лежат в `src/`.

## Связка

- ОС: Ubuntu 24.04 LTS (WSL2, дистрибуция `Ubuntu`)
- ROS 2: Jazzy (`/opt/ros/jazzy`)
- Gazebo: Harmonic (`ros-jazzy-ros-gz`)
- CI: GitHub Actions, контейнер `osrf/ros:jazzy-desktop-full`

## Порядок запуска (ПР01: окружение и первый граф)

В каждом терминале:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16        # домен исправного опыта; для разрыва — 17
```

- A (симулятор): `ros2 run turtlesim turtlesim_node`
- B (управление): `ros2 run turtlesim turtle_teleop_key` (стрелки, фокус в этом терминале)
- C (наблюдение):

```bash
ros2 node list --no-daemon --spin-time 5
ros2 topic list -t
ros2 node info /turtlesim
POSE_TYPE=$(ros2 topic type /turtle1/pose)   # Jazzy: turtlesim/msg/Pose
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose                  # ~62,5 Гц, остановка Ctrl+C
```

Разрыв связи: перезапустить B с `ROS_DOMAIN_ID=17` — в домене 17 виден только
`/teleop_turtle`, `ros2 topic echo /turtle1/pose "$POSE_TYPE" --once` завершается
по таймауту (exit=124). Возврат B в домен 16 восстанавливает позу (exit=0).
Наблюдения — в `evidence/pr01/`.

## Порядок запуска (ПР02: пакет turtle_bringup и launch)

```bash
colcon build --symlink-install --packages-select turtle_bringup   # терминал сборки
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py    # терминал A: окно turtlesim, Ctrl+C — остановка
# терминал B: ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 1.0}, angular: {z: 0.5}}"
# терминал C: ros2 topic info /turtle1/cmd_vel --verbose (pub+sub), /cmd_vel — pub 0 sub без подписчика
```

Опыт имени: издатель в `/cmd_vel` виден (`Publisher count: 1`), но подписчиков у него нет;
то же сообщение в `/turtle1/cmd_vel` двигает черепаху. Подробности — `evidence/pr02/commands.md`.

## Порядок запуска (ПР03: нода patrol)

```bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
python3 -m pytest src/patrol/test          # чистые тесты decide_command
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py   # терминал A
# терминал B (правильный запуск — remap имени):
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
# без remap нода публикует в /cmd_vel — издатель виден, черепаха стоит (см. demo.md)
# терминал C: ros2 topic hz /turtle1/cmd_vel   # ~10 Гц
```

## Порядок запуска (ПР04: параметры patrol)

```bash
colcon build --symlink-install --packages-select patrol && source install/setup.bash
python3 -m pytest src/patrol/test          # 25 passed (валидация + живой узел + команда)
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py   # терминал A
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel   # терминал B
# терминал C:
ros2 param get /patrol publish_hz          # Double 10.0
ros2 param set /patrol publish_hz 0.0      # rejected: out of range [1.0, 30.0] — узел жив
ros2 param set /patrol publish_hz 5.0      # поток падает до 5 Гц (period 0.2000 s)
```

Сборка собственных пакетов (с ПР02):

```bash
colcon build --symlink-install     # overlay из корня workspace
source install/setup.bash
```

Скачивание course-kit (в `.course-kit/`, в git не попадает; ревизия v1-w10, sha256 3b11d37c…:

```bash
mkdir -p .course-kit
curl -fLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w10-3b11d37c4d46.tar.gz
curl -fLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w10-3b11d37c4d46.tar.gz.sha256.txt
sha256sum -c robotics-course-kit-v1-w10-3b11d37c4d46.tar.gz.sha256.txt
tar -xzf robotics-course-kit-v1-w10-3b11d37c4d46.tar.gz -C .course-kit
```

Проверка сдачи (сначала свои тесты, потом checker):

```bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .   # номер текущей ПР
```

## Порядок запуска (ПР05: QoS датчика и namespace robot_a)

Система: patrol + pose_relay (публикует `/turtle1/pose` в относительный
`sensor_pose` с профилем BEST_EFFORT) + sensor_listener (профиль подписчика
задаётся параметром). Неймспейс и запись — аргументы launch:

```bash
# Дефект: reliable-подписчик не получает ничего с best-effort издателя
ros2 launch course_bringup patrol.launch.py namespace:=robot_a subscriber_reliability:=reliable record:=false
timeout 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once   # тишина, exit 124

# Исправление: подписчик best_effort — живой поток и MCAP-запись (record через IfCondition)
ros2 launch course_bringup patrol.launch.py namespace:=robot_a subscriber_reliability:=best_effort record:=true bag_dir:=evidence/pr05/bag

# Реплей того же bag с наложением QoS (evidence тот же, что в живом эксперименте)
ros2 bag play evidence/pr05/bag --qos-profile-overrides-path config/qos-overrides.yaml
```

Свидетельства: `evidence/pr05/qos-before.txt` (топик виден, 0 сообщений),
`qos-after.txt` (живой поток + `ros2 bag info`: 1 топик, 3141 сообщение),
`bag-metadata.yaml` (копия metadata.yaml bag-а), `tests.txt`.

## Порядок запуска (ПР06: модель Ackermann, tf2 и QoS преобразований)

`course_description` — описание робота из course-kit SDF (только размеры, без
плагинов Gazebo): `urdf/vehicle.urdf.xacro` с xacro-параметрами корпуса, колеи и
колеса (REP-103: x вперёд, y влево, z вверх; колёса крутятся вокруг +y).

```bash
# развернуть Xacro и проверить структуру
xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf

# дерево tf2: фиксированные звенья камеры/лидара/IMU публикуются сразу
ros2 launch course_description description.launch.py            # + rviz:=true для RViz
ros2 run tf2_ros tf2_echo base_link lidar_link
ros2 run tf2_tools view_frames

# QoS преобразований: /tf_static = RELIABLE + TRANSIENT_LOCAL (поздний
# подписчик получает кадры), volatile-подписчик не получает ничего
ros2 topic info /tf_static --verbose
timeout 4 ros2 topic echo /tf_static --once --qos-durability transient_local --qos-reliability reliable
timeout 4 ros2 topic echo /tf_static --once --qos-durability volatile --qos-reliability reliable   # exit 124
```

Свидетельства: `evidence/pr06/frames.md` (владельцы преобразований),
`model-check.txt` (xacro + check_urdf + тесты), `tf-qos.txt` (профиль /tf_static
и позднее чтение), `report.json`.

## Структура

- `src/` — ROS-пакеты (`package.xml`, `CMakeLists.txt` / `setup.py`)
- `evidence/prNN/` — отчёты и свидетельства (сдача двумя коммитами: реализация, затем evidence — см. runbook курса)
- `AI_USAGE.md` — декларация об использовании ИИ, обязателен для каждой ПР
- `.github/workflows/ci.yml` — CI курса
