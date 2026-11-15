# Декларация использования ИИ

Файл обязателен для каждой ПР. Для следующих ПР добавляю разделы, сохраняя предыдущие.

## PR01

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: DeepSeek (агентная сборка qwen3.8-flash-next в DeepSeek Harness).
- Среда или интерфейс агента: DeepSeek Harness (веб-GUI), агент работает в этом workspace
  через PowerShell + WSL2 (команды выполняются в Ubuntu от имени пользователя).
- Затронутые компоненты: установка ROS 2 Jazzy (скрипт на основе гайда курса, выбор зеркала
  apt из-за сломанного TLS packages.ros.org); прогон опытов ПР01 (turtlesim, teleop,
  замер hz, разрыв доменов 16/17); оформление `evidence/pr01/*` (graph.md из сырых логов,
  environment.json), README, CI workflow, report.json.
- Характер помощи: запуск и логирование команд по шагам условия, расшифровка выводов
  (таймауты discovery ros2cli, коды возврата), подготовка текстов отчёта по шаблону.
  Сценарий опыта, выбор доменов и объяснение причины разбора — по условию работы;
  объяснение в graph.md составлено по наблюдаемым данным, а не скопировано.
- Как результат был проверен независимо: все наблюдения — сырые логи терминалов
  (pose-broken.txt exit=124, pose-fixed.txt exit=0, hz-окна 62,49-62,52, node list в обоих
  доменах); environment.json прошёл `python3 -m json.tool`; комплект — локальный
  `check_practice.py PR01` и зелёный CI на evidence-коммите; опыты воспроизводимы
  повторным запуском команд из README и graph.md.

## PR02

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: DeepSeek (агентная сборка qwen3.8-flash-next в DeepSeek Harness).
- Среда или интерфейс агента: DeepSeek Harness (веб-GUI), команды выполняются в WSL2 Ubuntu
  в этом workspace.
- Затронутые компоненты: генерация пакета turtle_bringup (`ros2 pkg create`), launch-файл
  `sim.launch.py` и правка `setup.py` (установка launch-ресурсов), прогон опытов (launch,
  Twist-команды, опыт с `/cmd_vel`), оформление `evidence/pr02/*` (commands.md, types.md,
  cli-raw.txt, report.json), README и CI workflow.
- Характер помощи: выполнение команд условия, сбор и расшифровка логов (`topic info
  --verbose`, коды завершения), диагностика flake8-замечания (порядок импортов в setup.py),
  тексты разборов «до/сбой/после» составлены по фактическим выводам.
- Как результат был проверен независимо: живой прогон в WSL2 (поза до/после команд
  зафиксирована: x 5.544→6.509 при верном имени; подписчиков 0 при /cmd_vel; движение при
  исправлении имени; остановка launch — «process has finished cleanly»); `colcon test`
  зелёный (3 теста, 0 ошибок); `py_compile` launch-файла; локальный
  `check_practice.py PR02` и зелёный CI на evidence-коммите.

## PR03

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: DeepSeek (агентная сборка qwen3.8-flash-next в DeepSeek Harness).
- Среда или интерфейс агента: DeepSeek Harness (веб-GUI), команды — в WSL2 Ubuntu этого
  workspace.
- Затронутые компоненты: код ноды `patrol` (`src/patrol/patrol/patrol.py` — подписка,
  таймер, чистая `decide_command`), тесты `src/patrol/test/test_decide_command.py`,
  прогон опытов (сломанный запуск, remap, hz, остановка), тексты `evidence/pr03/*`
  (demo.md по сырым логам, tests.txt, raw-*.txt), report.json, README, CI workflow.
- Характер помощи: написание каркаса по паттерну лекции, отладка завершения по SIGINT
  (в Jazzy rclpy сам выключает контекст — нужен `ExternalShutdownException`), замер и
  расшифровка hz-окон, формулировки «до/сбой/после» по фактическим выводам терминала.
  Сценарий дефекта (относительный cmd_vel) и разбор ролей init/spin/callback заданы
  условием работы.
- Как результат был проверен независимо: поведение подтверждено живыми прогонами —
  без remap Publisher 1 / Subscription 0 и неподвижная поза; с remap позы меняются каждые
  4 с, hz ≈10,1–10,5 Гц; после SIGINT linear/angular velocity = 0. Тесты: pytest 7 passed
  (включая негативные), colcon test 0 failures. Логи без правок — evidence/pr03/raw-*.txt;
  локальный `check_practice.py PR03` и зелёный CI на evidence-коммите.

## PR04

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).
- Модель и версия: DeepSeek (агентная сборка qwen3.8-flash-next в DeepSeek Harness).
- Среда или интерфейс агента: DeepSeek Harness (веб-GUI), команды — в WSL2 Ubuntu этого
  workspace.
- Затронутые компоненты: `src/patrol/patrol/patrol.py` (объявление параметров, колбэк
  `add_on_set_parameters_callback` с валидацией до изменения состояния, пересоздание
  таймера), тесты `test_parameters.py`/`test_param_node.py`, прогоны опытов (дефект с
  нулём, отклонение, смена 10→5 Гц, сервис /clear и действие rotate_absolute),
  тексты `evidence/pr04/*`, report.json, README, CI workflow.
- Характер помощи: набросок кода по условию (параметры/границы/порядок «проверка до
  состояния»), отладка измерения потока в WSL2 (ros2 topic hz и подписки ловили
  discovery-разрывы — поставлен собствен зонд с прогревом, порядок прогонов подобран на
  чистые окна), расшифровка отказа ZeroDivisionError, формулировки «до/сбой/после» по
  фактическим логам. Сценарий дефекта и критерии заданы условием работы.
- Как результат был проверен независимо: живой прогон на свежей загрузке WSL — с
  отключённой проверкой `publish_hz=0.0` роняет узел (ZeroDivisionError, pgrep пуст);
  с проверкой 0 и -3.0 отклоняются службой параметров, `ros2 param get` = 10.0, узел жив;
  `set 5.0` — лог `period 0.1000 -> 0.2000` и зонд +5 сообщ/с вместо +10; pytest 25
  passed (включая узловые тесты «0 отклонён, таймер не тронут» и «один таймер»),
  colcon test 0 failures; локальный `check_practice.py PR04` и зелёный CI на
  evidence-коммите.
