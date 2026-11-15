# Robotics course workspace (ROS 2)

Учебный workspace курса «Робототехника · ROS 2» (НГУ, https://ros.lms.ci.nsu.ru).
Корень репозитория одновременно является colcon-workspace: пакеты лежат в `src/`.

## Связка

- ОС: Ubuntu 24.04 LTS (WSL2, дистрибуция `Ubuntu`)
- ROS 2: Jazzy (`/opt/ros/jazzy`)
- Gazebo: Harmonic (`ros-jazzy-ros-gz`)
- CI: GitHub Actions, контейнер с ROS 2 Jazzy

## Быстрый старт

```bash
source /opt/ros/jazzy/setup.bash   # underlay
cd ~/ROS
colcon build --symlink-install     # overlay
source install/setup.bash
```

Скачивание course-kit (в `.course-kit/`, в git не попадает):

```bash
mkdir -p .course-kit
curl -fLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1.tar.gz
curl -fLO https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1.tar.gz.sha256.txt
sha256sum -c robotics-course-kit-v1.tar.gz.sha256.txt
tar -xzf robotics-course-kit-v1.tar.gz -C .course-kit
```

Проверка сдачи (сначала свои тесты, потом checker):

```bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

## Структура

- `src/` — ROS-пакеты (`package.xml`, `CMakeLists.txt` / `setup.py`)
- `evidence/prNN/` — отчёты и свидетельства (сдача двумя коммитами: реализация, затем evidence — см. runbook курса)
- `AI_USAGE.md` — декларация об использовании ИИ, обязателен для каждой ПР
- `.github/workflows/ci.yml` — CI курса (появляется с ПР01)
