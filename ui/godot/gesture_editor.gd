class_name GestureEditor
extends PanelContainer
## The gesture editor: sliders for the angles of the FINAL pose of a gesture (arm, hand, fingers, torso). The character moves from the neutral pose to
## that pose in "reach" seconds, holds it for "hold" seconds and eases back; there are no keyframes to record (see ui/README.md, "Gestures from angles").
##
## - The pose is shown live while a slider moves. "Play" shows the whole motion from the neutral pose, with the face of the gesture.
## - One arm is edited at a time (right or left of the character); with "Mirror" on (the default) the other arm gets the same angles.
## - Only angles that differ from neutral are stored, so an arm that was not touched stays relaxed.
## - Gestures are saved on MIA's server like presets (same token); the sliders come from presets/pose_model.json (a copy of pose_model.py).

signal closed
## the "Expressions" button: the page switches to the expression editor
signal expressions_requested

const MODEL_FILE := "res://presets/pose_model.json"
const NEW_ENTRY := "(new gesture)"
const NO_FACE := "(no face)"
const SLIDER_HEIGHT := 40
const FINGER_MODES := ["relaxed", "open", "fist", "point", "custom"]
const FINGER_KEYS := ["thumb", "index", "middle", "ring", "little"]
## percent closed per finger of the named poses: where the finger sliders start when the mode changes to "custom"
const FINGER_PERCENT := {
	"relaxed": {"thumb": 10, "index": 15, "middle": 20, "ring": 22, "little": 25},
	"open": {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "little": 0},
	"fist": {"thumb": 100, "index": 100, "middle": 100, "ring": 100, "little": 100},
	"point": {"thumb": 40, "index": 0, "middle": 100, "ring": 100, "little": 100},
}

var engine: ExpressionEngine
var api: PresetApi
var loaded_name := ""        # gesture that is loaded into the sliders ("" = a new one)
var dirty := false
var mirror := true
var side := "R"              # the arm the sliders show: "R" = the character's right (the viewer's left)
var pose := {}               # only what differs from neutral: {"R": {param: value, "fingers": ...}, "L": {...}, "torso": {...}}
var reach := 0.6
var hold := 1.5

var _spec := {}              # parameter -> definition (min, max, neutral, label, description, group) from pose_model.json
var _timing := {}
var _rows := {}              # parameter -> {"row", "slider", "value"} (arm, hand and torso sliders)
var _finger_rows := {}       # "thumb" ... -> {"row", "slider", "value"}
var _timing_rows := {}       # "reach" / "hold"
var _sections := {}
var _pending_select := ""
var _delete_armed := false
var _grabber: ImageTexture
var _grabber_active: ImageTexture
var _name_regex := RegEx.create_from_string("^[A-Za-z0-9_-]{1,40}$")

var _picker: OptionButton
var _side_option: OptionButton
var _mirror_check: CheckButton
var _finger_option: OptionButton
var _finger_box: VBoxContainer
var _face_option: OptionButton
var _name_edit: LineEdit
var _description_edit: LineEdit
var _status: Label
var _hint: Label
var _token_row: HBoxContainer
var _token_edit: LineEdit
var _play_button: Button
var _save_new_button: Button
var _overwrite_button: Button
var _rename_button: Button
var _delete_button: Button
var _delete_timer: Timer

func setup(expression_engine: ExpressionEngine, preset_api: PresetApi) -> void:
	engine = expression_engine
	api = preset_api
	_load_model()
	_build()
	engine.gestures.library_changed.connect(_on_library_changed)
	engine.gestures.gesture_finished.connect(_on_gesture_finished)
	api.availability_changed.connect(func(_a): _on_availability())
	api.operation_done.connect(_on_operation_done)
	api.token_changed.connect(func(t): _token_edit.text = t)
	for field in [_name_edit, _description_edit, _token_edit]:
		(field as LineEdit).focus_entered.connect(HostBridge.focus_canvas)
	get_viewport().size_changed.connect(_update_layout)
	visible = false
	_on_library_changed()
	_on_availability()
	_update_layout()

