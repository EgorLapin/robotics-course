# PR06 frames.md — дерево преобразований course_ackermann

Все фиксированные кадры публикует **единственный** издатель — нода
`robot_state_publisher` (из `robot_description`, развёрнутого из
`src/course_description/urdf/vehicle.urdf.xacro`) на `/tf_static`
(RELIABLE + TRANSIENT_LOCAL). Подвижные звенья (колёса/рулевые) идут в `/tf`
(RELIABLE + VOLATILE) только при опубликованном `joint_states`; в обязательной
части издателя у `/tf` нет — подписчиков колёсных tf нет намеренно, второго
издателя `/tf_static` мы не запускаем (два издателя дают случайный ответ).

Единицы СИ, оси REP-103: x вперёд, y влево, z вверх; колёса крутятся вокруг +y,
рулевые кулаки — вокруг +z.

## Связи (joint -> родитель/потомок)

| Joint | Тип | Родитель | Потомок | Ожидаемое преобразование (родитель -> потомок) | Владелец публикации |
| --- | --- | --- | --- | --- | --- |
| front_left_steering_joint | revolute (axis z, ±0.55) | base_link | front_left_knuckle | xyz (0.40, 0.31, 0) | /tf при joint_states (не публикуется в обязательной части) |
| front_right_steering_joint | revolute (axis z, ±0.55) | base_link | front_right_knuckle | xyz (0.40, −0.31, 0) | /tf при joint_states |
| front_left_wheel_joint | revolute (axis y) | front_left_knuckle | front_left_wheel | xyz (0, 0, 0) | /tf при joint_states |
| front_right_wheel_joint | revolute (axis y) | front_right_knuckle | front_right_wheel | xyz (0, 0, 0) | /tf при joint_states |
| rear_left_wheel_joint | revolute (axis y) | base_link | rear_left_wheel | xyz (−0.40, 0.31, 0) | /tf при joint_states |
| rear_right_wheel_joint | revolute (axis y) | base_link | rear_right_wheel | xyz (−0.40, −0.31, 0) | /tf при joint_states |
| camera_joint | fixed | **base_link** | camera_link | xyz (0.28, 0, 0.38) | /tf_static — robot_state_publisher |
| lidar_joint | fixed | **base_link** | lidar_link | xyz (0.28, 0, 0.38) | /tf_static — robot_state_publisher |
| imu_joint | fixed | **base_link** | imu_link | xyz (0.28, 0, 0.38) | /tf_static — robot_state_publisher |

Размеры перенесены из `course-kit/v1/models/course_ackermann/model.sdf`:
короб корпуса 1.05×0.52×0.22 м (центр z=0.12, масса 12 кг), цилиндры колёс
r=0.12, l=0.07 (масса 0.8 кг), оси x=±0.40, колея y=±0.31.

## Проверки

```
$ ros2 run tf2_ros tf2_echo base_link lidar_link   # после починки (main)
- Translation: [0.280, 0.000, 0.380]               # ровно offset из URDF

$ ros2 run tf2_ros tf2_echo base_link lidar_link   # ветка pr06-broken (ef71b8f)
- Translation: [0.560, 0.000, 0.760]               # offset применён дважды

$ ros2 run tf2_tools view_frames   # (frames.pdf: tree below, log excerpt)
camera_link:
  parent: 'base_link'
  broadcaster: 'default_authority'
imu_link:
  parent: 'base_link'
lidar_link:
  parent: 'base_link'
```

Дефект: в отдельной ветке `pr06-broken` у `lidar_joint` parent изменён на
`camera_link` при том же offset — лидар уехал в (0.56, 0, 0.76), а
`test_fixed_sensors_parent_is_base_link` упал; `check_urdf` при этом дерево
принял (связно/ациклично) — см. `defect-broken.txt`, возврат связи в main.
