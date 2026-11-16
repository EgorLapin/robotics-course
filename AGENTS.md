# AGENTS.md — инструкции для ИИ-агентов в этом workspace

## Окружение

- Репозиторий лежит ВНУТРИ WSL2: `Ubuntu` (Ubuntu 24.04), путь `/home/egor/ROS`.
  Из Windows доступен как `\\wsl.localhost\Ubuntu\home\egor\ROS`.
- Linux-команды выполнять через: `wsl.exe -d Ubuntu -- bash -lc '<команда>'`.
- Дистрибуция `Ubuntu-26.04` (запасной вариант под связку Lyrical: проектная часть
  курса — Ubuntu 26.04 / ROS 2 Lyrical / Gazebo Jetty) удалена 2026-11-16 по просьбе
  пользователя: `wsl --unregister Ubuntu-26.04`, внутри ничего не было, кроме
  свежего образа. К освободившимся ~2.3 ГБ поставить заново при необходимости:
  `wsl --install -d Ubuntu-26.04` (инструкция установки ROS 2 Lyrical — та же,
  что в ~/setup_ros_jazzy.sh, с зеркалом apt при необходимости).
- GUI работает через WSLg (RViz, turtlesim — можно запускать, окна появятся на Windows).
  В неинтерактивной сессии (`wsl.exe -d X -- bash -c`) переменных GUI нет; в login-шелле
  (`bash -lc`) они есть: `DISPLAY=:0`, `WAYLAND_DISPLAY=wayland-0`.
- ROS 2 Jazzy: установлен в `/opt/ros/jazzy` (502 МБ, 329 пакетов), строка
  `source /opt/ros/jazzy/setup.bash` в `~/.bashrc` (строка 118). Не добавлять в .bashrc
  другие дистрибутивы.
- GitHub: приватный репозиторий `EgorLapin/robotics-course`, remote HTTPS,
  учёт через `gh` в WSL (`~/.config/gh/hosts.yml`, credential helper `gh auth setup-git`).
  Не коммитить токены, пароли, личные ключи.

## Установка ROS 2 (выполнена 2026-11-16) — что важно знать

- Установочный скрипт: `~/setup_ros_jazzy.sh`, лог: `~/ros_install.log`.
  Ставились `ros-jazzy-desktop ros-dev-tools ros-jazzy-ros-gz ros-jazzy-rviz2
  python3-colcon-common-extensions python3-rosdep` (1407 пакетов, 966 МБ архивов).
- **Официальный `https://packages.ros.org` сломан по TLS**: с 2026-11-13 OSUOSL отдаёт
  сертификат `CN=*.osuosl.org`, не покрывающий `packages.ros.org` → apt падает на
  проверке подписи индекса. По http тот же хост жив, но ~45 КБ/с. Это проблема апстрима,
  не локальная и не из-за VPN.
- Поэтому APT-источник указывает на зеркало: `/etc/apt/sources.list.d/ros2.list` =
  `deb [signed-by=/etc/apt/keyrings/ros2.gpg] https://mirrors.aliyun.com/ros2/ubuntu noble main`
  (2–3 МБ/с; запасные: mirrors.tuna.tsinghua.edu.cn, mirrors.ustc.edu.cn).
  Подлинность обеспечивает GPG: отпечаток ключа `C1CF 6E31 E6BA DE88 68B1 72B4 F42ED6FB AB17 C654`
  (Open Robotics), `InRelease` зеркала проверен против него. Ключ скачан с
  `raw.githubusercontent.com/ros/rosdistro/master/ros.key`.
- rosdep инициализирован, кэш обновлён (`~/.ros/rosdep/sources.cache`).
- Проверено работает: talker(C++)→listener(py), turtlesim + движение по `/turtle1/cmd_vel`,
  `colcon build --symlink-install` на тестовом пакете, headless `gz sim -s` (Harmonic 8.15.0).
- Особенности discovery в WSL2: кэш `ros2 daemon` может не увидеть ноды, запущенные
  до его старта — при «пустом» `ros2 topic list` сделать `ros2 daemon stop && ros2 daemon start`.
  Флаг `--no-daemon` есть у `ros2 topic list/echo`, но НЕ у `ros2 service call` / `ros2 topic pub`.
