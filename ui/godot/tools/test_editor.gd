extends SceneTree
# Drives the expression editor like a user would, against an in-memory stand-in of MIA's preset server.
# Run: godot --headless --path ui/godot --script res://tools/test_editor.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

## the server with the same rules as presets_api.py, answering at once
class FakeServer extends PresetApi:
	var presets := {}
	var protected := ["idle"]
	var needs_token := ""
	var online := true
	var counter := 1
	var calls: Array = []
	var feedback: Array = []
	var generate_error := ""
	var generated_preset := {"name": "llm-sly-grin", "description": "a sly grin", "weights": {"Fcl_MTH_Fun": 0.6, "Fcl_EYE_Joy": 0.4},
			"bones": {"head_roll": 4.0}, "gesture": "", "speaking": false, "tags": ["smug", "sly"], "source": "llm"}

	func _request(method: int, path: String, body, done: Callable) -> void:
		calls.append("%d %s" % [method, path])
		if not online:
			done.call(0, null)
			return
		var write := method != HTTPClient.METHOD_GET
		if write and not needs_token.is_empty() and token != needs_token:
			done.call(401, {"error": "a valid token is needed to change presets"})
			return
		if path == "/api/expression/match":
			done.call(200, {"name": "smug", "score": 3, "preset": presets.get("smug")})
			return
		if path == "/api/expression/generate":
			if generate_error.is_empty():
				done.call(200, {"id": "r1", "preset": generated_preset.duplicate(true), "corrections": [], "closest": "smug", "seconds": 1.5, "model": "fake"})
			else:
				done.call(503, {"error": generate_error})
			return
		if path == "/api/expression/feedback":
			feedback.append(body)
			done.call(200, {"logged": body["decision"]})
			return
		var name_in_path := path.trim_prefix("/api/presets/").get_slice("?", 0)
		if method == HTTPClient.METHOD_GET and path == "/api/presets":
			done.call(200, {"presets": presets.values(), "version": str(counter), "token_required": not needs_token.is_empty(), "protected": protected})
		elif method == HTTPClient.METHOD_GET and path == "/api/presets/version":
			done.call(200, {"version": str(counter)})
		elif method == HTTPClient.METHOD_POST:
			if presets.has(body["name"]):
				done.call(409, {"error": "preset '%s' exists already, change it instead" % body["name"]})
			else:
				presets[body["name"]] = body
				counter += 1
				done.call(201, {"preset": body, "corrections": [], "version": str(counter)})
		elif method == HTTPClient.METHOD_PUT:
			if not presets.has(name_in_path):
				done.call(404, {"error": "no preset '%s'" % name_in_path})
			elif body["name"] != name_in_path and (name_in_path in protected):
				done.call(409, {"error": "'%s' is used by MIA's emotions and cannot be renamed" % name_in_path})
			elif body["name"] != name_in_path and presets.has(body["name"]):
				done.call(409, {"error": "preset '%s' exists already" % body["name"]})
			else:
				presets.erase(name_in_path)
				presets[body["name"]] = body
				counter += 1
				done.call(200, {"preset": body, "corrections": [], "version": str(counter)})
		elif method == HTTPClient.METHOD_DELETE:
			if name_in_path in protected and not path.ends_with("force=1"):
				done.call(409, {"error": "'%s' is used by MIA's emotions and cannot be deleted" % name_in_path})
			elif presets.has(name_in_path):
				presets.erase(name_in_path)
				counter += 1
				done.call(200, {"deleted": name_in_path})
			else:
				done.call(404, {"error": "no preset"})

func frames(n: int) -> void:
	for i in n:
		await process_frame

