# ПР04 · parameters.md — параметры patrol: смена на лету и отклонение нуля

Среда: WSL2 Ubuntu 24.04, ROS 2 Jazzy, `ROS_DOMAIN_ID=16`. Узел — `src/patrol` из ПР03,
доработанный: три параметра `linear_speed` (0.5, допустимо 0–1), `turn_rate` (0.3, −1–1),
`publish_hz` (10.0, 1–30). Колбэк `add_on_set_parameters_callback` проверяет **каждое**
предлагаемое значение до изменения состояния (`_on_set_parameters`: сначала валидация всех,
только потом запись и пересоздание таймера). Значение `publish_hz` — конечное число в
границах; NaN/inf не проходят `math.isfinite`. При допустимой смене `_restart_timer()`
отменяет и уничтожает прежний таймер (`cancel` + `destroy_timer`) и создаёт новый с
`period = 1/publish_hz` — двух таймеров не остаётся (тест `len(node.timers) == 1`).

Сырые прогоны: `raw-broken.txt` (отказ), `raw-fixed.txt` (отклонение + смена 10→5 Гц +
сервис/действие), `tests.txt` (тесты).

## 1 · Собрать

```
$ colcon build --symlink-install --packages-select patrol
Summary: 1 package finished
$ source install/setup.bash && python3 -m pytest src/patrol/test -q
25 passed, 1 skipped
$ ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
$ ros2 param list /patrol
  linear_speed
  publish_hz
  turn_rate
```

Значения по умолчанию 0.5 / 0.3 / 10.0, типы double. Валидация — чистая функция
`validate_param` (границы включительно), арифметика таймера — `timer_period = 1/publish_hz`.

## 2 · Сломать: проверка отключена, publish_hz = 0

Временный дефект в рабочем дереве (строчная замена, НЕ попадает в сдачу):

```python
# было:
ok, reason = validate_param(p.name, p.value, PARAM_BOUNDS[p.name])
# стало (ВРЕМЕННЫЙ ДЕФЕКТ ПР04):
ok, reason = (True, "")
```

Узел с таким кодом принимает любое значение. Подаём ноль (полный протокол — `raw-broken.txt`):

```
$ ros2 param set /patrol publish_hz 0.0
(ответа нет: сервис повис и умер вместе с узлом)
$ pgrep -f lib/patrol/patrol    # NO — узел УМЕР
--- лог узла ---
  period = timer_period(self._values['publish_hz'])
  File ".../patrol/patrol.py", line 44, in timer_period
ZeroDivisionError: float division by zero
[ros2run]: Process exited with failure 1
```

Отказ воспроизводим и конкретен: принятый `0.0` доходит до `1.0 / publish_hz`, деление на
ноль происходит уже **после** записи значения — колбэк параметров выполняется в исполнителе
самого узла, поэтому исключение роняет весь процесс. Черепашка при этом разгоняется до
последней команды (`linear_velocity: 0.5` в позе сразу после падения) — узел не успевает
остановить таймер: активного издателя больше нет, и через несколько секунд поза
замораживается с обнулёнными скоростями (последний замер в `raw-broken.txt`).

## 3 · Доказать: проверка возвращена

Код возвращён на место валидации (`ok, reason = validate_param(...)`). Тот же сценарий —
значение отклонено, **активное состояние цело** (`raw-fixed.txt`):

```
$ ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz=0.0 rejected: out of range [1.0, 30.0]
$ ros2 param set /patrol publish_hz -3.0
Setting parameter failed: publish_hz=-3.0 rejected: out of range [1.0, 30.0]
$ ros2 param get /patrol publish_hz
Double value is: 10.0          # старое значение сохранено
# NODE_ALIVE                   # узел жив, таймер не тронут
```

Допустимая смена 10 → 5 Гц меняет поток. Поток меряем собственным зондом
(`rclpy`-подписка, сохранённая полем объекта; `ros2 topic hz` в долгих WSL-сессиях
ловил discovery-разрывы до 5 с и занижал среднее — отмечено в ПР03):

```
[A] warmup 1.4 с, pubs: 1      # publish_hz=10.0
[A] sec 1: +11  sec 2: +10  sec 3: +11  sec 4: +10  sec 5: +10
[A] sec 6: +11  sec 7: +10  sec 8: +10  sec 9: +10  sec 10: +11
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
--- лог узла ---
[patrol]: timer recreated: period 0.1000 s (publish_hz=10.0)
[patrol]: timer recreated: period 0.2000 s (publish_hz=5.0)
[B] warmup 2.6 с, pubs: 1      # publish_hz=5.0
[B] sec 1: +5  sec 2: +5  sec 3: +5  sec 4: +5  sec 5: +5
[B] sec 6: +6  sec 7: +5  sec 8: +5  sec 9: +5  sec 10: +5
```

Ровно вдвое реже при том же качестве потока; прежний таймер уничтожен — узловой тест
подтверждает `len(node.timers) == 1` и `period = 0.2 с`.

## 4 · Тесты (tests.txt)

- `test_parameters.py` — чистая `validate_param`: дефолты валидны; `0`, `-3`, `NaN`, `inf`,
  `True` отклоняются; границы 1/30 включительно; 10→5 валидна; скорости/повороты по границам.
- `test_param_node.py` — живой узел через `set_parameters`: 10→5 создаёт новый таймер
  (0.2 с, ровно один в `node.timers`); 0/−3/NaN/inf отклоняются и **не меняют** ни
  `_timer` (тот же объект, тот же период), ни `publish_hz=10.0`; linear_speed/turn_rate
  применяются.
- `test_decide_command.py` — решения команды из ПР03 (нет позы/NaN → ноль, лимиты).
- `colcon test`: 29 тестов, 0 ошибок, 0 провалов (2 skip — copyright/flake8-шаблоны).

## 5 · Готовые сервис и действие (по лекции, конец raw-fixed.txt)

```
$ ros2 service list | grep clear
/clear                                     # std_srvs/srv/Empty
$ ros2 service call /clear std_srvs/srv/Empty {}
response:                                  # пустой ответ — работа выполнена
$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]
$ ros2 action info /turtle1/rotate_absolute
Action servers: 1 (/turtlesim)
```

Сервис — однократный запрос-ответ: клиент отправил `Empty` и получил короткий ответ, про
промежуток ничего не известно. Действие (`rotate_absolute`) — долгая цель: у него четыре
канала (goal/cancel/feedback/result), клиент может следить за прогрессом через feedback и
отменить выполнение, чего сервис не умеет.