- VPN (туннель `happ-default-tun` + Netbird `wt0`) режет скорость до внешних хостов и
  ломает резолв `*.mycorpus.space` (DNS Netbird `100.107.234.218`). Для больших скачиваний
  выключать; сам сайт курса `ros.lms.ci.nsu.ru` доступен и через него.

## Правила курса (ros.lms.ci.nsu.ru) — важно для сдач

- Порядок команд: `colcon build --symlink-install` → `colcon test --event-handlers console_direct+`
  → `colcon test-result --verbose` → `python3 .course-kit/v1/tools/check_practice.py PRxx --submission .`
- Сдача = ДВА коммита: (1) реализация, (2) отдельно `evidence/prNN/` + `AI_USAGE.md`.
  В `report.json → commit` — полный SHA коммита РЕАЛИЗАЦИИ; проверяется зелёный CI
  на evidence-коммите.
- `AI_USAGE.md` обязателен для каждой ПР (даже «ИИ не использовался»). При работе агента
  — заполнять таблицу: модель, инструмент, компонент, характер помощи, как проверено.
  В `report.json` поле `ai_used` должно соответствовать записи.
- `report.json` создавать из `.course-kit/v1/practices/templates/`, заменить все
  `replace-with-*`, перенести трудоёмкость из условия, добавить claims из манифеста ПР.
- Course-kit: `.course-kit/` и скачанные архивы в .gitignore; VERSION и SHA-256
  архива фиксировать в report.json и в CI (immutable URL из `GET /api/course-kit`).
- В CI нельзя смешивать ROS-дистрибутивы; образ и путь setup.bash должны соответствовать
  выбранной связке (здесь — Jazzy). `fetch-depth: 0` для checkout обязателен.
- Не коммитить: `build/`, `install/`, `log/`, `.course-kit/`, bag-файлы, секреты.

## Приёмы работы из агента (проверено на этой машине)

- Инструмент `write`/`edit` не работает поверх `\\wsl.localhost` (rename не поддерживается).
  Текст с кириллицей переносить так: запись через `write` во временный файл Windows
  (`%TEMP%`), затем `Copy-Item` на UNC-путь. ASCII-строки можно писать
  `[System.IO.File]::WriteAllText(unc, text, UTF8-no-BOM)` из PowerShell 5.1.
- НЕ гонять heredoc/многострочный bash через `wsl.exe -- bash -c` внутри PowerShell —
  кавычки ломаются. Варианты: одна простая команда в одинарных кавычках; либо скрипт
  во временный файл и `wsl.exe -d Ubuntu -- bash /home/egor/...`; либо `wsl.exe -d Ubuntu -- bash`
  со stdin через `Get-Content file | wsl.exe` .
- В PowerShell 5.1 нет `??`, `-Encoding utf8NoBOM`; `$(` внутри двойных кавычек раскрывается
  PowerShell'ом, а не bash — для циклов/подстановки писать скрипт-файл.
- В WSL нет пароля для sudo в неинтерактивной сессии: установку пакетов подтверждает
  пользователь (NOPASSWD включается временно, файл `/etc/sudoers.d/ros-temp`).
- Долгие команды (apt, colcon build) запускать фоном (`run_in_background`) и собирать
  вывод через job_output; длинный трон иначе ловит `Request timed out` на стороне клиента API.
- Git-коммит-мессаги с кириллицей/скобками передавать через файл (`git commit -F file`),
  файл писать ASCII/UTF-8 без BOM (PowerShell 5.1 `-Encoding UTF8` добавляет BOM!).
  Force-push не всегда порождает прогон GitHub Actions — после amend+force проверять
  `gh api repos/EgorLapin/robotics-course/actions/runs?per_page=5`, при отсутствии
  прогона сделать `git commit --allow-empty` + push.
- В WSL стоит `gh` в ~/.local/bin (в PATH ~/.local/bin есть). Локальный course-kit
  лежит в ~/ROS/.course-kit (v1-w10); перед новой неделей сверять `GET /api/course-kit`.
- CI (.github/workflows/ci.yml): шаг checker закомментирован до первой сдачи — включается
  вместе с evidence/prNN; образ osrf/ros:jazzy-desktop-full, Node-шаг до checkout обязателен.
