extends SceneTree
# Drives the gesture editor like a user would, against an in-memory stand-in of MIA's gesture API.
# Run: godot --headless --path ui/godot --script res://tools/test_gesture_editor.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

class FakeServer extends PresetApi:
	var docs := {}
	var needs_token := ""
	var online := true
	var bodies: Array = []

	func _request(method: int, path: String, body, done: Callable) -> void:
		if not online:
			done.call(0, null)
			return
		if method != HTTPClient.METHOD_GET and not needs_token.is_empty() and token != needs_token:
			done.call(401, {"error": "a valid token is needed"})
			return
		var gesture_name := path.trim_prefix("/api/gestures/").get_slice("?", 0)
		if path == "/api/presets":
			done.call(200, {"presets": [], "version": "1", "token_required": not needs_token.is_empty(), "protected": []})
		elif path == "/api/presets/version":
			done.call(200, {"version": "1"})
		elif path == "/api/gestures" and method == HTTPClient.METHOD_GET:
			done.call(200, {"gestures": [], "pose_gestures": docs.values(), "version": "1", "token_required": false})
		elif method == HTTPClient.METHOD_POST:
			bodies.append(body)
			docs[body["name"]] = body
			done.call(201, {"gesture": body, "corrections": [], "version": "2"})
		elif method == HTTPClient.METHOD_PUT:
			bodies.append(body)
			docs.erase(gesture_name)
			docs[body["name"]] = body
			done.call(200, {"gesture": body, "corrections": [], "version": "2"})
		elif method == HTTPClient.METHOD_DELETE:
			docs.erase(gesture_name)
			done.call(200, {"deleted": gesture_name})
		else:
			done.call(404, {"error": "?"})

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
	main.editor.close()

	check(main.gesture_editor != null, "the page has a gesture editor")
	var server := FakeServer.new()
	main.add_child(server)
	server.setup("fake://server")
	server.gestures_received.connect(func(d: Array): eng.gestures.set_pose_gestures(d))
	server.refresh()
	await frames(2)

	var layer := CanvasLayer.new()
	main.add_child(layer)
	var ed := GestureEditor.new()
	layer.add_child(ed)
	ed.setup(eng, server)
	ed.open()
	await frames(2)

	# --- sliders and the sparse pose ---------------------------------------------------------------
	check(ed._rows.size() == 9, "9 angle sliders (got %d)" % ed._rows.size())
	check(ed.pose.is_empty() and ed._play_button.disabled, "nothing set: empty pose, Play disabled")
	check(ed.mirror and ed._mirror_check.button_pressed, "Mirror starts on")
	(ed._rows["upper_raise"]["slider"] as HSlider).value = 90.0
	check(ed.pose.get("R", {}).get("upper_raise") == 90.0 and ed.pose.get("L", {}).get("upper_raise") == 90.0, "with Mirror both arms get the angle")
	check(ed.dirty and not ed._play_button.disabled, "marked as changed, Play enabled")
	(ed._rows["upper_raise"]["slider"] as HSlider).value = 22.0
	check(ed.pose.is_empty(), "a value back at neutral is not stored")
	(ed._rows["torso_lean"]["slider"] as HSlider).value = 10.0
	check(ed.pose == {"torso": {"torso_lean": 10.0}}, "torso angles are shared, not per arm")
	(ed._rows["torso_lean"]["slider"] as HSlider).value = 0.0

	# --- mirror off, other side ------------------------------------------------------------------------
	ed._mirror_check.button_pressed = false
	(ed._rows["elbow_bend"]["slider"] as HSlider).value = 100.0
	check(ed.pose.has("R") and not ed.pose.has("L"), "without Mirror only the shown arm changes")
	ed._side_option.select(1)
	ed._side_option.item_selected.emit(1)
	check(ed.side == "L" and (ed._rows["elbow_bend"]["slider"] as HSlider).value == 9.0, "switching the side shows the other arm's angles (neutral)")
	(ed._rows["upper_raise"]["slider"] as HSlider).value = 120.0
	check(ed.pose["L"] == {"upper_raise": 120.0} and ed.pose["R"] == {"elbow_bend": 100.0}, "the two arms hold their own angles")
	ed._mirror_check.button_pressed = true
	check(ed.pose["R"] == ed.pose["L"] and ed.pose["R"].get("upper_raise") == 120.0, "turning Mirror on copies the shown arm to the other")

	# --- fingers ---------------------------------------------------------------------------------------
	ed._finger_option.select(2)   # fist
	ed._finger_option.item_selected.emit(2)
	check(ed.pose["R"]["fingers"] == "fist" and ed.pose["L"]["fingers"] == "fist", "named finger pose is stored for both arms")
	ed._finger_option.select(4)   # custom
	ed._finger_option.item_selected.emit(4)
	check(ed._finger_box.visible and typeof(ed.pose["R"]["fingers"]) == TYPE_DICTIONARY and ed.pose["R"]["fingers"]["index"] == 100, "custom starts from the fist")
	(ed._finger_rows["index"]["slider"] as HSlider).value = 0.0
	check(ed.pose["L"]["fingers"]["index"] == 0.0 and ed.pose["L"]["fingers"]["thumb"] == 100, "one finger slider changes one finger")
	ed._finger_option.select(0)
	ed._finger_option.item_selected.emit(0)
	check(not ed.pose["R"].has("fingers"), "relaxed fingers are not stored")

	# --- preview and play ------------------------------------------------------------------------------------
	eng.gestures.stop()
	ed._preview()
	check(eng.gestures.current == GestureEngine.PREVIEW, "a slider move previews the final pose")
	ed.play()
	check(eng.gestures.current == GestureEngine.TRY, "Play runs the gesture from neutral")
	eng.gestures.stop()
	ed.close()
	check(eng.gestures.current != GestureEngine.PREVIEW, "closing the editor ends the preview")
	ed.open()

	# --- saving ----------------------------------------------------------------------------------------------
	ed._name_edit.text = "shrug test"
	ed._refresh_buttons()
	check(ed._save_new_button.disabled, "a name with a space is refused")
	ed._name_edit.text = "high_arms"
	ed._description_edit.text = "both arms up"
	ed._refresh_buttons()
	check(not ed._save_new_button.disabled and ed._overwrite_button.disabled, "valid name: Save as new on, Overwrite off")
	ed._save_new()
	await frames(3)
	check(server.docs.has("high_arms") and server.docs["high_arms"]["source"] == "manual", "Save as new posts the document")
	check(server.docs["high_arms"]["pose"]["R"]["upper_raise"] == 120.0 and server.docs["high_arms"]["description"] == "both arms up", "the document has the angles")
	check(ed.loaded_name == "high_arms" and not ed.dirty, "the saved gesture is loaded")
	check(eng.gestures.library.has("high_arms"), "the character can play it afterwards")

	(ed._rows["wrist"]["slider"] as HSlider).value = 30.0
	ed._overwrite()
	await frames(3)
	check(server.docs["high_arms"]["pose"]["R"]["wrist"] == 30.0, "Overwrite saves the change")

	ed._name_edit.text = "high_arms2"
	ed._refresh_buttons()
	ed._rename()
	await frames(3)
	check(server.docs.has("high_arms2") and not server.docs.has("high_arms") and ed.loaded_name == "high_arms2", "Rename moves the gesture")

	# --- loading --------------------------------------------------------------------------------------------
	ed.new_gesture()
	check(ed.pose.is_empty() and ed.loaded_name.is_empty(), "New gesture clears the sliders")
	ed._picker.select(1)
	ed._picker.item_selected.emit(1)
	check(ed.loaded_name == "high_arms2" and ed.mirror and (ed._rows["upper_raise"]["slider"] as HSlider).value == 120.0, "the picker loads a gesture into the sliders (mirror on: equal arms)")

	# --- delete (two presses) --------------------------------------------------------------------------------------
	ed._delete()
	check(server.docs.has("high_arms2") and ed._delete_button.text == "Really delete?", "the first press only arms the button")
	ed._delete()
	await frames(3)
	check(not server.docs.has("high_arms2") and ed.loaded_name.is_empty(), "the second press deletes")

	# --- token and offline ------------------------------------------------------------------------------------
	server.needs_token = "secret"
	ed.new_gesture()
	(ed._rows["upper_raise"]["slider"] as HSlider).value = 100.0
	ed._name_edit.text = "needs_token"
	ed._refresh_buttons()
	ed._save_new()
	await frames(3)
	check(not server.docs.has("needs_token") and ed._status.text.to_lower().contains("token"), "a missing token is explained")
	server.needs_token = ""
	server.online = false
	server.refresh()
	await frames(2)
	ed._refresh_buttons()
	check(ed._save_new_button.disabled and not ed._play_button.disabled, "offline: saving is off, Play still works")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