func open() -> void:
	visible = true
	_update_layout()
	_refresh_buttons()
	_preview()

func close() -> void:
	engine.gestures.end_preview()
	visible = false
	closed.emit()

# --- the model: which sliders there are ---------------------------------------------------------------------

func _load_model() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(MODEL_FILE))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("cannot read " + MODEL_FILE)
		return
	for group in ["arm", "torso"]:
		for entry in parsed.get(group, []):
			_spec[entry["name"]] = entry
	_timing = parsed.get("timing", {})

func neutral(param: String) -> float:
	return float(_spec[param]["neutral"])

## the value a slider shows: what the pose says, else neutral (arm parameters of the arm that is shown)
func value_of(param: String) -> float:
	var part: String = "torso" if str(_spec[param]["group"]) == "torso" else side
	return float((pose.get(part, {}) as Dictionary).get(param, neutral(param)))

func _other(s: String) -> String:
	return "L" if s == "R" else "R"

# --- building the panel -----------------------------------------------------------------------------------------

func _build() -> void:
	var look := Theme.new()
	look.default_font_size = 18
	theme = look
	var background := StyleBoxFlat.new()
	background.bg_color = Color(0.11, 0.12, 0.16, 0.96)
	background.corner_radius_top_left = 14
	background.corner_radius_top_right = 14
	add_theme_stylebox_override("panel", background)
	_grabber = _circle(16, Color(0.30, 0.55, 0.95))
	_grabber_active = _circle(16, Color(0.95, 0.65, 0.20))
	var margin := MarginContainer.new()
	for edge in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + edge, 10)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 6)
	margin.add_child(root)

	var header := HBoxContainer.new()
	root.add_child(header)
	var title := Label.new()
	title.text = "Gesture editor"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	header.add_child(_button("Expressions", func(): expressions_requested.emit(), "expressions_button"))
	header.add_child(_button("Close", close, "close_button"))

	var picker_row := HBoxContainer.new()
	root.add_child(picker_row)
	_picker = OptionButton.new()
	_picker.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_picker.custom_minimum_size = Vector2(0, 44)
	_picker.item_selected.connect(_on_picker_selected)
	picker_row.add_child(_picker)
	picker_row.add_child(_button("Neutral", reset_to_neutral, "neutral_button"))

	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_status)
	_hint = Label.new()
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint.add_theme_font_size_override("font_size", 14)
	_hint.add_theme_color_override("font_color", Color(0.75, 0.75, 0.8))
	_hint.text = "Set the angles of the final pose. The character moves there from the neutral pose."
	root.add_child(_hint)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)
	_build_arm(content)
	_build_hand(content)
	_build_torso(content)
	_build_details(content)

	var buttons := HFlowContainer.new()
	root.add_child(buttons)
	_play_button = _button("Play", play, "play_button")
	_save_new_button = _button("Save as new", _save_new, "save_new_button")
	_overwrite_button = _button("Overwrite", _overwrite, "overwrite_button")
	_rename_button = _button("Rename", _rename, "rename_button")
	_delete_button = _button("Delete", _delete, "delete_button")
	for b in [_play_button, _save_new_button, _overwrite_button, _rename_button, _delete_button]:
		buttons.add_child(b)
	_delete_timer = Timer.new()
	_delete_timer.one_shot = true
	_delete_timer.wait_time = 3.0
	_delete_timer.timeout.connect(_disarm_delete)
	add_child(_delete_timer)

	_token_row = HBoxContainer.new()
	var token_label := Label.new()
	token_label.text = "Token"
	_token_row.add_child(token_label)
	_token_edit = LineEdit.new()
	_token_edit.secret = true
	_token_edit.placeholder_text = "needed to change gestures"
	_token_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_token_edit.text = api.token
	_token_edit.text_changed.connect(func(t):
		api.token = t.strip_edges()
		PresetApi.store_token(api.token))
	_token_row.add_child(_token_edit)
	root.add_child(_token_row)

