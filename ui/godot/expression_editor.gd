class_name ExpressionEditor
extends PanelContainer
## Slider editor for expressions (ui/REQUIREMENTS.md 4.5): one slider per shape key, grouped (eyes, brows, mouth,
## other) with a filter, bone sliders, load / reset / save as new / overwrite / rename / delete. The face
## changes live while sliders move. Presets are saved on the server (PresetApi), so every device sees them.
## Made for touch: large sliders, a panel at the right (wide screens) or a bottom sheet (phones), closable.

signal closed

const CATEGORY_TITLES := {"eyes": "Eyes", "brows": "Brows", "mouth": "Mouth", "other": "Other (teeth, whole face)"}
const BONES := ["head_pitch", "head_yaw", "head_roll", "eye_pitch", "eye_yaw"]
const BONE_LIMIT := 45.0
const SLIDER_HEIGHT := 40
const EDIT_NAME := "_editing"
const NEW_ENTRY := "(new preset)"
const NO_GESTURE := "(no gesture)"

var engine: ExpressionEngine
var api: PresetApi
var loaded_name := ""        # preset that is loaded into the sliders ("" = a new one)
var dirty := false           # sliders changed since loading/saving

var _meta := {}              # shape key -> {"category", "description"}
var _rows := {}              # shape key -> {"row", "slider", "value", "category"}
var _sections := {}          # category -> {"header": Button, "box": VBoxContainer}
var _bone_rows := {}         # bone param -> {"slider", "value"}
var _weights := {}
var _bones := {}
var _loaded_source := "manual"
var _pending_select := ""
var _delete_armed := false
var _gen := {}               # the expression of the language model that is shown: {"id", "preset"} (empty = none)
var _before_gen := ""        # expression that was shown before the request (comes back when it is rejected)
var _gen_busy := false
var _feedback_after_save := false

var _preset_option: OptionButton
var _gesture_option: OptionButton
var _speaking_check: CheckBox
var _filter: LineEdit
var _hint: Label
var _status: Label
var _name_edit: LineEdit
var _description_edit: LineEdit
var _tags_edit: LineEdit
var _describe_edit: LineEdit
var _generate_button: Button
var _result_row: HFlowContainer
var _token_row: HBoxContainer
var _token_edit: LineEdit
var _save_new_button: Button
var _overwrite_button: Button
var _rename_button: Button
var _delete_button: Button
var _delete_timer: Timer
var _grabber: ImageTexture
var _grabber_active: ImageTexture
var _name_regex := RegEx.create_from_string("^[A-Za-z0-9_-]{1,40}$")

func setup(expression_engine: ExpressionEngine, preset_api: PresetApi) -> void:
	engine = expression_engine
	api = preset_api
	_load_meta()
	_build()
	engine.library_changed.connect(_on_library_changed)
	api.availability_changed.connect(func(_a): _on_availability())
	api.operation_done.connect(_on_operation_done)
	api.generated.connect(_on_generated)
	api.token_changed.connect(func(t): _token_edit.text = t)
	for field in [_describe_edit, _name_edit, _description_edit, _tags_edit, _token_edit, _filter]:
		(field as LineEdit).focus_entered.connect(HostBridge.focus_canvas)   # typing needs the keyboard focus on the canvas in the browser
	api.matched.connect(_on_matched)
	get_viewport().size_changed.connect(_update_layout)
	visible = false
	_on_library_changed()
	_on_availability()
	_update_layout()

func open() -> void:
	visible = true
	_update_layout()
	_refresh_buttons()

func close() -> void:
	visible = false
	closed.emit()

# --- building the panel ------------------------------------------------------------------------------

func _load_meta() -> void:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://presets/shape_keys.json"))
	if typeof(parsed) == TYPE_DICTIONARY:
		for entry in parsed.get("shape_keys", []):
			_meta[entry["name"]] = {"category": entry["category"], "description": entry.get("description", "")}
	_sections.clear()

