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
var _inset := Vector4.ZERO  # left, right, top, bottom: fractions of the window the page covers (chat panel); eased
var _inset_goal := Vector4.ZERO
var _distance_goal := distance
var _touches := {}
var _pinch_start := 0.0
var _pinch_dist_start := 0.0

var engine: ExpressionEngine
var bridge: HostBridge
var backgrounds: BackgroundManager
var preset_api: PresetApi
var editor: ExpressionEditor
var _bar: Control
var _menu_root: Control
var _expression_flow: HFlowContainer
var _background_row_built := false
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
	# the background (plain colour or a picture from the backgrounds folder) is drawn on canvas layer -1
	env.background_mode = Environment.BG_CANVAS
	env.background_canvas_max_layer = -1
	backgrounds = BackgroundManager.new()
	add_child(backgrounds)
	backgrounds.setup()
	backgrounds.refresh()
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
	# the presets of the server (shared by all devices) replace the bundled ones as soon as they arrive;
	# without a server the bundled presets stay
	preset_api = PresetApi.new()
	add_child(preset_api)
	preset_api.setup()
	preset_api.library_received.connect(func(presets: Array, _info): _on_server_presets(presets))
	preset_api.gestures_received.connect(func(docs: Array): engine.gestures.set_pose_gestures(docs))   # gestures made in the editor
	preset_api.refresh()
	preset_api.start_polling()
	bridge = HostBridge.new()
	add_child(bridge)
	bridge.setup(engine, backgrounds)  # commands from the page around us (MIA's chat page)
	bridge.inset_changed.connect(set_inset)
	bridge.view_requested.connect(show_view)

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

## The page covers part of the window (chat panel, bottom sheet): the camera centers the character in the free area
## and keeps it inside the free height. Fractions of the window; eased like the views.
func set_inset(left: float, right: float, top: float, bottom: float) -> void:
	_inset_goal = Vector4(left, right, top, bottom)

## Sets the camera right away (also used by the screenshot tools).
func set_camera(new_pivot: Vector3, new_distance: float) -> void:
	pivot = new_pivot
	distance = new_distance
	_pivot_goal = new_pivot
	_distance_goal = new_distance
	_update_camera()

func _process(delta: float) -> void:
	var k := 1.0 - exp(-CAMERA_FOLLOW * delta)
	var moving := not pivot.is_equal_approx(_pivot_goal) or not is_equal_approx(distance, _distance_goal)
	if moving:
		pivot = pivot.lerp(_pivot_goal, k)
		distance = lerpf(distance, _distance_goal, k)
	if _inset != _inset_goal:
		_inset = _inset.lerp(_inset_goal, k)
		if _inset.distance_to(_inset_goal) < 0.0005:
			_inset = _inset_goal
		moving = true
	if moving:
		_update_camera()

