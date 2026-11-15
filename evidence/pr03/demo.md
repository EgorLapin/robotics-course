# ПР03 · demo.md — первая нода: поза и команда

Среда: WSL2 Ubuntu 24.04, ROS 2 Jazzy, `ROS_DOMAIN_ID=16`. Симулятор запускается launch'ом
из ПР02: `ros2 launch turtle_bringup sim.launch.py` (терминал A). Пакет `patrol`:
подписка на `/turtle1/pose` хранит последнюю позу, таймер 0,1 с публикует
`geometry_msgs/msg/Twist` в относительный `cmd_vel`; до первой позы — нулевая команда,
после — `linear.x=0.5`, `angular.z=0.3`. Выбор команды вынесен в чистую функцию
`decide_command()` и покрыт pytest (см. `tests.txt`). Тип позы по выводу команды:
`ros2 topic type /turtle1/pose` → `turtlesim/msg/Pose` (Jazzy).

Сырые запуски: `raw-broken.txt`, `raw-fixed.txt`, `raw-hz.txt`; вывод тестов — `tests.txt`.

## Роль частей ноды (каркас hello_ros)

- **`__init__` (init)** — конструктор `PatrolNode(Node)`: регистрирует узел `patrol`,
  создаёт издатель `Twist` на `cmd_vel`, подписку на `/turtle1/pose` и таймер 0,1 с.
  Подписку сохраняем полем объекта (`self._sub`), иначе Python соберёт объект подписки
  сборщиком мусора и подписки в графе не станет. Конструктор только описывает, что узел
  умеет, — сам он ничего не вызывает.
- **callback** (`_on_pose`) — ROS вызывает его при каждом сообщении позы; он только
  сохраняет `msg` в `self._last_pose`. Из callback'а не публикуем: публиковал бы ровно
  с частотой позы (~62 Гц), а нам нужен собственный такт.
- **таймер** (`_on_timer`) — каждые 0,1 с читает последнюю позу, зовёт чистую
  `decide_command()` и публикует Twist. Это «тактовый генератор» команды: 10 Гц, не
  зависит от того, как часто приходит поза.
- **`rclpy.spin(node)`** — бесконечный цикл: ждёт готовности событий (сообщения, таймеры)
  и вызывает callback'и. До `spin` ни подписка, ни таймер не работают — узел в графе есть
  (он объявлен в init), но «не живёт».
- **Ctrl+C** — в Jazzy SIGINT обрабатывает сам rclpy: он выключает контекст, и `spin`
  завершается исключением `ExternalShutdownException` (обрабатываем его рядом с
  `KeyboardInterrupt`), `finally` уничтожает узел, процесс завершается кодом 0. Исчезновение
  процесса — не команда торможения: turtlesim получил бы последную ненулевую команду и
  катился бы по инерции, поэтому после остановки **ждём** и проверяем, что поза замёрзла,
  а `linear_velocity=angular_velocity=0` (см. «Доказать» ниже).

## 1 · Собрать

```
$ ros2 pkg create --build-type ament_python --node-name patrol patrol --dependencies rclpy geometry_msgs
$ ros2 topic type /turtle1/pose
turtlesim/msg/Pose
# + <depend>turtlesim</depend> в package.xml — пакет типа Pose выбранной дистрибуции
$ colcon build --symlink-install --packages-select patrol
Summary: 1 package finished
$ source install/setup.bash && python3 -m pytest src/patrol/test
7 passed, 1 skipped            # тесты чистой функции decide_command + линтеры шаблона
$ colcon test --packages-select patrol && colcon test-result --verbose
Summary: 11 tests, 0 errors, 0 failures, 2 skipped
```

`test_copyright` пропущен генератором (нет заголовка авторства в файлах шаблона) — skip, не
провал; `decide_command` покрыт 5 тестами: отсутствие позы, нормальная поза, NaN-координаты,
ограничения команды, «далёкая» поза.

## 2 · Сломать: публикация в относительный cmd_vel

```
$ ros2 run patrol patrol          # терминал B, БЕЗ remap — так по условию
[INFO] ... [patrol]: patrol started, waiting for /turtle1/pose
```

Наблюдение (полный текст — `raw-broken.txt`):

```
$ ros2 topic info /cmd_vel --verbose | grep -E "Type|count"
Type: geometry_msgs/msg/Twist
Publisher count: 1        # patrol публикует 10 Гц — издатель ВИДЕН
Subscription count: 0     # подключаться не к чему
$ ros2 topic info /turtle1/cmd_vel --verbose | grep -E "Type|count"
Type: geometry_msgs/msg/Twist
Publisher count: 0
Subscription count: 1     # подписчик turtlesim ждёт ДРУГОЕ имя
$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639  y: 5.544444561004639  theta: 0.0
(через 3 с — то же)      # черепаха стоит
```

Тип совпадает, имена — нет: узел в namespace `/` публикует относительное `cmd_vel` →
`/cmd_vel`, а turtlesim подписан на `/turtle1/cmd_vel`. DDS соединяет эндпоинты по полному
имени, соединение не возникает. Нода при этом исправно получает позу (подписка на
абсолютный `/turtle1/pose`) и печатает 10 Гц в пустоту.

## 3 · Доказать: remap + измерение частоты

Исправлен только запуск — имя топика подменяет CLI-ремap, код и сборка не менялись:

```
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
$ ros2 node list --no-daemon --spin-time 5
/patrol
/turtlesim
$ ros2 topic info /turtle1/cmd_vel --verbose | grep -E "Type|count"
Type: geometry_msgs/msg/Twist
Publisher count: 1        # patrol подключился к правильному имени
Subscription count: 1     # turtlesim принимает
```

Движение (позы с интервалом 4 с, `raw-fixed.txt`):

```
x: 5.452473163604736  y: 8.875452995300293  theta: -3.0911853313446045
x: 3.8837056159973145 y: 7.0294508934021    theta: -1.4639853239059448
```

Реальная частота команды, `ros2 topic hz /turtle1/cmd_vel` при ноде, работающей ~14 с
(замер ~11 с; полное окно снимка — `raw-hz.txt`):

```
average rate: 10.544  window: 12
average rate: 10.277  window: 23
average rate: 10.191  window: 33
average rate: 10.143  window: 44
```

≈10 Гц при заявленном таймере 0,1 с; избыток первых окон — discovery-задержка первого
сообщения измерителя. Измерение выполнено в исправленном имени `/turtle1/cmd_vel`
(после remap).

Остановка (Ctrl+C → SIGINT процессу patrol) и ожидание остановки turtlesim:

```
(после kill -INT; patrol завершился штатно)
$ ros2 topic echo /turtle1/pose --once
x: 6.703990459442139  y: 8.404398918151855  theta: 2.366414785385132
linear_velocity: 0.0
angular_velocity: 0.0
$ sleep 5; ros2 topic echo /turtle1/pose --once    # то же самое — черепаха остановилась
```

## Почему remap, а не правка кода

Имя `cmd_vel` оставлено относительным сознательно (так в условии): один и тот же пакет
подключается к разным топикам/namespace при запуске (`-r cmd_vel:=...`, `namespace=` в
launch) без пересборки. Правка литерала в коде привязала бы ноду к одному чату и убрала
бы наблюдаемый дефект, который мы и разбираем: совпадения типа Twist недостаточно —
граф соединяет издателя и подписчика по полному имени топика.