func _build() -> void:
	var look := Theme.new()
	look.default_font_size = 18
	theme = look
	var background := StyleBoxFlat.new()   # solid, so the sliders stay readable in front of the character
	background.bg_color = Color(0.11, 0.12, 0.16, 0.96)
	background.corner_radius_top_left = 14
	background.corner_radius_top_right = 14
	add_theme_stylebox_override("panel", background)
	_grabber = _circle(16, Color(0.30, 0.55, 0.95))
	_grabber_active = _circle(16, Color(0.95, 0.65, 0.20))
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 10)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 6)
	margin.add_child(root)

	var header := HBoxContainer.new()
	root.add_child(header)
	var title := Label.new()
	title.text = "Expression editor"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	header.add_child(_button("Close", close, "close_button"))

	var picker := HBoxContainer.new()
	root.add_child(picker)
	_preset_option = OptionButton.new()
	_preset_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_preset_option.custom_minimum_size = Vector2(0, 44)
	_preset_option.item_selected.connect(_on_preset_selected)
	picker.add_child(_preset_option)
	picker.add_child(_button("Neutral", reset_to_neutral, "reset_button"))

	# describe an expression in words: the language model makes it, the closest preset is shown while it works
	var describe := HBoxContainer.new()
	root.add_child(describe)
	_describe_edit = LineEdit.new()
	_describe_edit.placeholder_text = "Describe an expression, e.g. surprised but hiding it"
	_describe_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_describe_edit.custom_minimum_size = Vector2(0, 44)
	_describe_edit.clear_button_enabled = true
	_describe_edit.max_length = 300
	_describe_edit.text_submitted.connect(func(_t): _generate())
	_describe_edit.text_changed.connect(func(_t): _refresh_buttons())
	describe.add_child(_describe_edit)
	_generate_button = _button("Generate", _generate, "generate_button")
	describe.add_child(_generate_button)
	_result_row = HFlowContainer.new()
	_result_row.visible = false
	root.add_child(_result_row)
	_result_row.add_child(_button("Keep", _keep, "keep_button"))
	_result_row.add_child(_button("Edit", _edit_generated, "edit_button"))
	_result_row.add_child(_button("Reject", _reject_generated, "reject_button"))

	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_status)

	_filter = LineEdit.new()
	_filter.placeholder_text = "Filter sliders (e.g. joy, eye, mouth) ..."
	_filter.clear_button_enabled = true
	_filter.custom_minimum_size = Vector2(0, 44)
	_filter.text_changed.connect(_apply_filter)
	root.add_child(_filter)
	_hint = Label.new()
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hint.add_theme_font_size_override("font_size", 14)
	_hint.add_theme_color_override("font_color", Color(0.75, 0.75, 0.8))
	_hint.text = "Touch a slider to see what it does."
	root.add_child(_hint)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(content)
	_build_sections(content)
	_build_details(content)

	_name_edit = _line("Name (letters, digits, - and _)")
	_name_edit.text_changed.connect(func(_t): _refresh_buttons())
	root.add_child(_name_edit)

	var buttons := HFlowContainer.new()
	root.add_child(buttons)
	_save_new_button = _button("Save as new", _save_new, "save_new_button")
	_overwrite_button = _button("Overwrite", _overwrite, "overwrite_button")
	_rename_button = _button("Rename", _rename, "rename_button")
	_delete_button = _button("Delete", _delete, "delete_button")
	for b in [_save_new_button, _overwrite_button, _rename_button, _delete_button]:
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
	_token_edit.placeholder_text = "needed to change presets"
	_token_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_token_edit.text = api.token
	_token_edit.text_changed.connect(func(t):
		api.token = t.strip_edges()
		PresetApi.store_token(api.token))
	_token_row.add_child(_token_edit)
	root.add_child(_token_row)

## header button + box of a collapsible group
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

## eyes, brows, mouth, head and eyes (bones), and last (collapsed) teeth and whole-face keys
func _build_sections(parent: VBoxContainer) -> void:
	var order := ["eyes", "brows", "mouth", "bones", "other"]
	for key in order:
		var title: String = "Head and eyes (degrees)" if key == "bones" else CATEGORY_TITLES.get(key, str(key).capitalize())
		_make_section(parent, key, title, key != "other")
	for key in engine.get_shape_names():
		var info: Dictionary = _meta.get(key, {"category": "other", "description": ""})
		var category: String = info["category"] if _sections.has(info["category"]) and info["category"] != "bones" else "other"
		var row := _slider_row(key.trim_prefix("Fcl_"), 0.0, 1.0, 0.01, info["description"])
		(row["slider"] as HSlider).value_changed.connect(_on_weight.bind(key))
		(row["slider"] as HSlider).drag_started.connect(func(): _hint.text = "%s: %s" % [key, info["description"]])
		(_sections[category]["box"] as VBoxContainer).add_child(row["row"])
		row["category"] = category
		_rows[key] = row
	var hints := {"head_pitch": "nod: + looks down", "head_yaw": "turn: + to the viewer's right", "head_roll": "tilt the head",
			"eye_pitch": "gaze: + down", "eye_yaw": "gaze: + to the viewer's right"}
	for bone in BONES:
		var row := _slider_row(bone, -BONE_LIMIT, BONE_LIMIT, 0.5, hints[bone])
		(row["slider"] as HSlider).value_changed.connect(_on_bone.bind(bone))
		(row["slider"] as HSlider).drag_started.connect(func(): _hint.text = "%s: %s" % [bone, hints[bone]])
		(_sections["bones"]["box"] as VBoxContainer).add_child(row["row"])
		_bone_rows[bone] = row

