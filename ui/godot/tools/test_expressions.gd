extends SceneTree
# Headless checks for the expression engine.
# Run: godot --headless --path ui/godot --script res://tools/test_expressions.gd

const REQUIRED := ["greet", "no", "annoyed", "talk", "yes", "idle",
		"neutral", "happy", "sad", "angry", "surprised", "embarrassed", "smug", "thinking"]
var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

func shape_value(mi: MeshInstance3D, key: String) -> float:
	return mi.get_blend_shape_value(mi.find_blend_shape_by_name(key))

func _init() -> void:
	var character: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(character)
	var skeleton: Skeleton3D = character.find_child("GeneralSkeleton", true, false)
	var face: MeshInstance3D = character.find_child("Face", true, false)
	var eng := ExpressionEngine.new()
	get_root().add_child(eng)
	eng.setup(character, skeleton)
	eng.blink_enabled = false

	var count := eng.load_library("res://presets/library.json")
	check(count == REQUIRED.size(), "library loads %d presets (got %d)" % [REQUIRED.size(), count])
	for n in REQUIRED:
		check(eng.library.has(n), "required preset '%s' present" % n)

	# validation: unknown key rejected, values clamped, bad bone param rejected
	var v := eng.validate({"name": "t", "weights": {"Fcl_MTH_Joy": 1.7, "Nope": 0.5, "Fcl_EYE_Joy": -2},
			"bones": {"head_yaw": 99, "tail": 1}})
	var p: Dictionary = v["preset"]
	check(not p["weights"].has("Nope"), "unknown shape key rejected")
	check(p["weights"]["Fcl_MTH_Joy"] == 1.0 and p["weights"]["Fcl_EYE_Joy"] == 0.0, "weights clamped to 0..1")
	check(p["bones"]["head_yaw"] == 45.0 and not p["bones"].has("tail"), "bones clamped / unknown rejected")
	check((v["corrections"] as Array).size() == 5, "5 corrections reported (got %d)" % (v["corrections"] as Array).size())
	check(eng.validate({"weights": {}})["preset"] == null, "preset without name rejected")
	check(not eng.play("does_not_exist"), "unknown preset name returns false")

	# blending: halfway is between, end is exact, keys not in the next preset go back to 0
	eng.idle_enabled = false
	eng.play("neutral", 0.0)
	eng.apply_preset({"name": "a", "weights": {"Fcl_MTH_Joy": 1.0, "Fcl_BRW_Joy": 0.5}}, 1.0)
	eng.advance(0.5)
	var mid := shape_value(face, "Fcl_MTH_Joy")
	check(absf(mid - 0.5) < 0.01, "smooth easing is 0.5 at halfway (got %.3f)" % mid)
	eng.advance(0.6)
	check(shape_value(face, "Fcl_MTH_Joy") == 1.0, "reaches target weight")
	eng.apply_preset({"name": "b", "weights": {"Fcl_EYE_Angry": 0.4}}, 0.2)
	eng.advance(0.1)
	check(shape_value(face, "Fcl_MTH_Joy") > 0.0 and shape_value(face, "Fcl_MTH_Joy") < 1.0, "interrupted blend continues from the current value")
	eng.advance(0.2)
	check(shape_value(face, "Fcl_MTH_Joy") == 0.0 and shape_value(face, "Fcl_BRW_Joy") == 0.0, "keys not in the preset blend back to 0")
	check(absf(shape_value(face, "Fcl_EYE_Angry") - 0.4) < 0.001, "new key reaches 0.4")

	# blinking: happens on top of an expression, never while the eyes are closed
	eng.blink_enabled = true
	eng.play("neutral", 0.0)
	var max_blink := 0.0
	for i in 600:  # 10 s at 60 fps
		eng.advance(1.0 / 60.0)
		max_blink = maxf(max_blink, shape_value(face, "Fcl_EYE_Close"))
	check(max_blink > 0.9, "blinks happen on a neutral face (max close %.2f)" % max_blink)
	eng.play("greet", 0.0)  # eyes partly closed by Joy, but not above the threshold
	eng.apply_preset({"name": "closed", "weights": {"Fcl_EYE_Close": 1.0}}, 0.0)
	var dipped := false
	for i in 600:
		eng.advance(1.0 / 60.0)
		if shape_value(face, "Fcl_EYE_Close") < 0.99:
			dipped = true
	check(not dipped, "no blink while the eyes are already closed")

	# idle motion moves the head, and presets leave bones neutral again afterwards
	eng.blink_enabled = false
	eng.idle_enabled = true
	eng.play("neutral", 0.0)
	var head := skeleton.find_bone("Head")
	var q0 := skeleton.get_bone_pose_rotation(head)
	for i in 120:
		eng.advance(1.0 / 60.0)
	check(skeleton.get_bone_pose_rotation(head).angle_to(q0) > 0.001, "idle motion moves the head")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