func _init() -> void:
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	await frames(4)
	var eng: ExpressionEngine = main.engine
	eng.blink_enabled = false
	eng.idle_enabled = false
	if main.editor != null:
		main.editor.close()
	var face := main.find_child("Face", true, false) as MeshInstance3D

	# the server with a copy of the bundled presets
	var server := FakeServer.new()
	main.add_child(server)
	server.setup("fake://server")
	for n in eng.library_order:
		var copy: Dictionary = (eng.library[n] as Dictionary).duplicate(true)
		server.presets[n] = copy
	server.library_received.connect(func(presets: Array, _info): main._on_server_presets(presets))
	server.refresh()
	check(server.available and eng.library.size() == 14, "the library comes from the server (14 presets)")

	var layer := CanvasLayer.new()
	main.add_child(layer)
	var ed := ExpressionEditor.new()
	layer.add_child(ed)
	ed.setup(eng, server)
	ed.open()
	await frames(2)

	# --- the sliders -------------------------------------------------------------------------------
	check(ed._rows.size() == 57, "57 shape key sliders (got %d)" % ed._rows.size())
	var counts := {}
	for k in ed._rows:
		counts[ed._rows[k]["category"]] = counts.get(ed._rows[k]["category"], 0) + 1
	check(counts == {"eyes": 14, "brows": 5, "mouth": 19, "other": 19}, "grouped into eyes/brows/mouth/other (%s)" % [counts])
	check(ed._bone_rows.size() == 5, "5 sliders for head and eyes")
	var slider := ed._rows["Fcl_MTH_Joy"]["slider"] as HSlider
	check(slider.custom_minimum_size.y >= 36 and slider.has_theme_icon_override("grabber"), "sliders are touch friendly (tall, big handle)")
	slider.value = 0.7
	eng.advance(0.3)
	var joy := face.get_blend_shape_value(face.find_blend_shape_by_name("Fcl_MTH_Joy"))
	check(absf(joy - 0.7) < 0.02, "moving a slider changes the face live (Joy %.2f)" % joy)
	var yaw := ed._bone_rows["head_yaw"]["slider"] as HSlider
	yaw.value = 20.0
	check(absf(ed._bones["head_yaw"] - 20.0) < 0.01, "a bone slider sets the head yaw")
	check(ed.dirty, "changes are marked as unsaved")

	# --- filter ----------------------------------------------------------------------------------------------
	ed._filter.text = "joy"
	ed._filter.text_changed.emit("joy")
	var shown := 0
	for k in ed._rows:
		if (ed._rows[k]["row"] as Control).visible:
			shown += 1
			if not (k as String).to_lower().contains("joy") and not str(ed._meta[k]["description"]).to_lower().contains("joy"):
				shown += 1000
	check(shown > 0 and shown < 57, "the filter shows only matching sliders (%d)" % shown)
	check(not (ed._sections["brows"]["header"] as Control).visible or (ed._rows["Fcl_BRW_Joy"]["row"] as Control).visible, "groups without a match are hidden")
	ed._filter.text = ""
	ed._filter.text_changed.emit("")
	var all_shown := true
	for k in ed._rows:
		all_shown = all_shown and (ed._rows[k]["row"] as Control).visible
	check(all_shown, "clearing the filter shows everything again")

	# --- loading and resetting ---------------------------------------------------------------------------
	check(ed.load_preset("smug"), "load preset 'smug'")
	check(absf((ed._rows["Fcl_MTH_Fun"]["slider"] as HSlider).value - 0.6) < 0.001 and (ed._rows["Fcl_MTH_Joy"]["slider"] as HSlider).value == 0.0,
			"the sliders show the preset (others at 0)")
	check(ed._name_edit.text == "smug" and ed._gesture_option.get_item_text(ed._gesture_option.selected) == "hand_on_hip", "name and gesture are filled in")
	check(not ed.dirty and ed.loaded_name == "smug", "freshly loaded: nothing unsaved")
	ed.reset_to_neutral()
	var any_set := false
	for k in ed._rows:
		any_set = any_set or (ed._rows[k]["slider"] as HSlider).value != 0.0
	eng.advance(0.5)
	check(not any_set and face.get_blend_shape_value(face.find_blend_shape_by_name("Fcl_MTH_Fun")) < 0.01, "'Neutral' puts all sliders and the face to neutral")

	# --- save as new ------------------------------------------------------------------------------------------------
	ed.start_new()
	check(ed.loaded_name == "" and ed._save_new_button.disabled and ed._overwrite_button.disabled, "new preset: only 'Save as new' can become available")
	(ed._rows["Fcl_EYE_Surprised"]["slider"] as HSlider).value = 0.9
	(ed._rows["Fcl_MTH_Surprised"]["slider"] as HSlider).value = 0.4
	ed._name_edit.text = "bad name"
	ed._name_edit.text_changed.emit("bad name")
	check(ed._save_new_button.disabled, "an invalid name cannot be saved")
	ed._save_new()
	check(not server.presets.has("bad name") and ed._status.text.contains("letters"), "no request for an invalid name, with a hint")
	ed._name_edit.text = "shocked"
	ed._name_edit.text_changed.emit("shocked")
	ed._description_edit.text = "very surprised"
	ed._tags_edit.text = "surprised, test ,"
	ed._save_new()
	check(server.presets.has("shocked"), "'Save as new' stores the preset on the server")
	var saved: Dictionary = server.presets["shocked"]
	check(absf(saved["weights"]["Fcl_EYE_Surprised"] - 0.9) < 0.001 and saved["description"] == "very surprised" and saved["tags"] == ["surprised", "test"] and saved["source"] == "manual",
			"with weights, description, tags and source")
	check(eng.library.has("shocked") and ed.loaded_name == "shocked" and not ed.dirty, "it is in the library and selected after saving")
	check(ed._preset_option.get_item_text(ed._preset_option.selected) == "shocked", "the list shows it")
	ed.start_new()
	ed._name_edit.text = "shocked"
	ed._name_edit.text_changed.emit("shocked")
	ed._save_new()
	check(ed._status.text.contains("exists"), "an existing name is refused with a hint")

	# --- overwrite, rename, delete --------------------------------------------------------------------------------------
	ed.load_preset("shocked")
	(ed._rows["Fcl_MTH_Surprised"]["slider"] as HSlider).value = 0.1
	ed._overwrite()
	check(absf(server.presets["shocked"]["weights"]["Fcl_MTH_Surprised"] - 0.1) < 0.001 and not ed.dirty, "'Overwrite' saves the changed sliders")
	ed._name_edit.text = "astonished"
	ed._name_edit.text_changed.emit("astonished")
	check(not ed._rename_button.disabled, "'Rename' is available with a new name")
	ed._rename()
	check(server.presets.has("astonished") and not server.presets.has("shocked") and ed.loaded_name == "astonished", "'Rename' moves the preset")
	ed.load_preset("idle")
	ed._name_edit.text = "calm_idle"
	ed._rename()
	check(server.presets.has("idle") and ed._status.text.contains("MIA"), "a preset MIA uses cannot be renamed (the reason is shown)")
	ed.load_preset("astonished")
	ed._delete()
	check(server.presets.has("astonished") and ed._delete_button.text == "Really delete?", "'Delete' needs a second press")
	ed._delete()
	check(not server.presets.has("astonished") and not eng.library.has("astonished"), "the second press deletes it")
	check(ed.loaded_name == "", "nothing stays selected after a delete")
	ed.load_preset("idle")
	ed._delete()
	ed._delete()
	check(server.presets.has("idle") and ed._status.text.contains("cannot be deleted"), "a preset MIA uses cannot be deleted")

	# --- source of expressions made by the LLM ---------------------------------------------------------------------
	server.presets["llm_made"] = {"name": "llm_made", "description": "", "weights": {"Fcl_MTH_Joy": 0.5}, "bones": {}, "gesture": "", "speaking": false, "tags": [], "source": "llm"}
	server.refresh()
	ed.load_preset("llm_made")
	check(ed.collect("llm_made")["source"] == "llm", "unchanged LLM presets stay 'llm'")
	(ed._rows["Fcl_MTH_Joy"]["slider"] as HSlider).value = 0.8
	check(ed.collect("llm_made")["source"] == "llm_edited", "an LLM preset changed by hand becomes 'llm_edited'")

	# --- another device ---------------------------------------------------------------------------------------------------
	var before := eng.library.size()
	server.presets["from_phone"] = {"name": "from_phone", "description": "", "weights": {"Fcl_EYE_Joy": 1.0}, "bones": {}, "gesture": "", "speaking": false, "tags": [], "source": "manual"}
	server.counter += 1
	server.check_version()   # the poll finds the changed version
	check(eng.library.size() == before + 1 and eng.library.has("from_phone"), "a preset saved on another device shows up after the poll")
	check(main._buttons.has("expression:from_phone"), "and gets a button in the menu")

	# --- offline and token -------------------------------------------------------------------------------------------------------
	server.online = false
	server.check_version()
	check(not server.available and ed._save_new_button.disabled and ed._status.text.contains("Offline"), "offline: saving is disabled and says why")
	check(eng.library.size() > 0, "offline: the presets that are loaded keep working")
	server.online = true
	server.needs_token = "s3cret"
	server.refresh()
	check(server.available and server.token_required and ed._token_row.visible, "a server with a token shows the token field")
	ed.start_new()
	ed._name_edit.text = "needs_token"
	ed._name_edit.text_changed.emit("needs_token")
	ed._save_new()
	check(not server.presets.has("needs_token") and ed._status.text.contains("token"), "without the token nothing is saved")
	ed._token_edit.text = "s3cret"
	ed._token_edit.text_changed.emit("s3cret")
	ed._save_new()
	check(server.presets.has("needs_token"), "with the token it works")

	# --- layout ---------------------------------------------------------------------------------------------------------------------
	get_root().size = Vector2i(1280, 720)
	ed._update_layout()
	check(ed.anchor_left > 0.5 and ed.anchor_right == 1.0 and ed.anchor_top == 0.0 and ed.anchor_bottom == 1.0, "wide screen: panel on the right")
	get_root().size = Vector2i(400, 800)
	ed._update_layout()
	check(ed.anchor_left == 0.0 and ed.anchor_right == 1.0 and ed.anchor_top == 1.0, "phone: bottom sheet")
	ed.close()
	check(not ed.visible, "the panel can be closed")

	# --- expressions from a description -------------------------------------------------------------------------------
	ed.load_preset("happy")
	check(ed._generate_button.disabled, "Generate is disabled while the description is empty")
	ed._describe_edit.text = "sly grin"
	ed._describe_edit.text_changed.emit("sly grin")
	check(not ed._generate_button.disabled, "Generate is enabled with a description")
	server.calls.clear()
	ed._generate()
	await frames(3)
	check("2 /api/expression/match" in server.calls and "2 /api/expression/generate" in server.calls, "the description goes to match (instant) and generate")
	check(not ed._gen.is_empty() and ed._result_row.visible, "the result is shown with keep / edit / reject")
	check(ed._name_edit.text == "llm-sly-grin" and ed._description_edit.text == "a sly grin", "name and description of the result are filled in")
	check(absf((ed._rows["Fcl_MTH_Fun"]["slider"] as HSlider).value - 0.6) < 0.001, "the sliders show the generated weights")
	eng.advance(0.8)
	var fun := face.get_blend_shape_value(face.find_blend_shape_by_name("Fcl_MTH_Fun"))
	check(absf(fun - 0.6) < 0.05, "the character shows it (Fun %.2f)" % fun)
	check(ed.loaded_name == "" and ed.collect("llm-sly-grin")["source"] == "llm", "it is an unsaved new preset with source llm")

	# keep: saved as it is, the server learns "keep"
	server.feedback.clear()
	ed._keep()
	await frames(4)
	check(server.presets.has("llm-sly-grin") and server.presets["llm-sly-grin"]["source"] == "llm", "Keep saves the preset with source llm")
	check(server.feedback.size() == 1 and server.feedback[0]["decision"] == "keep" and server.feedback[0]["id"] == "r1", "the server is told 'keep'")
	check(not ed._result_row.visible and ed._gen.is_empty(), "the keep / edit / reject row is gone afterwards")

	# edit: change a slider, save under another name -> llm_edited and "edit" with the saved preset
	ed._describe_edit.text = "sly grin again"
	ed._generate()
	await frames(3)
	(ed._rows["Fcl_MTH_Fun"]["slider"] as HSlider).value = 0.9
	ed._name_edit.text = "my-sly-grin"
	server.feedback.clear()
	ed._save_new()
	await frames(4)
	check(server.presets.has("my-sly-grin") and server.presets["my-sly-grin"]["source"] == "llm_edited", "a changed result is saved as llm_edited")
	check(server.feedback.size() == 1 and server.feedback[0]["decision"] == "edit" and server.feedback[0]["preset"]["weights"]["Fcl_MTH_Fun"] == 0.9,
			"the server is told 'edit' with the saved preset")

	# reject: back to the expression before, "reject" is logged, nothing saved
	ed.load_preset("sad")
	eng.play("sad", 0.0)
	var count_before := server.presets.size()
	ed._describe_edit.text = "a different look"
	ed._generate()
	await frames(3)
	server.feedback.clear()
	ed._reject_generated()
	await frames(2)
	check(server.feedback.size() == 1 and server.feedback[0]["decision"] == "reject", "Reject is logged")
	check(server.presets.size() == count_before and not ed._result_row.visible, "nothing was saved and the row is gone")
	check(eng.current_name == "sad", "the expression from before comes back (got '%s')" % eng.current_name)

	# a failing model: clear message, the expression from before stays
	server.generate_error = "the language model could not be reached: down"
	ed._describe_edit.text = "anything"
	ed._generate()
	await frames(3)
	check(ed._gen.is_empty() and not ed._result_row.visible and not ed._generate_button.disabled and ed._generate_button.text == "Generate", "after an error the button is usable again")
	check(ed._status.text.contains("could not be reached"), "the error is shown: %s" % ed._status.text)
	check(eng.current_name == "sad", "the expression from before stays after an error")
	server.generate_error = ""

	# offline: generate is not possible
	server.online = false
	server.refresh()
	await frames(2)
	ed._refresh_buttons()
	check(ed._generate_button.disabled, "Generate is disabled offline")
	server.online = true
	server.refresh()
	await frames(2)

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
