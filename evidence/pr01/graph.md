# ПР01 · graph.md — Окружение и первый граф ROS 2

Среда: WSL2 (Ubuntu 24.04.5), ROS 2 Jazzy, домены опыта 16 (исправный) и 17 (разрыв).
Все команды выполнялись в терминалах с `source /opt/ros/jazzy/setup.bash`.
Симулятор (терминал A) запущен `ros2 run turtlesim turtlesim_node` и не перезапускался
между стадиями «собрать / сломать / доказать».

## 1 · Собрать: исправный граф (ROS_DOMAIN_ID=16)

Терминал A: `ros2 run turtlesim turtlesim_node` (окно turtlesim открылось через WSLg).
Терминал B: `ros2 run turtlesim turtle_teleop_key`, нажимались стрелки вверх.

### Ноды

```
$ ros2 node list --no-daemon --spin-time 5   # export ROS_DOMAIN_ID=16
/teleop_turtle
/turtlesim
```

### Топики и типы

```
$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim/msg/Color]
/turtle1/pose [turtlesim/msg/Pose]
```

### Узел симулятора

```
$ ros2 node info /turtlesim
/turtlesim
  Subscribers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/color_sensor: turtlesim/msg/Color
    /turtle1/pose: turtlesim/msg/Pose
  Service Servers:
    /clear: std_srvs/srv/Empty
    /kill: turtlesim/srv/Kill
    /reset: std_srvs/srv/Empty
    /spawn: turtlesim/srv/Spawn
    /turtle1/set_pen: turtlesim/srv/SetPen
    /turtle1/teleport_absolute: turtlesim/srv/TeleportAbsolute
    /turtle1/teleport_relative: turtlesim/srv/TeleportRelative
    ... (служебные параметр-серверы опущены)
  Action Servers:
    /turtle1/rotate_absolute: turtlesim/action/RotateAbsolute
```

### Тип позы и одно сообщение

```
$ ros2 topic type /turtle1/pose
turtlesim/msg/Pose

$ ros2 topic echo /turtle1/pose --once
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
exit=0
```

### Движение с клавиатуры (телеуправление в домене 16)

После четырёх нажатий «вверх» координата x изменилась — команда доходит:

```
ДО:    x: 5.544444561004639  y: 5.544444561004639
ПОСЛЕ: x: 9.576444625854492  y: 5.544444561004639   (theta=0, движение вдоль x)
```

### Частота /turtle1/pose (замер 12 с)

```
$ ros2 topic hz /turtle1/pose   # 12 с, остановка Ctrl+C (SIGINT)
average rate: 62.522   window: 64
average rate: 62.490   window: 127
...
average rate: 62.499   window: 631
```

Фактическая частота ≈ 62,5 Гц при таймере симулятора 16 мс; длительность замера 12 с
(631 сообщений в последнем окне). Последняя строка усреднения с окном 271 (15,9 Гц) —
артефакт усреднения при остановке SIGINT, стабильные окна дают 62,49–62,52 Гц.

## 2 · Сломать: другой ROS_DOMAIN_ID

Терминал B остановлен Ctrl+C и перезапущен в другом домене; в C тоже выставлен домен 17,
чтобы новый CLI-подписчик искал позу там же, где teleop. Симулятор не трогали —
`export` не перенастраивает уже работающую ноду.

```
$ export ROS_DOMAIN_ID=17
$ ros2 node list --no-daemon --spin-time 5   # export ROS_DOMAIN_ID=17
/teleop_turtle
```

`/turtlesim` в домене 17 не виден. Поза не приходит (сырой лог — `evidence/pr01/pose-broken.txt`):

```
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once
exit=124        # таймаут 5 с истёк, ни одного сообщения
```

Стрелки в терминале B больше не двигают черепаху.

## 3 · Доказать: возврат в исходный домен

Терминал B перезапущен с `ROS_DOMAIN_ID=16` (изменено только это), симулятор тот же.

```
$ export ROS_DOMAIN_ID=16
$ ros2 node list --no-daemon --spin-time 5   # export ROS_DOMAIN_ID=16
/teleop_turtle
/turtlesim
```

Тот же тест получает позу (`evidence/pr01/pose-fixed.txt`):

```
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once
x: 5.128444671630859
y: 5.544444561004639
...
exit=0
```

## Сравнение «до / сбой / после»

| | домен ноды-издателя | домен наблюдателя | node list | echo /turtle1/pose | код возврата |
|---|---|---|---|---|---|
| до | 16 | 16 | /teleop_turtle, /turtlesim | приходит | 0 |
| сбой | 16 (не менялся) | 17 | только /teleop_turtle | таймаут | 124 |
| после | 16 | 16 | /teleop_turtle, /turtlesim | приходит | 0 |

## Почему перезапустили teleop, а не симулятор и не ROS

`ROS_DOMAIN_ID` читается каждым процессом при старте и определяет, в какой области
обнаружения (DDS domain) он объявляет своих участников; `export` меняет значение только
для новых процессов. Значит достаточно было перезапустить узлы, которые должны
«переехать» в другой домен (teleop и CLI-наблюдатель), а симулятор остаётся в домене 16 —
именно это и наблюдаем: в 17 он не появляется, а в 16 продолжает работать без изменений.
Установка ROS тоже не при чём: это только библиотека и набор нод, раздел доменов — свойство
запущенных процессов, а не пакетов. Причина сбоя — не «сломалась доставка», а то, что
участники оказались в разных областях discovery: издателя в домене 17 нет, и подписчик
не может узнать ни тип, ни адрес топика (в этом и причина, почему тип позы
передали явным аргументом `"$POSE_TYPE"`).
