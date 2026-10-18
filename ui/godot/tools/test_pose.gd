extends SceneTree
# Checks the angles of the gesture editor: the conversion into arm directions (pose_model.gd) and the gesture engine with gestures made of
# angles: playing, torso, fingers, arms following the torso, gestures coming and going.
# Run: godot --headless --path ui/godot --script res://tools/test_pose.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

func near(a: Vector3, b: Vector3, tolerance := 0.02) -> bool:
	return a.distance_to(b) < tolerance

func angle_between(a: Array, b: Array) -> float:
	return rad_to_deg(Vector3(a[0], a[1], a[2]).normalized().angle_to(Vector3(b[0], b[1], b[2]).normalized()))

func _init() -> void:
	# --- the upper arm: [forward, up, outward] -----------------------------------------------------------------------
	check(near(PoseModel.upper_direction(0, 0), Vector3(0, -1, 0)), "raise 0: the arm hangs down")
	check(near(PoseModel.upper_direction(90, 0), Vector3(0, 0, 1)), "raise 90, direction 0: sideways (outward)")
	check(near(PoseModel.upper_direction(90, 90), Vector3(1, 0, 0)), "raise 90, direction 90: forward")
	check(near(PoseModel.upper_direction(90, -90), Vector3(-1, 0, 0)), "raise 90, direction -90: backward")
	check(near(PoseModel.upper_direction(90, 180), Vector3(0, 0, -1)), "raise 90, direction 180: across the body")
	check(near(PoseModel.upper_direction(180, 33), Vector3(0, 1, 0)), "raise 180: straight up whatever the direction")

	# --- the forearm ---------------------------------------------------------------------------------------------------
	var hanging := Vector3(0, -1, 0)
	check(near(PoseModel.forearm_direction(hanging, 0, 0), hanging), "no bend: the forearm continues the upper arm")
	check(near(PoseModel.forearm_direction(hanging, 90, 0), Vector3(1, 0, 0)), "hanging arm, bend 90, turn 0: the forearm swings forward")
	check(near(PoseModel.forearm_direction(hanging, 90, 90), Vector3(0, 0, -1)), "turn 90: inward (across the body)")
	check(near(PoseModel.forearm_direction(hanging, 90, -90), Vector3(0, 0, 1)), "turn -90: outward")
	check(near(PoseModel.forearm_direction(hanging, 90, 180), Vector3(-1, 0, 0)), "turn 180: backward")
	check(near(PoseModel.forearm_direction(Vector3(0, 0, 1), 90, 0), Vector3(1, 0, 0)), "arm out to the side, bend 90: the forearm swings forward")
	check(near(PoseModel.forearm_direction(Vector3(1, 0, 0), 90, 0), Vector3(0, 1, 0)), "arm pointing forward, bend 90: the forearm swings up (no forward reference)")

	# --- the palm -------------------------------------------------------------------------------------------------------
	check(near(PoseModel.palm_direction(hanging, 0), Vector3(0, 0, -1)), "palm turn 0: towards the body")
	check(near(PoseModel.palm_direction(hanging, 90), Vector3(1, 0, 0)), "palm turn 90: forward (towards the viewer)")
	check(near(PoseModel.palm_direction(hanging, -90), Vector3(-1, 0, 0)), "palm turn -90: backward")
	check(near(PoseModel.palm_direction(hanging, 180), Vector3(0, 0, 1)), "palm turn 180: away from the body")

	# --- the whole arm: neutral = the relaxed arm of the engine --------------------------------------------------------------
	var neutral := PoseModel.arm_entry({})
	check(angle_between(neutral["upper"], GestureEngine.BASE["upper"]["dir"]) < 1.5, "neutral angles give the relaxed upper arm (%.2f deg off)" % angle_between(neutral["upper"], GestureEngine.BASE["upper"]["dir"]))
	check(angle_between(neutral["lower"]["dir"], GestureEngine.BASE["lower"]["dir"]) < 2.0, "... and the relaxed forearm (%.2f deg off)" % angle_between(neutral["lower"]["dir"], GestureEngine.BASE["lower"]["dir"]))
	check(not neutral.has("hand") and neutral["fingers"] == "relaxed", "no wrist bend: the hand follows the forearm, fingers relaxed")
	var wrist := PoseModel.arm_entry({"wrist": 90.0})
	check(wrist.has("hand") and angle_between(wrist["hand"]["dir"], neutral["lower"]["palm"]) < 3.0, "wrist +90 bends the hand towards the palm")
	check(PoseModel.arm_entry({"fingers": "fist"})["fingers"] == "fist" and PoseModel.arm_entry({"fingers": {"index": 100}})["fingers"]["index"] == 100, "finger specs are passed on")

	# --- the torso ------------------------------------------------------------------------------------------------------------------
	check(near(PoseModel.torso_euler({"torso_lean": 10, "torso_side": 5, "torso_turn": -7}), Vector3(10, -7, -5)), "torso: lean = pitch, turn = yaw, side = minus roll")
	check(PoseModel.torso_euler({}) == Vector3.ZERO, "no torso values: no rotation")

	# --- a gesture made of angles as the engine plays it ------------------------------------------------------------------------------
	var doc := {"name": "cheer_v", "description": "arms up", "expression": "happy", "reach": 0.5, "hold": 1.0,
			"pose": {"R": {"upper_raise": 150, "upper_direction": 20, "hand_turn": 90, "fingers": "open"}, "torso": {"torso_lean": -6}}}
	var g := PoseModel.gesture_from_pose(doc)
	check(g["keys"].size() == 3 and g["keys"][0]["t"] == 0.0 and g["keys"][1]["t"] == 0.5 and g["keys"][2]["t"] == 1.5, "three keys: neutral, final pose after reach, held until reach + hold")
	check(is_equal_approx(g["duration"], 1.5) and g["kind"] == "pose" and g["expression"] == "happy", "duration, kind and the expression of the face")
	check(not g["keys"][0].has("R") and g["keys"][1].has("R") and not g["keys"][1].has("L"), "the first key is neutral; only the arm that was given moves")
	check(near(Vector3(g["keys"][1]["torso"][0], g["keys"][1]["torso"][1], g["keys"][1]["torso"][2]), Vector3(-6, 0, 0)), "the torso is part of the final key")
	check(PoseModel.gesture_from_pose({"name": "x", "pose": {}})["keys"].size() == 3 and not PoseModel.gesture_from_pose({"name": "x"}).has("expression"), "an empty pose and a missing expression are harmless")

	# --- the engine ---------------------------------------------------------------------------------------------------------------------
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	for i in 4:
		await process_frame
	var eng: ExpressionEngine = main.engine
	eng.blink_enabled = false
	eng.idle_enabled = false
	var ge: GestureEngine = eng.gestures
	ge.set_process(false)
	var shipped := ge.library.size()
	var emitted := [0]
	ge.library_changed.connect(func(): emitted[0] += 1)
	ge.set_pose_gestures([doc, {"name": "lean_left", "pose": {"torso": {"torso_side": 10, "torso_turn": 20}}}, {"name": "wave", "pose": {"R": {"upper_raise": 90}}}, {"bad": 1}, 5])
	check(ge.library.size() == shipped + 2 and ge.library_order.has("cheer_v") and ge.library_order.has("lean_left"), "gestures of the editor are added (2 new; a clash with a built in name and garbage are ignored)")
	check(not ge.library["wave"].has("kind"), "a built in gesture is never replaced")
	check(emitted[0] == 1, "one library_changed for the whole list")
	ge.set_pose_gestures([doc])
	check(ge.library.size() == shipped + 1 and not ge.library.has("lean_left"), "a new list replaces the old gestures of the editor")
	ge.set_pose_gestures([])
	check(ge.library.size() == shipped and not ge.library.has("cheer_v"), "without gestures of the editor only the built in ones remain")
	ge.set_pose_gestures([doc])

	var spine := eng._skeleton.find_bone("Spine")
	var chest := eng._skeleton.find_bone("UpperChest")
	var hand := eng._skeleton.find_bone("RightHand")
	for i in 90:
		ge.advance(1.0 / 30.0)
	eng.advance(0.0)
	var hand_rest := eng._skeleton.get_bone_global_pose(hand).origin
	var chest_rest := eng._skeleton.get_bone_global_pose(chest).basis

	check(ge.play("cheer_v"), "the gesture of the editor plays")
	for i in 36:                                   # 1.2 s: the pose is reached (0.5 s) and held (until 1.5 s)
		ge.advance(1.0 / 30.0)
	eng.advance(0.0)
	var target_up := PoseModel.upper_direction(150, 20)
	var shown_up: Vector3 = ge._dir["R"]["upper"]
	check(rad_to_deg(shown_up.angle_to(target_up)) < 4.0, "the right arm reaches the pose (%.1f deg off)" % rad_to_deg(shown_up.angle_to(target_up)))
	check(rad_to_deg((ge._dir["L"]["upper"] as Vector3).angle_to(Vector3(0, -0.93, 0.37))) < 4.0, "the left arm, not part of the pose, stays relaxed")
	check(absf(ge.torso_euler.x - (-6.0)) < 0.6, "the torso leans back by the angle (pitch %.1f)" % ge.torso_euler.x)
	check(eng._skeleton.get_bone_global_pose(hand).origin.y > hand_rest.y + 0.3, "the hand is much higher than at rest")
	var chest_leaning := eng._skeleton.get_bone_global_pose(chest).basis
	check(chest_leaning.y.angle_to(chest_rest.y) > deg_to_rad(1.5), "the spine bones really lean (%.1f deg)" % rad_to_deg(chest_leaning.y.angle_to(chest_rest.y)))

	# after the hold the arms and the torso ease back
	for i in 150:
		ge.advance(1.0 / 30.0)
	check(not ge.is_playing() and ge.torso_euler.length() < 0.3 and rad_to_deg((ge._dir["R"]["upper"] as Vector3).angle_to(Vector3(0, -0.93, 0.37))) < 4.0, "after the gesture the arms and the torso are back to neutral")

	# --- the angles are in the character's frame: the torso moves the shoulders, the arm directions stay -----------------------------------------
	ge.set_pose_gestures([{"name": "lean_only", "pose": {"torso": {"torso_lean": 25}}, "reach": 0.3, "hold": 5.0}])
	var hand_before := eng._skeleton.get_bone_global_pose(hand).origin
	ge.play("lean_only")
	for i in 60:
		ge.advance(1.0 / 30.0)
	eng.advance(0.0)
	var hand_leaning := eng._skeleton.get_bone_global_pose(hand).origin
	check(hand_leaning.z > hand_before.z + 0.08, "leaning forward 25 deg moves the shoulders and so the hanging hand forward (%.2f m)" % (hand_leaning.z - hand_before.z))
	var upper_bone := eng._skeleton.get_bone_global_pose(eng._skeleton.find_bone("RightUpperArm")).origin
	var lower_bone := eng._skeleton.get_bone_global_pose(eng._skeleton.find_bone("RightLowerArm")).origin
	var seen := (lower_bone - upper_bone).normalized()
	var wanted: Vector3 = ge._to_model(ge._dir["R"]["upper"], "R").normalized()
	check(rad_to_deg(seen.angle_to(wanted)) < 3.0, "the upper arm still points where the angles say, whatever the torso does (%.1f deg off)" % rad_to_deg(seen.angle_to(wanted)))
	ge.stop()

	# --- fingers in percent ------------------------------------------------------------------------------------------------------------------------
	check(ge._curl_of({"index": 100}, "Index") == ge._pose_curl("fist", "Index"), "finger 100: like the fist")
	check(ge._curl_of({"index": 0}, "Index") == ge._pose_curl("open", "Index"), "finger 0: like the open hand")
	check(ge._curl_of({"index": 50}, "Index").is_equal_approx(ge._pose_curl("open", "Index").lerp(ge._pose_curl("fist", "Index"), 0.5)), "finger 50: halfway")
	check(ge._curl_of({"index": 100}, "Middle") == ge._pose_curl("relaxed", "Middle"), "a finger that is not mentioned stays relaxed")
	check(ge._curl_of("point", "Index") == ge._pose_curl("point", "Index"), "names still work")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