func _make_section(parent: VBoxContainer, key: String, title: String, expanded: bool) -> VBoxContainer:
	var header := Button.new()
	header.text = title
	header.toggle_mode = true
	header.button_pressed = expanded
	header.alignment = HORIZONTAL_ALIGNMENT_LEFT
	header.custom_minimum_size = Vector2(0, 44)
	var box := VBoxContainer.new()
	box.visible = expanded
	header.toggled.connect(func(on): box.visible = on)
	parent.add_child(header)
	parent.add_child(box)
	_sections[key] = {"header": header, "box": box}
	return box

## a slider row for one parameter of the pose model
func _param_row(param: String, unit: String) -> Dictionary:
	var info: Dictionary = _spec[param]
	var row := _slider_row(str(info["label"]), float(info["min"]), float(info["max"]), 1.0, str(info["description"]))
	(row["slider"] as HSlider).value_changed.connect(_on_param.bind(param))
	(row["slider"] as HSlider).drag_started.connect(func(): _hint.text = "%s: %s" % [info["label"], info["description"]])
	row["unit"] = unit
	_rows[param] = row
	return row

func _build_arm(parent: VBoxContainer) -> void:
	var box := _make_section(parent, "arm", "Arm", true)
	var choose := HBoxContainer.new()
	box.add_child(choose)
	_side_option = OptionButton.new()
	_side_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_side_option.custom_minimum_size = Vector2(0, 44)
	_side_option.add_item("Right arm (the viewer's left)")
	_side_option.add_item("Left arm (the viewer's right)")
	_side_option.item_selected.connect(_on_side_selected)
	choose.add_child(_side_option)
	_mirror_check = CheckButton.new()
	_mirror_check.text = "Mirror"
	_mirror_check.button_pressed = true
	_mirror_check.tooltip_text = "On: both arms get the same angles (symmetric poses). Off: each arm is set on its own."
	_mirror_check.toggled.connect(_on_mirror_toggled)
	choose.add_child(_mirror_check)
	for param in ["upper_raise", "upper_direction", "elbow_bend", "elbow_turn"]:
		box.add_child(_param_row(param, "°")["row"])

func _build_hand(parent: VBoxContainer) -> void:
	var box := _make_section(parent, "hand", "Hand and fingers", true)
	for param in ["hand_turn", "wrist"]:
		box.add_child(_param_row(param, "°")["row"])
	_finger_option = OptionButton.new()
	_finger_option.custom_minimum_size = Vector2(0, 44)
	for mode in FINGER_MODES:
		_finger_option.add_item("Fingers: " + mode)
	_finger_option.item_selected.connect(_on_finger_mode)
	box.add_child(_finger_option)
	_finger_box = VBoxContainer.new()
	_finger_box.visible = false
	box.add_child(_finger_box)
	for key in FINGER_KEYS:
		var row := _slider_row(str(key).capitalize(), 0.0, 100.0, 1.0, "0 = open, 100 = closed")
		(row["slider"] as HSlider).value_changed.connect(_on_finger_slider.bind(key))
		_finger_box.add_child(row["row"])
		_finger_rows[key] = row

func _build_torso(parent: VBoxContainer) -> void:
	var box := _make_section(parent, "torso", "Torso", false)
	for param in ["torso_lean", "torso_side", "torso_turn"]:
		box.add_child(_param_row(param, "°")["row"])