## gesture, speaking mouth, description and tags
func _build_details(parent: VBoxContainer) -> void:
	var box := _make_section(parent, "details", "Gesture and details", true)
	var gesture_row := HBoxContainer.new()
	box.add_child(gesture_row)
	_gesture_option = OptionButton.new()
	_gesture_option.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_gesture_option.custom_minimum_size = Vector2(0, 44)
	engine.gestures.library_changed.connect(_fill_gestures)
	_gesture_option.add_item(NO_GESTURE)
	for g in engine.gestures.library_order:
		_gesture_option.add_item(g)
	_gesture_option.item_selected.connect(func(_i): _changed())
	gesture_row.add_child(_gesture_option)
	gesture_row.add_child(_button("Play", _play_gesture, "play_gesture_button"))
	_speaking_check = CheckBox.new()
	_speaking_check.text = "talks"
	_speaking_check.toggled.connect(func(_on): _changed())
	gesture_row.add_child(_speaking_check)
	_description_edit = _line("Description")
	box.add_child(_description_edit)
	_tags_edit = _line("Tags, separated by commas")
	box.add_child(_tags_edit)

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
	value.custom_minimum_size = Vector2(52, 0)
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

## a filled circle as slider handle: big enough for fingers
static func _circle(radius: int, color: Color) -> ImageTexture:
	var size := radius * 2
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	for y in size:
		for x in size:
			var d := Vector2(x + 0.5 - radius, y + 0.5 - radius).length()
			image.set_pixel(x, y, Color(color, clampf(radius - d, 0.0, 1.0)))
	return ImageTexture.create_from_image(image)

# --- layout: panel at the right on wide screens, bottom sheet on phones ----------------------------------

func _update_layout() -> void:
	if not is_inside_tree():
		return
	var area := get_viewport().get_visible_rect().size
	custom_minimum_size = Vector2(300, 200)
	if area.x < 700.0 or area.y > area.x:
		# phone: bottom sheet over the lower 62 percent
		anchor_left = 0.0
		anchor_right = 1.0
		anchor_top = 1.0
		anchor_bottom = 1.0
		offset_left = 0.0
		offset_right = 0.0
		offset_bottom = 0.0
		offset_top = -area.y * 0.62
	else:
		# wide screen: panel at the right, full height
		anchor_left = 1.0
		anchor_right = 1.0
		anchor_top = 0.0
		anchor_bottom = 1.0
		offset_left = -clampf(area.x * 0.38, 360.0, 520.0)
		offset_right = 0.0
		offset_top = 0.0
		offset_bottom = 0.0

# --- the sliders ----------------------------------------------------------------------------------------------

func _on_weight(value: float, key: String) -> void:
	if value <= 0.0:
		_weights.erase(key)
	else:
		_weights[key] = value
	(_rows[key]["value"] as Label).text = "%.2f" % value
	_changed()

func _on_bone(value: float, bone: String) -> void:
	if is_zero_approx(value):
		_bones.erase(bone)
	else:
		_bones[bone] = value
	(_bone_rows[bone]["value"] as Label).text = "%.1f" % value
	_changed()

func _changed() -> void:
	dirty = true
	_preview()
	_refresh_buttons()
	if not loaded_name.is_empty():
		_set_status("Unsaved changes to '%s'." % loaded_name)

## shows the sliders on the face right away (no gesture: the arms stay where they are)
func _preview() -> void:
	engine.apply_preset(preview_preset(), 0.06, false)

func preview_preset() -> Dictionary:
	return {"name": EDIT_NAME, "weights": _weights.duplicate(), "bones": _bones.duplicate(),
			"gesture": "", "speaking": _speaking_check.button_pressed}

