# ПР02 · commands.md — Терминал, пакет и запуск turtlesim

Среда: WSL2 Ubuntu 24.04, ROS 2 Jazzy, `ROS_DOMAIN_ID=16` (тот же домен, что в ПР01).
Все терминалы начинают с `source /opt/ros/jazzy/setup.bash`; workspace-накладка —
`source install/setup.bash` из корня репозитория.

## Шаг 1 · Корень работы и терминал

```
$ pwd
/home/egor/ROS
$ ls -a | head -14
.  ..  AGENTS.md  AI_USAGE.md  build  .course-kit  evidence  .git  .github  .gitignore  install  log  README.md  src
$ mkdir -p src evidence/pr02
$ printenv ROS_DISTRO ROS_DOMAIN_ID
jazzy
16
$ ros2 pkg prefix turtlesim
/opt/ros/jazzy
```

Назначение: убедиться, что репозиторий = корень workspace (`pwd`), найти установленный
пакет turtlesim (`ros2 pkg prefix` — путь к **установленному** пакету, а не к текущему
каталогу: две разные «точки отсчёта»). Результат: `/opt/ros/jazzy` — turtlesim из дистрибутива.

## Три разобранные команды Linux

### 1. `colcon build ... 2>&1 | tee evidence/pr02/build-empty.txt`

- Точная команда (из шага 2):
  `colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build-empty.txt`
- Назначение: собрать пакет и **одновременно** показать сборку в терминале и сохранить её
  в файл. `2>&1` перенаправляет stderr в stdout, чтобы ошибки сборки попали в тот же поток,
  что и обычный вывод; `tee` читает stdout и пишет его и на экран, и в файл.
  Предшествующий `set -o pipefail` сохраняет ненулевой код возврата colcon, иначе код tee
  (0) скрыл бы провал сборки.
- Мой результат: `Summary: 1 package finished [3.41s]`, файл лога 4 строки;
  содержимое — в `evidence/pr02/build-empty.txt` и `build.txt`.

### 2. `source /opt/ros/jazzy/setup.bash` (и `source install/setup.bash`)

- Точная команда: `source /opt/ros/jazzy/setup.bash`
- Назначение: выполнить скрипт **в текущем** оболочечном процессе. Скрипт меняет
  переменные среды именно этого терминала (`AMENT_PREFIX_PATH`, `PYTHONPATH`, `PATH`,
  `ROS_DISTRO`), поэтому ROS-команды начинают видеть пакеты.
- Мой результат: `printenv ROS_DISTRO` → `jazzy`; после второй строки
  `ros2 pkg prefix turtle_bringup` → `/home/egor/ROS/install/turtle_bringup` — накладка
  workspace добавлена поверх дистрибутива.

### 3. `grep` по длинному логу

- Точная команда: `grep -E 'sending signal|finished cleanly' /tmp/pr02_launch.log`
  (для длинных логов удобнее `less /tmp/pr02_launch.log`, выход — `q`).
- Назначение: найти в потоке лога строки, доказывающие событие, не перечитывая всё глазами.
- Мой результат:
  `[INFO] [turtlesim_node-1]: sending signal 'SIGINT' to process[turtlesim_node-1]` и
  `process has finished cleanly` — запуск корректно завершил ноду по Ctrl+C.

### `>` против `|`

`>` перенаправляет вывод команды в **файл**: `ros2 node list > nodes.txt` пишет stdout в
nodes.txt, **заменяя** его прежнее содержимое (дописывает `>>`), и на экран ничего не
попадает. `|` соединяет вывод команды с **вводом** следующей команды:
`colcon build 2>&1 | tee log.txt` — это поток между двумя процессами, файл появляется как
побочный эффект tee, а сборка по-прежнему видна на экране. Это разные получатели: файл
против другой программы.

### `source` против запуска новой программы

`source setup.bash` выполняется в текущей оболочке: изменённые им переменные среды
остаются после возврата в приглашение (поэтому `ros2` потом находит пакеты). Запуск
программы (`python3 script.py`, `./my_node`, даже `bash setup.bash`) — отдельный процесс-
ребёнок: его изменения среды умирают вместе с ним, в терминале ничего не меняется.
Поэтому ROS обязательно *source*-ят, а не запускают.

## Шаг 2–3 · Сборка и запуск launch

```
$ ros2 pkg create --build-type ament_python --license Apache-2.0 turtle_bringup \
    --dependencies launch launch_ros turtlesim
$ colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build-empty.txt
Finished <<< turtle_bringup [3.04s]        # лог: evidence/pr02/build-empty.txt

# (после добавления launch/sim.launch.py и правки setup.py)
$ colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build.txt
Finished <<< turtle_bringup [2.48s]        # лог: evidence/pr02/build.txt
```

### Файл на диске ≠ установленный ресурс ≠ запущенная нода