func _update_camera() -> void:
	pitch = clampf(pitch, deg_to_rad(-40), deg_to_rad(60))
	distance = clampf(distance, MIN_DISTANCE, MAX_DISTANCE)
	# the free height of the window decides how far away the camera is (the figure stays inside it)
	var free_height := clampf(1.0 - _inset.z - _inset.w, 0.3, 1.0)
	var eff_distance := distance / free_height
	var offset := Vector3(0, 0, eff_distance).rotated(Vector3.RIGHT, -pitch).rotated(Vector3.UP, yaw)
	camera.position = pivot + offset
	camera.look_at(pivot)
	# the character appears in the middle of the free area: slide the camera (orientation stays) by the offset of that middle
	var size := get_viewport().get_visible_rect().size
	var half_height := eff_distance * tan(deg_to_rad(camera.fov) * 0.5)
	var half_width := half_height * size.x / maxf(size.y, 1.0)
	var ndc := Vector2(_inset.x - _inset.y, _inset.w - _inset.z)
	camera.position -= camera.global_transform.basis.x * ndc.x * half_width + camera.global_transform.basis.y * ndc.y * half_height

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
	# inside MIA's page the dev menu is hidden (add ?menu to the URL to see it anyway)
	if engine == null or (HostBridge.is_embedded() and not HostBridge.has_url_flag("menu")):
		return
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	root.grow_vertical = Control.GROW_DIRECTION_BEGIN
	layer.add_child(root)
	_menu_root = root
	var toggle := Button.new()
	toggle.text = "Menu"
	toggle.custom_minimum_size = Vector2(0, 56)
	root.add_child(toggle)
	_bar = VBoxContainer.new()
	_bar.visible = false  # start collapsed so the whole figure is visible
	root.add_child(_bar)
	editor = ExpressionEditor.new()
	layer.add_child(editor)
	editor.setup(engine, preset_api)
	editor.closed.connect(func(): _menu_root.visible = true)
	var editor_button := Button.new()
	editor_button.text = "Expression editor"
	editor_button.name = "editor_button"
	editor_button.custom_minimum_size = Vector2(0, 48)
	editor_button.pressed.connect(open_editor)
	_bar.add_child(editor_button)
	_add_row("Camera", ["body", "bust", "face"], show_view)
	_expression_flow = _add_row("Expression", engine.library_order, engine.play, "expression")
	engine.library_changed.connect(_rebuild_expression_row)
	_add_row("Gesture", ["stop gesture"] + engine.gestures.library_order, _gesture_button, "gesture")
	toggle.pressed.connect(func(): _bar.visible = not _bar.visible)
	backgrounds.list_changed.connect(_on_backgrounds_listed)
	_on_backgrounds_listed(backgrounds.names, backgrounds.default_name)
	backgrounds.background_changed.connect(func(_n): _refresh_active())
	engine.expression_changed.connect(func(_n): _refresh_active())
	engine.gestures.gesture_started.connect(func(_n): _refresh_active())
	engine.gestures.gesture_finished.connect(func(_n): _refresh_active())
	_refresh_active()
	if HostBridge.has_url_flag("editor"):
		open_editor()

## the background row appears when there are pictures in the backgrounds folder
func _on_backgrounds_listed(names: Array, _default_name: String) -> void:
	if _background_row_built or names.is_empty() or _bar == null:
		return
	_background_row_built = true
	_add_row("Background", ["none"] + names, func(item): backgrounds.show_background("" if item == "none" else item), "background")
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
				or (parts[0] == "gesture" and parts[1] == engine.gestures.current) \
				or (parts[0] == "background" and (parts[1] == backgrounds.current or (parts[1] == "none" and backgrounds.current.is_empty())))
		(_buttons[key] as Button).modulate = Color(1.0, 0.85, 0.35) if active else Color.WHITE

## the expression editor (menu button, or ?editor in the URL); the menu is hidden while it is open
func open_editor() -> void:
	if editor == null:
		return
	_menu_root.visible = false
	editor.open()

## the presets from the server replace the bundled ones (an empty answer is ignored)
func _on_server_presets(presets: Array) -> void:
	if not presets.is_empty():
		engine.set_library(presets)

func _rebuild_expression_row() -> void:
	if _expression_flow == null:
		return
	for key in _buttons.keys():
		if str(key).begins_with("expression:"):
			_buttons.erase(key)
	for child in _expression_flow.get_children():
		child.queue_free()
	_fill_row(_expression_flow, engine.library_order, engine.play, "expression")
	_refresh_active()

func _add_row(title: String, names: Array, callback: Callable, kind := "") -> HFlowContainer:
	if not title.is_empty():
		var label := Label.new()
		label.text = title
		label.add_theme_color_override("font_shadow_color", Color(1, 1, 1, 0.6))
		_bar.add_child(label)
	var flow := HFlowContainer.new()
	_bar.add_child(flow)
	_fill_row(flow, names, callback, kind)
	return flow

func _fill_row(flow: HFlowContainer, names: Array, callback: Callable, kind: String) -> void:
	for item in names:
		var b := Button.new()
		b.text = item
		b.custom_minimum_size = Vector2(100, 48)
		b.pressed.connect(callback.bind(item))
		flow.add_child(b)
		if not kind.is_empty():
			_buttons[kind + ":" + item] = b