func _sync_sliders() -> void:
	for key in _rows:
		var v: float = _weights.get(key, 0.0)
		(_rows[key]["slider"] as HSlider).set_value_no_signal(v)
		(_rows[key]["value"] as Label).text = "%.2f" % v
	for bone in _bone_rows:
		var b: float = _bones.get(bone, 0.0)
		(_bone_rows[bone]["slider"] as HSlider).set_value_no_signal(b)
		(_bone_rows[bone]["value"] as Label).text = "%.1f" % b

func _apply_filter(text: String) -> void:
	var needle := text.strip_edges().to_lower()
	var filtering := not needle.is_empty()
	var visible_in := {}
	for key in _rows:
		var info: Dictionary = _meta.get(key, {"description": ""})
		var match_: bool = not filtering or key.to_lower().contains(needle) or str(info["description"]).to_lower().contains(needle) \
				or str(_rows[key]["category"]).contains(needle)
		(_rows[key]["row"] as Control).visible = match_
		if match_:
			visible_in[_rows[key]["category"]] = true
	for key in _bone_rows:
		var match_: bool = not filtering or str(key).contains(needle) or "head".contains(needle) or "eye".contains(needle) or "bone".contains(needle)
		(_bone_rows[key]["row"] as Control).visible = match_
		if match_:
			visible_in["bones"] = true
	for category in _sections:
		var header := _sections[category]["header"] as Button
		var box := _sections[category]["box"] as Control
		if category == "details":
			continue
		header.visible = not filtering or visible_in.has(category)
		# while filtering the matching groups are shown open, otherwise the user's open/closed choice counts
		box.visible = header.visible and (header.button_pressed or filtering)

# --- presets: loading, resetting ----------------------------------------------------------------------------------

func load_preset(preset_name: String) -> bool:
	if not engine.library.has(preset_name):
		return false
	_dismiss_generated()
	var p: Dictionary = engine.library[preset_name]
	_weights = (p["weights"] as Dictionary).duplicate()
	_bones = (p["bones"] as Dictionary).duplicate()
	_sync_sliders()
	var gesture_index := 0
	for i in _gesture_option.item_count:
		if _gesture_option.get_item_text(i) == p["gesture"]:
			gesture_index = i
	_gesture_option.select(gesture_index)
	_speaking_check.set_pressed_no_signal(p["speaking"])
	_name_edit.text = preset_name
	_description_edit.text = p["description"]
	_tags_edit.text = ", ".join(PackedStringArray(p["tags"]))
	loaded_name = preset_name
	_loaded_source = p["source"]
	dirty = false
	_select_option(preset_name)
	engine.apply_preset(p, 0.15, false)
	_set_status("Loaded '%s'." % preset_name)
	_refresh_buttons()
	return true

## all sliders to zero (not saved); the loaded preset stays selected, so "Overwrite" would overwrite it
func reset_to_neutral() -> void:
	_weights.clear()
	_bones.clear()
	_sync_sliders()
	_speaking_check.set_pressed_no_signal(false)
	_gesture_option.select(0)
	_preview()
	dirty = true
	_set_status("Sliders reset to neutral (not saved yet).")
	_refresh_buttons()

func start_new() -> void:
	_dismiss_generated()
	_weights.clear()
	_bones.clear()
	_sync_sliders()
	_gesture_option.select(0)
	_speaking_check.set_pressed_no_signal(false)
	_name_edit.text = ""
	_description_edit.text = ""
	_tags_edit.text = ""
	loaded_name = ""
	_loaded_source = "manual"
	dirty = false
	_select_option("")
	engine.apply_preset(preview_preset(), 0.15, false)
	_set_status("New preset: set the sliders, enter a name and press 'Save as new'.")
	_refresh_buttons()

func _on_preset_selected(index: int) -> void:
	if index == 0:
		start_new()
	else:
		load_preset(_preset_option.get_item_text(index))

func _select_option(preset_name: String) -> void:
	for i in _preset_option.item_count:
		if _preset_option.get_item_text(i) == (preset_name if not preset_name.is_empty() else NEW_ENTRY):
			_preset_option.select(i)
			return

## the gesture list of the preset: keeps the selected gesture when it still exists
func _fill_gestures() -> void:
	var selected := ""
	if _gesture_option.selected > 0:
		selected = _gesture_option.get_item_text(_gesture_option.selected)
	_gesture_option.clear()
	_gesture_option.add_item(NO_GESTURE)
	for g in engine.gestures.library_order:
		_gesture_option.add_item(g)
	for i in _gesture_option.item_count:
		if _gesture_option.get_item_text(i) == selected:
			_gesture_option.select(i)