func _build_details(parent: VBoxContainer) -> void:
	var box := _make_section(parent, "details", "Timing, face and name", true)
	for key in ["reach", "hold"]:
		var info: Dictionary = _timing.get(key, {"min": 0.0, "max": 5.0, "default": 1.0, "description": ""})
		var row := _slider_row("Reach (s)" if key == "reach" else "Hold (s)", float(info["min"]), float(info["max"]), 0.05, str(info["description"]))
		(row["slider"] as HSlider).value_changed.connect(_on_timing.bind(key))
		(row["slider"] as HSlider).drag_started.connect(func(): _hint.text = str(info["description"]))
		box.add_child(row["row"])
		_timing_rows[key] = row
	_face_option = OptionButton.new()
	_face_option.custom_minimum_size = Vector2(0, 44)
	_face_option.tooltip_text = "the face (expression preset) that goes with the gesture"
	_face_option.item_selected.connect(func(_i): _changed())
	box.add_child(_face_option)
	_name_edit = _line("Name (letters, digits, - and _)")
	_name_edit.text_changed.connect(func(_t): _refresh_buttons())
	box.add_child(_name_edit)
	_description_edit = _line("Description")
	_description_edit.text_changed.connect(func(_t): _changed(false))
	box.add_child(_description_edit)
	_fill_faces()

func _slider_row(label_text: String, min_value: float, max_value: float, step: float, tip: String) -> Dictionary:
	var row := HBoxContainer.new()
	row.tooltip_text = tip
	var label := Label.new()
	label.text = label_text
	label.custom_minimum_size = Vector2(150, 0)
	label.clip_text = true
	label.tooltip_text = tip
	row.add_child(label)
	var slider := HSlider.new()
	slider.min_value = min_value
	slider.max_value = max_value
	slider.step = step
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size = Vector2(0, SLIDER_HEIGHT)
	slider.add_theme_icon_override("grabber", _grabber)
	slider.add_theme_icon_override("grabber_highlight", _grabber_active)
	slider.add_theme_icon_override("grabber_disabled", _grabber)
	row.add_child(slider)
	var value := Label.new()
	value.custom_minimum_size = Vector2(62, 0)
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value.text = "0"
	row.add_child(value)
	return {"row": row, "slider": slider, "value": value}

func _button(text: String, callback: Callable, button_name := "") -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 44)
	b.pressed.connect(callback)
	if not button_name.is_empty():
		b.name = button_name
	return b

func _line(placeholder: String) -> LineEdit:
	var edit := LineEdit.new()
	edit.placeholder_text = placeholder
	edit.custom_minimum_size = Vector2(0, 44)
	return edit

static func _circle(radius: int, color: Color) -> ImageTexture:
	var size := radius * 2
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	for y in size:
		for x in size:
			var d := Vector2(x + 0.5 - radius, y + 0.5 - radius).length()
			image.set_pixel(x, y, Color(color, clampf(radius - d, 0.0, 1.0)))
	return ImageTexture.create_from_image(image)

## panel at the right on wide screens, bottom sheet on phones (like the expression editor)
func _update_layout() -> void:
	if not is_inside_tree():
		return
	var area := get_viewport().get_visible_rect().size
	custom_minimum_size = Vector2(300, 200)
	if area.x < 700.0 or area.y > area.x:
		anchor_left = 0.0
		anchor_right = 1.0
		anchor_top = 1.0
		anchor_bottom = 1.0
		offset_left = 0.0
		offset_right = 0.0
		offset_bottom = 0.0
		offset_top = -area.y * 0.62
	else:
		anchor_left = 1.0
		anchor_right = 1.0
		anchor_top = 0.0
		anchor_bottom = 1.0
		offset_left = -clampf(area.x * 0.38, 360.0, 520.0)
		offset_right = 0.0
		offset_top = 0.0
		offset_bottom = 0.0

func _fill_faces() -> void:
	var selected := ""
	if _face_option.selected > 0:
		selected = _face_option.get_item_text(_face_option.selected)
	_face_option.clear()
	_face_option.add_item(NO_FACE)
	for n in engine.library_order:
		_face_option.add_item(n)
	for i in _face_option.item_count:
		if _face_option.get_item_text(i) == selected:
			_face_option.select(i)

func face() -> String:
	return _face_option.get_item_text(_face_option.selected) if _face_option.selected > 0 else ""

# --- the sliders -----------------------------------------------------------------------------------------------------

func _format(param: String, v: float) -> String:
	return "%d°" % int(roundf(v))