```
$ ls src/turtle_bringup/launch/          # файл на диске — пока просто текст
sim.launch.py
$ ros2 pkg prefix turtle_bringup         # где установленный пакет
/home/egor/ROS/install/turtle_bringup
$ ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
sim.launch.py                            # появился только ПОСЛЕ colcon build
$ ros2 node list --no-daemon --spin-time 5
/turtlesim                               # а это уже работающий ПРОЦЕСС в графе
```

Три разных состояния: `src/.../sim.launch.py` — источник; `install/.../share/turtle_bringup/launch/`
— установленный ресурс, его находит `ros2 launch` (именно поэтому запуск до пересборки падал);
`/turtlesim` в `node list` — живой процесс, объявленный в DDS.

### Запуск и остановка

```
$ ros2 launch turtle_bringup sim.launch.py     # терминал A
[turtlesim_node-1] [INFO] ... Starting turtlesim with node name /turtlesim
[turtlesim_node-1] [INFO] ... Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]

$ ros2 node list --no-daemon --spin-time 5     # терминал C
/turtlesim

^C                                             # Ctrl+C в терминале A
[INFO] [turtlesim_node-1]: sending signal 'SIGINT' to process[turtlesim_node-1]
[turtlesim_node-1] [INFO] ... [rclcpp]: signal_handler(SIGINT/SIGTERM)
[INFO] [turtlesim_node-1]: process has finished cleanly [pid 37973]
```

launch сам послал SIGINT запущенной ноде и дождался её завершения — `turtlesim_node`
закрылась вместе с запуском (проверено `pgrep`: процессов не осталось).

## Шаг 4 · Одна команда → движение

```
$ ros2 topic type /turtle1/pose
turtlesim/msg/Pose
$ ros2 topic echo /turtle1/pose --once        # до команды
x: 5.544444561004639  y: 5.544444561004639  theta: 0.0

$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
    '{linear: {x: 1.0}, angular: {z: 0.5}}'   # терминал B, одна публикация
publishing #1: ...Twist(linear=...(x=1.0...), angular=...(z=0.5...))

$ ros2 topic echo /turtle1/pose --once        # после команды
x: 6.509308815002441  y: 5.796990871429443  theta: 0.5040000081062317
```

Ожидалось: `linear.x>0` — вперёд по направлению взгляда, `angular.z>0` — поворот
против часовой. Факт: x и y выросли, theta 0 → 0,504 рад — черепашка сместилась и
повернулась именно так. Одна публикация дала короткий импульс (turtlesim интегрирует
скорость до следующей команды) — движение не бесконечное.

## Шаг 5 · Ошиблись в имени — /cmd_vel вместо /turtle1/cmd_vel

### До (шаг 4): издатель в полном имени

`ros2 topic info /turtle1/cmd_vel --verbose`: Publisher count 1, Subscription count 1
(подписчик `turtlesim`) — команда доставляется, поза меняется (см. выше).

### Сбой: `--wait-matching-subscriptions 0` и относительное имя

```
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
    /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'   # издатель работает

$ ros2 topic info /cmd_vel --verbose
Publisher count: 1
Node name: _ros2cli_38118        # издатель ЕСТЬ
Subscription count: 0            # подписчиков НЕТ
...
$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist
Publisher count: 0
Subscription count: 1
Node name: turtlesim             # подписчик turtlesim ждёт ДРУГОЕ имя
```

Поза не меняется: `/cmd_vel` и `/turtle1/cmd_vel` — два разных имени в графе, хотя тип
(Twist) у них один и тот же. `--wait-matching-subscriptions 0` разрешил публиковать в
пустоту (с `--once` по умолчанию ждётся один подписчик, и команда бы зависла в ожидании).

### После: исправлено только имя

```
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 1 /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'

$ ros2 topic info /turtle1/cmd_vel --verbose
Publisher count: 1               # появился издатель
Subscription count: 1            # подписчик turtlesim был и остался
--- поза после движения ---
x: 5.952568531036377  y: 9.500670433044434  theta: 2.927999973297119   # черепашка едет
```

После Ctrl+C издателя черепашка остановилась (поза не меняется 6 с:
x 8.610887 → 8.610887).

### Почему правильного типа недостаточно

Обнаружение и доставка в ROS 2 устроены по именам топиков: подписчик turtlesim создаёт
подписку на имя `/turtle1/cmd_vel`, издатель объявляется на `/cmd_vel`. DDS сопоставляет
эндпоинты по **полному имени** (и совместимому типу); одинаковый `geometry_msgs/msg/Twist`
их не сближает — это два несвязанных топика графа. Тип важен для совместимости при
совпавшем имени; при несовпавшем имени доставка не начинается вовсе: издатель никого не
находит (`Subscription count: 0`), подписчик не получает данных. Правильное полное имя —
условие соединения, тип — условие понимания.