func _on_library_changed() -> void:
	_preset_option.clear()
	_preset_option.add_item(NEW_ENTRY)
	for n in engine.library_order:
		_preset_option.add_item(n)
	if not _pending_select.is_empty() and engine.library.has(_pending_select):
		var target := _pending_select
		_pending_select = ""
		load_preset(target)
	elif not loaded_name.is_empty() and not engine.library.has(loaded_name):
		var gone := loaded_name
		loaded_name = ""
		_select_option("")
		_set_status("'%s' was removed (on another device?). The sliders stay as they are." % gone)
	else:
		_select_option(loaded_name)
	_refresh_buttons()

func _play_gesture() -> void:
	if _gesture_option.selected > 0:
		engine.gestures.play(_gesture_option.get_item_text(_gesture_option.selected))

# --- saving -------------------------------------------------------------------------------------------------------------

## the preset as the sliders and fields describe it
func collect(preset_name: String) -> Dictionary:
	var tags: Array = []
	for t in _tags_edit.text.split(","):
		var tag := t.strip_edges()
		if not tag.is_empty():
			tags.append(tag)
	var source := _loaded_source
	if source == "llm" and dirty:
		source = "llm_edited"   # an expression made by the LLM and changed by hand
	if loaded_name.is_empty():
		source = ("llm_edited" if dirty else "llm") if not _gen.is_empty() else "manual"
	var gesture := ""
	if _gesture_option.selected > 0:
		gesture = _gesture_option.get_item_text(_gesture_option.selected)
	return {"name": preset_name, "description": _description_edit.text.strip_edges(), "weights": _weights.duplicate(),
			"bones": _bones.duplicate(), "gesture": gesture, "speaking": _speaking_check.button_pressed,
			"tags": tags, "source": source}

func _valid_name(text: String) -> bool:
	return _name_regex.search(text) != null

func _save_new() -> void:
	var n := _name_edit.text.strip_edges()
	if not _valid_name(n):
		_set_status("Name: 1-40 letters, digits, - or _ (no spaces).", true)
		return
	if engine.library.has(n):
		_set_status("'%s' exists already: load it and use 'Overwrite', or choose another name." % n, true)
		return
	_pending_select = n
	_feedback_after_save = not _gen.is_empty()
	_disarm_delete()
	api.create(collect(n))

func _overwrite() -> void:
	if loaded_name.is_empty():
		_set_status("Load a preset first, or use 'Save as new'.", true)
		return
	_pending_select = loaded_name
	_disarm_delete()
	api.update(loaded_name, collect(loaded_name))

func _rename() -> void:
	var n := _name_edit.text.strip_edges()
	if loaded_name.is_empty():
		_set_status("Load a preset first.", true)
	elif not _valid_name(n):
		_set_status("Name: 1-40 letters, digits, - or _ (no spaces).", true)
	elif n == loaded_name:
		_set_status("Enter the new name in the name field.", true)
	else:
		_pending_select = n
		_disarm_delete()
		api.update(loaded_name, collect(n))

## two presses: the first arms the button for 3 seconds
func _delete() -> void:
	if loaded_name.is_empty():
		_set_status("Load a preset first.", true)
		return
	if not _delete_armed:
		_delete_armed = true
		_delete_button.text = "Really delete?"
		_delete_timer.start()
		return
	_disarm_delete()
	_pending_select = ""
	api.delete(loaded_name)

func _disarm_delete() -> void:
	_delete_armed = false
	_delete_timer.stop()
	if _delete_button != null:
		_delete_button.text = "Delete"

func _on_operation_done(kind: String, ok: bool, message: String, data: Dictionary) -> void:
	_set_status(message, not ok)
	_token_row.visible = api.token_required
	if not ok:
		_pending_select = ""
		return
	if kind == "delete":
		loaded_name = ""
	else:
		dirty = false
		loaded_name = str((data.get("preset", {}) as Dictionary).get("name", loaded_name))
		if kind == "create" and _feedback_after_save and not _gen.is_empty():
			# an expression of the language model was saved: kept as it was, or edited by hand first
			var saved: Dictionary = data.get("preset", {})
			api.send_feedback(str(_gen["id"]), "edit" if saved.get("source", "") == "llm_edited" else "keep", saved)
			_dismiss_generated()
		_feedback_after_save = false
	api.refresh()   # the answer replaces the library and selects _pending_select

# --- state of the buttons and messages ----------------------------------------------------------------------------------

