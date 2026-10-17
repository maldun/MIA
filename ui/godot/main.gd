extends Node3D
# Phase 3: character viewer (waist-up, soft light, orbit/zoom camera for mouse and touch).

const CHARACTER := "res://assets/mia.vrm"
const ARM_DOWN_DEG := 68.0

var character: Node3D
var skeleton: Skeleton3D
var camera: Camera3D
var pivot := Vector3(0, 1.2, 0)
var yaw := 0.0
var pitch := deg_to_rad(5.0)
var distance := 1.9
var _touches := {}
var _pinch_start := 0.0
var _pinch_dist_start := 0.0

func _ready() -> void:
	_setup_environment()
	_load_character()
	_setup_camera()

func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.86, 0.88, 0.92)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.85, 0.87, 0.95)
	env.ambient_light_energy = 0.6
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	# soft key light from the front left
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-30, 25, 0)
	key.light_energy = 0.8
	add_child(key)

func _load_character() -> void:
	var packed := load(CHARACTER) as PackedScene
	if packed == null:
		push_error("cannot load " + CHARACTER)
		return
	character = packed.instantiate()
	add_child(character)
	skeleton = character.find_child("GeneralSkeleton", true, false)
	if skeleton:
		_relaxed_pose()
		var head := skeleton.find_bone("Head")
		if head >= 0:
			pivot = skeleton.global_transform * skeleton.get_bone_global_pose(head).origin - Vector3(0, 0.15, 0)

# rotates the upper arms around the model's Z axis so the T-pose becomes arms-down
func _relaxed_pose() -> void:
	for side in [["LeftUpperArm", 1.0], ["RightUpperArm", -1.0]]:
		var i := skeleton.find_bone(side[0])
		if i < 0:
			continue
		var parent := skeleton.get_bone_parent(i)
		var parent_global := skeleton.get_bone_global_pose(parent).basis
		var rest_local := skeleton.get_bone_rest(i).basis
		var rest_global := parent_global * rest_local
		var rot := Basis(Vector3.BACK, deg_to_rad(ARM_DOWN_DEG) * side[1])
		var new_global := rot * rest_global
		var pose := rest_local.inverse() * parent_global.inverse() * new_global
		skeleton.set_bone_pose_rotation(i, pose.get_rotation_quaternion())

func _setup_camera() -> void:
	camera = Camera3D.new()
	camera.fov = 30.0
	camera.near = 0.05
	add_child(camera)
	_update_camera()

func _update_camera() -> void:
	pitch = clampf(pitch, deg_to_rad(-40), deg_to_rad(60))
	distance = clampf(distance, 0.4, 2.5)
	var offset := Vector3(0, 0, distance).rotated(Vector3.RIGHT, -pitch).rotated(Vector3.UP, yaw)
	camera.position = pivot + offset
	camera.look_at(pivot)

func _unhandled_input(event: InputEvent) -> void:
	# mouse: left drag orbits, wheel zooms
	if event is InputEventMouseMotion and (event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		yaw -= event.relative.x * 0.006
		pitch += event.relative.y * 0.006
		_update_camera()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance *= 0.92
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance /= 0.92
		_update_camera()
	# touch: one finger orbits, two fingers pinch-zoom
	elif event is InputEventScreenTouch:
		if event.pressed:
			_touches[event.index] = event.position
		else:
			_touches.erase(event.index)
		if _touches.size() == 2:
			var p: Array = _touches.values()
			_pinch_start = (p[0] as Vector2).distance_to(p[1])
			_pinch_dist_start = distance
	elif event is InputEventScreenDrag:
		_touches[event.index] = event.position
		if _touches.size() == 1:
			yaw -= event.relative.x * 0.006
			pitch += event.relative.y * 0.006
		elif _touches.size() == 2 and _pinch_start > 0.0:
			var p: Array = _touches.values()
			distance = _pinch_dist_start * _pinch_start / maxf((p[0] as Vector2).distance_to(p[1]), 1.0)
		_update_camera()
