# ПР02 · types.md — типы и поля сообщений

Команды и выводы соответствуют моей установке (ROS 2 Jazzy):
`ros2 topic type /turtle1/pose` → `turtlesim/msg/Pose` (в Lyrical тот же тип назывался бы
`turtlesim_msgs/msg/Pose` — выбираем по выводу своей команды).

## Два основных топика этой работы

| Топик | Тип | Направление | Назначение |
|---|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | teleop/CLI → turtlesim | команда скорости для черепахи turtle1 |
| `/turtle1/pose` | `turtlesim/msg/Pose` | turtlesim → наблюдатели | текущая поза turtle1 (обратная связь) |

Имена полные (absolute): начинаются с `/`, не зависят от namespace издателя/подписчика.
Относительное имя `cmd_vel` в рабочем namespace `/` разворачивается в `/cmd_vel` — это уже
другой топик (см. commands.md, шаг 5).

## geometry_msgs/msg/Twist (команда)

```
$ ros2 interface show geometry_msgs/msg/Twist
# This expresses velocity in free space broken into its linear and angular parts.
Vector3  linear
	float64 x
	float64 y
	float64 z
Vector3  angular
	float64 x
	float64 y
	float64 z
```

Поля, значимые для turtlesim (плоскость):

- `linear.x` — поступательная скорость вперёд вдоль «морды» черепахи (м/с). `>0` — вперёд,
  `<0` — назад.
- `linear.y` — боковая скорость; turtlesim её игнорирует (черепашка не умеет боком).
- `linear.z` — вертикальная; игнорируется в 2D.
- `angular.z` — угловая скорость вокруг оси Z (рад/с): `>0` против часовой, `<0` по часовой.
- `angular.x`, `angular.y` — наклоны; в 2D-симуляторе игнорируются.

Пример из опыта: `{linear: {x: 1.0}, angular: {z: 0.5}}` — «ехать вперёд 1 м/с и
поворачивать 0,5 рад/с» → поза x 5.544→6.509, theta 0→0.504.

## turtlesim/msg/Pose (состояние)

```
$ ros2 interface show turtlesim/msg/Pose
float32 x
float32 y
float32 theta
float32 linear_velocity
float32 angular_velocity
```

- `x`, `y` — координаты в окне симулятора (0…11); старт черепашки `5.544, 5.544`.
- `theta` — ориентация в радианах (0 … 2π).
- `linear_velocity`, `angular_velocity` — фактические скорости; после остановки издателя
  обе 0, поза перестаёт меняться.

Пример сообщения (до команды): `x: 5.544444561004639  y: 5.544444561004639  theta: 0.0`;
(после команды выше): `x: 6.509308815002441  y: 5.796990871429443  theta: 0.5040000081062317`.

## Что это объясняет про граф

`ros2 topic info /cmd_vel --verbose` и `ros2 topic info /turtle1/cmd_vel --verbose`
показывают одинаковый `Type: geometry_msgs/msg/Twist`, но у первого только издатель
(Publisher count 1, Subscription count 0), у второго — только подписчик turtlesim
(Publisher count 0, Subscription count 1). Тип сообщения описывает *формат данных*;
*соединение* в графе происходит по полному имени топика. Файл `.msg` в пакете — это
описание типа на диске; сообщение «живёт» только в момент доставки между издателем и
подписчиком, а нода — это процесс, который эти эндпоинты создаёт.
