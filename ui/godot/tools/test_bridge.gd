extends SceneTree
# Checks the messages MIA's page sends to the character (host_bridge.gd).
# Run: godot --headless --path ui/godot --script res://tools/test_bridge.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

func _init() -> void:
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	for i in 5:
		await process_frame
	var bridge: HostBridge = main.bridge
	var eng: ExpressionEngine = main.engine

	check(bridge.handle_json('{"type": "expression", "name": "surprised"}'), "expression message is accepted")
	check(eng.current_name == "surprised", "the character shows 'surprised' (got '%s')" % eng.current_name)
	check(eng.gestures.current == "hands_up", "its gesture starts")

	check(not bridge.handle_json('{"type": "expression", "name": "no_such_face"}'), "unknown expression is rejected")
	check(eng.current_name == "surprised", "the current expression stays after an unknown name")
	check(not bridge.handle_json("not json at all"), "garbage is rejected")
	check(not bridge.handle_json('{"type": "dance"}'), "unknown message type is rejected")
	check(bridge.handle_json('{"type": "ready"}'), "'ready' (own echo outside an iframe) is harmless")

	check(bridge.handle_json('{"type": "speaking", "value": true}') and eng.speaking, "speaking message turns the mouth on")
	bridge.handle_json('{"type": "expression", "name": "happy"}')
	check(eng.speaking, "a new expression does not end the speaking that comes from the voice")
	var face := main.find_child("Face", true, false) as MeshInstance3D
	var moved := 0.0
	for i in 90:
		await process_frame
		for v in ExpressionEngine.VOWELS:
			moved = maxf(moved, face.get_blend_shape_value(face.find_blend_shape_by_name(v)))
	check(moved > 0.1, "the mouth moves while the voice plays (max vowel weight %.2f)" % moved)
	bridge.handle_json('{"type": "speaking", "value": false}')
	check(not eng.speaking, "speaking message turns the mouth off again")

	check(bridge.handle_json('{"type": "gesture", "name": "wave"}') and eng.gestures.current == "wave", "gesture message plays a gesture")

	# --- viewport_inset: the character is centered in the free area -------------------------------------------
	var size := main.get_viewport().get_visible_rect().size
	var w := int(size.x)
	var h := int(size.y)
	main.show_view("body")
	main.set_camera(main.pivot, main.distance)
	var inset_msg := '{"type": "viewport_inset", "left": 0, "right": %d, "top": 0, "bottom": 0, "width": %d, "height": %d}' % [int(w * 0.3), w, h]
	check(bridge.handle_json(inset_msg), "viewport_inset (panel at the right) is accepted")
	for i in 150:
		await process_frame
	var at: Vector2 = main.camera.unproject_position(main.pivot)
	check(absf(at.x / size.x - 0.35) < 0.02, "panel 30%% wide: the character is centered in the free area (x %.3f, wanted 0.35)" % (at.x / size.x))
	check(absf(at.y / size.y - 0.5) < 0.02, "no vertical change for a side panel (y %.3f)" % (at.y / size.y))

	var sheet_msg := '{"type": "viewport_inset", "left": 0, "right": 0, "top": 0, "bottom": %d, "width": %d, "height": %d}' % [int(h * 0.5), w, h]
	bridge.handle_json(sheet_msg)
	for i in 150:
		await process_frame
	at = main.camera.unproject_position(main.pivot)
	check(absf(at.x / size.x - 0.5) < 0.02, "bottom sheet: horizontally centered again (x %.3f)" % (at.x / size.x))
	check(absf(at.y / size.y - 0.25) < 0.02, "bottom sheet 50%% high: centered in the upper half (y %.3f, wanted 0.25)" % (at.y / size.y))
	var head_top: Vector2 = main.camera.unproject_position(Vector3(0, main.head_height + 0.15, 0))
	check(head_top.y > 0.0, "the head stays inside the window above the sheet (y %.0f)" % head_top.y)

	bridge.handle_json('{"type": "viewport_inset", "left": 0, "right": 0, "top": 0, "bottom": 0, "width": %d, "height": %d}' % [w, h])
	for i in 150:
		await process_frame
	at = main.camera.unproject_position(main.pivot)
	check(absf(at.x / size.x - 0.5) < 0.02 and absf(at.y / size.y - 0.5) < 0.02, "no inset: back in the middle of the window")

	check(not bridge.handle_json('{"type": "viewport_inset", "left": 0, "right": 10, "top": 0, "bottom": 0}'), "viewport_inset without a window size is refused")
	check(not bridge.handle_json('{"type": "viewport_inset", "left": "a", "right": 10, "top": 0, "bottom": 0, "width": 100, "height": 100}'), "viewport_inset with text instead of numbers is refused")
	var got := []
	bridge.inset_changed.connect(func(l, r, t, b): got.append([l, r, t, b]))
	bridge.handle_json('{"type": "viewport_inset", "left": 0, "right": 5000, "top": -20, "bottom": 0, "width": 1000, "height": 500}')
	check(got.size() == 1 and absf(got[0][1] - 0.9) < 0.001 and got[0][2] == 0.0, "insets are clamped (0 .. 0.9 of the window)")

	# --- view ---------------------------------------------------------------------------------------------------
	check(bridge.handle_json('{"type": "view", "name": "face"}'), "view message is accepted")
	check(is_equal_approx(main._distance_goal, 0.8), "the camera goes to the face view")
	check(not bridge.handle_json('{"type": "view", "name": "moon"}'), "unknown view is refused")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