## stores one angle: values equal to neutral are not stored (the arm stays relaxed); the other arm gets it too with Mirror
func _put(part: String, key: String, v, neutral_value) -> void:
	var d: Dictionary = pose.get(part, {})
	if neutral_value != null and is_equal_approx(float(v), float(neutral_value)):
		d.erase(key)
	else:
		d[key] = v
	if d.is_empty():
		pose.erase(part)
	else:
		pose[part] = d

func _on_param(v: float, param: String) -> void:
	if str(_spec[param]["group"]) == "torso":
		_put("torso", param, v, neutral(param))
	else:
		_put(side, param, v, neutral(param))
		if mirror:
			_put(_other(side), param, v, neutral(param))
	(_rows[param]["value"] as Label).text = _format(param, v)
	_changed()

func _on_timing(v: float, key: String) -> void:
	if key == "reach":
		reach = v
	else:
		hold = v
	(_timing_rows[key]["value"] as Label).text = "%.2f s" % v
	_changed()

func _on_side_selected(index: int) -> void:
	side = "R" if index == 0 else "L"
	_sync_sliders()

func _on_mirror_toggled(on: bool) -> void:
	mirror = on
	if on:
		# both arms get what the arm that is shown has
		if pose.has(side):
			pose[_other(side)] = (pose[side] as Dictionary).duplicate(true)
		else:
			pose.erase(_other(side))
		_changed()

func _finger_spec():
	return (pose.get(side, {}) as Dictionary).get("fingers", "relaxed")

func _set_fingers(spec) -> void:
	for part in [side] + ([_other(side)] if mirror else []):
		var d: Dictionary = pose.get(part, {})
		if typeof(spec) == TYPE_STRING and spec == "relaxed":
			d.erase("fingers")
		else:
			d["fingers"] = spec.duplicate(true) if typeof(spec) == TYPE_DICTIONARY else spec
		if d.is_empty():
			pose.erase(part)
		else:
			pose[part] = d

func _on_finger_mode(index: int) -> void:
	var mode: String = FINGER_MODES[index]
	if mode == "custom":
		var current = _finger_spec()
		var start: Dictionary = (current as Dictionary).duplicate() if typeof(current) == TYPE_DICTIONARY else (FINGER_PERCENT[str(current)] as Dictionary).duplicate()
		_set_fingers(start)
	else:
		_set_fingers(mode)
	_sync_fingers()
	_changed()

func _on_finger_slider(v: float, key: String) -> void:
	var current = _finger_spec()
	if typeof(current) != TYPE_DICTIONARY:
		return
	var spec: Dictionary = (current as Dictionary).duplicate()
	spec[key] = v
	_set_fingers(spec)
	(_finger_rows[key]["value"] as Label).text = "%d%%" % int(roundf(v))
	_changed()

func _sync_fingers() -> void:
	var spec = _finger_spec()
	if typeof(spec) == TYPE_DICTIONARY:
		_finger_option.select(FINGER_MODES.find("custom"))
		_finger_box.visible = true
		for key in FINGER_KEYS:
			var v := float((spec as Dictionary).get(key, FINGER_PERCENT["relaxed"][key]))
			(_finger_rows[key]["slider"] as HSlider).set_value_no_signal(v)
			(_finger_rows[key]["value"] as Label).text = "%d%%" % int(roundf(v))
	else:
		_finger_option.select(maxi(0, FINGER_MODES.find(str(spec))))
		_finger_box.visible = false

## puts the state into all sliders (no signals: nothing is recorded as a change)
func _sync_sliders() -> void:
	for param in _rows:
		var v := value_of(param)
		(_rows[param]["slider"] as HSlider).set_value_no_signal(v)
		(_rows[param]["value"] as Label).text = _format(param, v)
	_sync_fingers()
	for key in ["reach", "hold"]:
		var v := reach if key == "reach" else hold
		(_timing_rows[key]["slider"] as HSlider).set_value_no_signal(v)
		(_timing_rows[key]["value"] as Label).text = "%.2f s" % v
	_side_option.select(0 if side == "R" else 1)
	_mirror_check.set_pressed_no_signal(mirror)

