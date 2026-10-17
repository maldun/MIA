extends Node3D
# Character viewer: soft light, orbit/zoom camera (mouse and touch), expression and gesture review panel.

const CHARACTER := "res://assets/mia.vrm"
const MIN_DISTANCE := 0.4
const MAX_DISTANCE := 5.0
const CAMERA_FOLLOW := 8.0  # how fast the camera eases to a new view (1/s)

var character: Node3D
var skeleton: Skeleton3D
var camera: Camera3D
var head_height := 1.5
var pivot := Vector3(0, 0.8, 0)
var yaw := 0.0
var pitch := deg_to_rad(4.0)
var distance := 3.8
var _pivot_goal := pivot
var _distance_goal := distance
var _touches := {}
var _pinch_start := 0.0
var _pinch_dist_start := 0.0

var engine: ExpressionEngine
var _bar: Control
var _buttons := {}  # "expression:<name>" / "gesture:<name>" -> Button (highlighted while active)

func _ready() -> void:
	_setup_environment()
	_load_character()
	_setup_camera()
	_setup_expressions()
	_build_panel()
	show_view("body")

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
		var head := skeleton.find_bone("Head")
		if head >= 0:
			head_height = (skeleton.global_transform * skeleton.get_bone_global_pose(head).origin).y

func _setup_expressions() -> void:
	if skeleton == null:
		return
	engine = ExpressionEngine.new()
	add_child(engine)
	engine.setup(character, skeleton)  # also puts the arms into the relaxed base pose
	engine.load_library("res://presets/library.json")
	engine.play("idle", 0.0)

# --- camera ---------------------------------------------------------------------------------

func _setup_camera() -> void:
	camera = Camera3D.new()
	camera.fov = 30.0
	camera.near = 0.05
	add_child(camera)
	_update_camera()

## Named views: "body" (whole figure), "bust" (waist up), "face"
func show_view(view: String) -> void:
	match view:
		"face":
			_pivot_goal = Vector3(0, head_height + 0.02, 0)
			_distance_goal = 0.8
		"bust":
			_pivot_goal = Vector3(0, head_height - 0.15, 0)
			_distance_goal = 1.9
		_:
			_pivot_goal = Vector3(0, head_height * 0.55, 0)
			_distance_goal = 3.8

## Sets the camera right away (also used by the screenshot tools).
func set_camera(new_pivot: Vector3, new_distance: float) -> void:
	pivot = new_pivot
	distance = new_distance
	_pivot_goal = new_pivot
	_distance_goal = new_distance
	_update_camera()

func _process(delta: float) -> void:
	var k := 1.0 - exp(-CAMERA_FOLLOW * delta)
	if not pivot.is_equal_approx(_pivot_goal) or not is_equal_approx(distance, _distance_goal):
		pivot = pivot.lerp(_pivot_goal, k)
		distance = lerpf(distance, _distance_goal, k)
		_update_camera()

func _update_camera() -> void:
	pitch = clampf(pitch, deg_to_rad(-40), deg_to_rad(60))
	distance = clampf(distance, MIN_DISTANCE, MAX_DISTANCE)
	var offset := Vector3(0, 0, distance).rotated(Vector3.RIGHT, -pitch).rotated(Vector3.UP, yaw)
	camera.position = pivot + offset
	camera.look_at(pivot)

func _zoom(factor: float) -> void:
	_distance_goal = clampf(_distance_goal * factor, MIN_DISTANCE, MAX_DISTANCE)

func _unhandled_input(event: InputEvent) -> void:
	# mouse events emulated from touches are ignored here: touches are handled below
	if event is InputEventMouse and event.device == InputEvent.DEVICE_ID_EMULATION:
		return
	# mouse: left drag orbits, wheel zooms
	if event is InputEventMouseMotion and (event.button_mask & MOUSE_BUTTON_MASK_LEFT):
		yaw -= event.relative.x * 0.006
		pitch += event.relative.y * 0.006
		_update_camera()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom(0.92)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom(1.0 / 0.92)
	# touch: one finger orbits, two fingers pinch-zoom
	elif event is InputEventScreenTouch:
		if event.pressed:
			_touches[event.index] = event.position
		else:
			_touches.erase(event.index)
		if _touches.size() == 2:
			var p: Array = _touches.values()
			_pinch_start = (p[0] as Vector2).distance_to(p[1])
			_pinch_dist_start = _distance_goal
	elif event is InputEventScreenDrag:
		_touches[event.index] = event.position
		if _touches.size() == 1:
			yaw -= event.relative.x * 0.006
			pitch += event.relative.y * 0.006
			_update_camera()
		elif _touches.size() == 2 and _pinch_start > 0.0:
			var p: Array = _touches.values()
			_distance_goal = clampf(_pinch_dist_start * _pinch_start / maxf((p[0] as Vector2).distance_to(p[1]), 1.0),
					MIN_DISTANCE, MAX_DISTANCE)

# --- review panel -------------------------------------------------------------------------------
# temporary (the slider editor of phase 6 replaces it); collapsible for phones

func _build_panel() -> void:
	if engine == null:
		return
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	root.grow_vertical = Control.GROW_DIRECTION_BEGIN
	layer.add_child(root)
	var toggle := Button.new()
	toggle.text = "Menu"
	toggle.custom_minimum_size = Vector2(0, 56)
	root.add_child(toggle)
	_bar = VBoxContainer.new()
	_bar.visible = false  # start collapsed so the whole figure is visible
	root.add_child(_bar)
	_add_row("Camera", ["body", "bust", "face"], show_view)
	_add_row("Expression", engine.library_order, engine.play, "expression")
	_add_row("Gesture", ["stop gesture"] + engine.gestures.library_order, _gesture_button, "gesture")
	toggle.pressed.connect(func(): _bar.visible = not _bar.visible)
	engine.expression_changed.connect(func(_n): _refresh_active())
	engine.gestures.gesture_started.connect(func(_n): _refresh_active())
	engine.gestures.gesture_finished.connect(func(_n): _refresh_active())
	_refresh_active()

func _gesture_button(item: String) -> void:
	if item == "stop gesture":
		engine.gestures.stop()
	else:
		engine.gestures.play(item)

## highlights the buttons of the expression and gesture that are active right now
func _refresh_active() -> void:
	for key in _buttons:
		var parts: PackedStringArray = key.split(":")
		var active := (parts[0] == "expression" and parts[1] == engine.current_name) \
				or (parts[0] == "gesture" and parts[1] == engine.gestures.current)
		(_buttons[key] as Button).modulate = Color(1.0, 0.85, 0.35) if active else Color.WHITE

func _add_row(title: String, names: Array, callback: Callable, kind := "") -> void:
	if not title.is_empty():
		var label := Label.new()
		label.text = title
		label.add_theme_color_override("font_shadow_color", Color(1, 1, 1, 0.6))
		_bar.add_child(label)
	var flow := HFlowContainer.new()
	_bar.add_child(flow)
	for item in names:
		var b := Button.new()
		b.text = item
		b.custom_minimum_size = Vector2(100, 48)
		b.pressed.connect(callback.bind(item))
		flow.add_child(b)
		if not kind.is_empty():
			_buttons[kind + ":" + item] = b
