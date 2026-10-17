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

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