func _changed(preview := true) -> void:
	dirty = true
	if preview:
		_preview()
	_refresh_buttons()
	if not loaded_name.is_empty():
		_set_status("Unsaved changes to '%s'." % loaded_name)

# --- the document, preview and play ---------------------------------------------------------------------------------------

func doc(doc_name: String) -> Dictionary:
	return {"name": doc_name, "description": _description_edit.text.strip_edges(), "expression": face(), "reach": reach, "hold": hold,
			"pose": pose.duplicate(true), "source": "manual"}

## shows the final pose and keeps it (nothing set: the arms are relaxed)
func _preview() -> void:
	if not visible:
		return
	if pose.is_empty():
		engine.gestures.end_preview()
	else:
		engine.gestures.preview(doc(GestureEngine.PREVIEW))

## the whole motion from the neutral pose, with the face of the gesture; afterwards the pose is shown again
func play() -> void:
	if not engine.gestures.try_doc(doc(loaded_name if not loaded_name.is_empty() else "try")):
		_set_status("Set at least one angle first.", true)
		return
	_set_status("Playing: %.2f s to the pose, held for %.2f s." % [reach, hold])

func _on_gesture_finished(finished: String) -> void:
	if finished == GestureEngine.TRY and visible:
		_preview()

func reset_to_neutral() -> void:
	pose.clear()
	dirty = true
	_sync_sliders()
	_preview()
	_set_status("All angles are neutral (not saved yet).")
	_refresh_buttons()

func new_gesture() -> void:
	pose.clear()
	reach = float(_timing.get("reach", {}).get("default", 0.6))
	hold = float(_timing.get("hold", {}).get("default", 1.5))
	side = "R"
	mirror = true
	_name_edit.text = ""
	_description_edit.text = ""
	_face_option.select(0)
	loaded_name = ""
	dirty = false
	_select_option("")
	_sync_sliders()
	_preview()
	_set_status("New gesture: set the angles, enter a name and press 'Save as new'.")
	_refresh_buttons()

func load_gesture(gesture_name: String) -> bool:
	if not engine.gestures.pose_docs.has(gesture_name):
		return false
	var d: Dictionary = engine.gestures.pose_docs[gesture_name]
	pose = (d.get("pose", {}) as Dictionary).duplicate(true)
	reach = float(d.get("reach", 0.6))
	hold = float(d.get("hold", 1.5))
	side = "R"
	mirror = _arms_equal()
	_name_edit.text = gesture_name
	_description_edit.text = str(d.get("description", ""))
	_face_option.select(0)
	for i in _face_option.item_count:
		if _face_option.get_item_text(i) == str(d.get("expression", "")):
			_face_option.select(i)
	loaded_name = gesture_name
	dirty = false
	_select_option(gesture_name)
	_sync_sliders()
	_preview()
	_set_status("Loaded '%s'." % gesture_name)
	_refresh_buttons()
	return true

## both arms have the same angles (the mirror switch starts on for such gestures)
func _arms_equal() -> bool:
	return JSON.stringify(pose.get("R", {})) == JSON.stringify(pose.get("L", {}))

# --- the list of gestures -----------------------------------------------------------------------------------------------------

func _on_picker_selected(index: int) -> void:
	if index == 0:
		new_gesture()
	else:
		load_gesture(_picker.get_item_text(index))

func _select_option(gesture_name: String) -> void:
	for i in _picker.item_count:
		if _picker.get_item_text(i) == (gesture_name if not gesture_name.is_empty() else NEW_ENTRY):
			_picker.select(i)
			return

func _on_library_changed() -> void:
	_fill_faces()
	_picker.clear()
	_picker.add_item(NEW_ENTRY)
	var names: Array = engine.gestures.pose_docs.keys()
	names.sort()
	for n in names:
		_picker.add_item(n)
	if not _pending_select.is_empty() and engine.gestures.pose_docs.has(_pending_select):
		var target := _pending_select
		_pending_select = ""
		load_gesture(target)
	elif not loaded_name.is_empty() and not engine.gestures.pose_docs.has(loaded_name):
		var gone := loaded_name
		loaded_name = ""
		_select_option("")
		_set_status("'%s' was removed (on another device?). The sliders stay as they are." % gone)
	else:
		_select_option(loaded_name)
	_refresh_buttons()