func _on_availability() -> void:
	_token_row.visible = api.available and api.token_required
	if not api.available:
		_set_status("Offline: the presets that came with the character are used. Saving needs the server.", true)
	elif loaded_name.is_empty():
		_set_status("Connected to the server. Presets are shared with all devices.")
	_refresh_buttons()

func _refresh_buttons() -> void:
	if _save_new_button == null:
		return
	var online := api.available
	var typed := _name_edit.text.strip_edges()
	_save_new_button.disabled = not online or not _valid_name(typed)
	_overwrite_button.disabled = not online or loaded_name.is_empty()
	_rename_button.disabled = not online or loaded_name.is_empty() or not _valid_name(typed) or typed == loaded_name
	_delete_button.disabled = not online or loaded_name.is_empty()
	_token_row.visible = online and api.token_required
	_generate_button.disabled = not online or _gen_busy or _describe_edit.text.strip_edges().is_empty()

func _set_status(text: String, is_error := false) -> void:
	_status.text = text
	_status.add_theme_color_override("font_color", Color(1.0, 0.55, 0.5) if is_error else Color(0.7, 0.9, 0.7))

# --- expressions from a description (LLM) ------------------------------------------------------------------------------

## asks for an expression; meanwhile the closest preset is shown (the model may need seconds)
func _generate() -> void:
	var description := _describe_edit.text.strip_edges()
	if description.is_empty() or _gen_busy or not api.available:
		return
	_dismiss_generated()
	_gen_busy = true
	_before_gen = engine.current_name
	_generate_button.text = "..."
	_refresh_buttons()
	_set_status("Asking the language model ... the closest preset is shown meanwhile.")
	api.match_description(description)
	api.generate(description)

func _on_matched(data: Dictionary) -> void:
	var preset_name := str(data.get("name", ""))
	if _gen_busy and _gen.is_empty() and engine.library.has(preset_name):
		engine.play(preset_name)

func _on_generated(ok: bool, data: Dictionary, message: String) -> void:
	_gen_busy = false
	_generate_button.text = "Generate"
	if not ok:
		if engine.library.has(_before_gen):
			engine.play(_before_gen)
		_set_status(message, true)
		_refresh_buttons()
		return
	_gen = {"id": str(data.get("id", "")), "preset": data["preset"]}
	_load_generated(data["preset"])
	_result_row.visible = true
	var text := "Made by the language model in %.1f s: keep it, edit it or reject it." % float(data.get("seconds", 0.0))
	var corrections: Array = data.get("corrections", [])
	if not corrections.is_empty():
		text += " (Corrected: " + "; ".join(PackedStringArray(corrections)) + ")"
	_set_status(text)
	_refresh_buttons()

## puts the generated expression into the sliders as a new, unsaved preset and shows it
func _load_generated(p: Dictionary) -> void:
	_weights = (p.get("weights", {}) as Dictionary).duplicate()
	_bones = (p.get("bones", {}) as Dictionary).duplicate()
	_sync_sliders()
	var gesture_index := 0
	for i in _gesture_option.item_count:
		if _gesture_option.get_item_text(i) == str(p.get("gesture", "")):
			gesture_index = i
	_gesture_option.select(gesture_index)
	_speaking_check.set_pressed_no_signal(false)
	_name_edit.text = str(p.get("name", ""))
	_description_edit.text = str(p.get("description", ""))
	_tags_edit.text = ", ".join(PackedStringArray(p.get("tags", [])))
	loaded_name = ""
	_loaded_source = "llm"
	dirty = false
	_select_option("")
	engine.apply_preset(preview_preset(), 0.4, false)

## saves it as it is (source llm); "Save as new" after changing sliders saves it as llm_edited
func _keep() -> void:
	if _gen.is_empty():
		return
	_save_new()

func _edit_generated() -> void:
	if _gen.is_empty():
		return
	_set_status("Change the sliders, then press 'Save as new': it is saved as an edited expression and the model learns from it.")

func _reject_generated() -> void:
	if _gen.is_empty():
		return
	api.send_feedback(str(_gen["id"]), "reject")
	_dismiss_generated()
	if engine.library.has(_before_gen):
		engine.play(_before_gen)
	_set_status("Rejected (the model will avoid it next time).")

## the generated expression is no longer the one being worked on (another preset was loaded, saved, rejected)
func _dismiss_generated() -> void:
	_gen = {}
	_feedback_after_save = false
	if _result_row != null:
		_result_row.visible = false
