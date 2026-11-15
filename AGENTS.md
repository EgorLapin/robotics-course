# AGENTS.md — инструкции для ИИ-агентов в этом workspace

## Окружение

- Репозиторий лежит ВНУТРИ WSL2: `Ubuntu` (Ubuntu 24.04), путь `/home/egor/ROS`.
  Из Windows доступен как `\\wsl.localhost\Ubuntu\home\egor\ROS`.
- Linux-команды выполнять через: `wsl.exe -d Ubuntu -- bash -lc '<команда>'`.
- Есть вторая дистрибуция `Ubuntu-26.04` — запасной вариант для связки Lyrical
  (проектная часть курса зафиксирована на Ubuntu 26.04 / ROS 2 Lyrical / Gazebo Jetty;
  базовые ПР01–ПР06 делаются на Jazzy здесь).
- GUI работает через WSLg (RViz, turtlesim — можно запускать, окна появятся на Windows).
- ROS 2 Jazzy: перед любой командой `ros2`/`colcon` в shell выполнять
  `source /opt/ros/jazzy/setup.bash` (в ~/.bashrc после успешной установки).
- GitHub: приватный репозиторий `EgorLapin/robotics-course`, remote HTTPS,
  учёт через `gh` в WSL (`~/.config/gh/hosts.yml`, credential helper `gh auth setup-git`).
  Не коммитить токены, пароли, личные ключи.

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
  во временный файл и `wsl.exe -d Ubuntu -- bash /mnt/c/...`; либо `wsl.exe -d Ubuntu -- bash`
  со stdin через `Get-Content file | wsl.exe` .
- В WSL нет пароля для sudo в неинтерактивной сессии: установку пакетов подтверждает
  пользователь (NOPASSWD включается временно, файл `/etc/sudoers.d/ros-temp`).
- Долгие команды (apt, colcon build) запускать фоном (`run_in_background`) и собирать
  вывод через job_output.
- Git-коммит-мессаги с кириллицей/скобками передавать через файл (`git commit -F file`),
  файл писать ASCII/UTF-8 без BOM (PowerShell 5.1 `-Encoding UTF8` добавляет BOM!).
  Force-push не всегда порождает прогон GitHub Actions — после amend+force проверять
  `gh api repos/EgorLapin/robotics-course/actions/runs?per_page=5`, при отсутствии
  прогона сделать `git commit --allow-empty` + push.
- В WSL стоит `gh` в ~/.local/bin (в PATH ~/.local/bin есть). Локальный course-kit
  лежит в ~/ROS/.course-kit (v1-w10); перед новой неделей сверять `GET /api/course-kit`.
- CI (.github/workflows/ci.yml): шаг checker закомментирован до первой сдачи — включается
  вместе с evidence/prNN; образ osrf/ros:jazzy-desktop-full, Node-шаг до checkout обязателен.