# --- saving ---------------------------------------------------------------------------------------------------------------------

func _valid_name(text: String) -> bool:
	return _name_regex.search(text) != null

func _save_new() -> void:
	var n := _name_edit.text.strip_edges()
	if not _valid_name(n):
		_set_status("Name: 1-40 letters, digits, - or _ (no spaces).", true)
		return
	if engine.gestures.library.has(n):
		_set_status("'%s' exists already: load it and use 'Overwrite', or choose another name." % n, true)
		return
	if pose.is_empty():
		_set_status("Set at least one angle first.", true)
		return
	_pending_select = n
	_disarm_delete()
	api.create_gesture(doc(n))

func _overwrite() -> void:
	if loaded_name.is_empty():
		_set_status("Load a gesture first, or use 'Save as new'.", true)
		return
	_pending_select = loaded_name
	_disarm_delete()
	api.update_gesture(loaded_name, doc(loaded_name))

func _rename() -> void:
	var n := _name_edit.text.strip_edges()
	if loaded_name.is_empty():
		_set_status("Load a gesture first.", true)
	elif not _valid_name(n):
		_set_status("Name: 1-40 letters, digits, - or _ (no spaces).", true)
	elif n == loaded_name:
		_set_status("Enter the new name in the name field.", true)
	else:
		_pending_select = n
		_disarm_delete()
		api.update_gesture(loaded_name, doc(n))

## two presses: the first arms the button for 3 seconds
func _delete() -> void:
	if loaded_name.is_empty():
		_set_status("Load a gesture first.", true)
		return
	if not _delete_armed:
		_delete_armed = true
		_delete_button.text = "Really delete?"
		_delete_timer.start()
		return
	_disarm_delete()
	_pending_select = ""
	api.delete_gesture(loaded_name)

func _disarm_delete() -> void:
	_delete_armed = false
	_delete_timer.stop()
	if _delete_button != null:
		_delete_button.text = "Delete"

func _on_operation_done(kind: String, ok: bool, message: String, data: Dictionary) -> void:
	if not kind.begins_with("gesture_"):
		return
	_set_status(message, not ok)
	_token_row.visible = api.token_required
	if not ok:
		_pending_select = ""
		return
	if kind == "gesture_delete":
		loaded_name = ""
	else:
		dirty = false
		loaded_name = str((data.get("gesture", {}) as Dictionary).get("name", loaded_name))
	api.refresh()      # the answer replaces the gestures and selects _pending_select

func _on_availability() -> void:
	_token_row.visible = api.available and api.token_required
	if not api.available:
		_set_status("Offline: you can try angles and play them, saving needs the server.", true)
	elif loaded_name.is_empty():
		_set_status("Connected to the server. Gestures are shared with all devices.")
	_refresh_buttons()

func _refresh_buttons() -> void:
	if _save_new_button == null:
		return
	var online := api.available
	var typed := _name_edit.text.strip_edges()
	var has_pose := not pose.is_empty()
	_play_button.disabled = not has_pose
	_save_new_button.disabled = not online or not _valid_name(typed) or not has_pose
	_overwrite_button.disabled = not online or loaded_name.is_empty() or not has_pose
	_rename_button.disabled = not online or loaded_name.is_empty() or not _valid_name(typed) or typed == loaded_name or not has_pose
	_delete_button.disabled = not online or loaded_name.is_empty()
	_token_row.visible = online and api.token_required

func _set_status(text: String, is_error := false) -> void:
	_status.text = text
	_status.add_theme_color_override("font_color", Color(1.0, 0.55, 0.5) if is_error else Color(0.7, 0.9, 0.7))
