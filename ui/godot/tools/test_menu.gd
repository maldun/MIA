extends SceneTree
# Presses the menu buttons of the main scene like a user would and checks the effect.
# Run: godot --headless --path ui/godot --script res://tools/test_menu.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

func button(main: Node, text: String) -> Button:
	for b in main.find_children("*", "Button", true, false):
		if (b as Button).text == text:
			return b
	return null

func frames(n: int) -> void:
	for i in n:
		await process_frame

func click(at: Vector2) -> void:
	var m := InputEventMouseMotion.new()  # buttons need the pointer to hover first
	m.position = at
	m.global_position = at
	get_root().push_input(m)
	await process_frame
	for pressed in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = pressed
		e.position = at
		e.global_position = at
		get_root().push_input(e)
		await process_frame

func center(b: Button) -> Vector2:
	return b.get_global_rect().get_center()

func _init() -> void:
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	await frames(5)
	var eng: ExpressionEngine = main.engine
	var g: GestureEngine = eng.gestures
	var arm: int = main.skeleton.find_bone("RightLowerArm")
	var base_q: Quaternion = main.skeleton.get_bone_pose_rotation(arm)

	button(main, "cheer").pressed.emit()
	await frames(3)
	check(g.current == "cheer", "pressing 'cheer' starts the gesture")
	check(eng.current_name == "happy", "pressing 'cheer' also shows the happy face (got '%s')" % eng.current_name)
	await frames(40)
	check(main.skeleton.get_bone_pose_rotation(arm).angle_to(base_q) > 0.3, "the arm moves while cheering")

	var stop := button(main, "stop gesture")
	check(stop != null, "the 'stop gesture' button exists")
	stop.pressed.emit()
	await frames(3)
	check(g.current == "", "pressing 'stop gesture' ends the gesture")
	await frames(90)
	check(main.skeleton.get_bone_pose_rotation(arm).angle_to(base_q) < 0.05, "the arm returns to the relaxed pose after stop")

	button(main, "talk").pressed.emit()
	await frames(2)
	check(eng.speaking and g.current == "explain", "'talk' speaks and explains")
	var moved := 0.0
	var face := main.find_child("Face", true, false) as MeshInstance3D
	for i in 90:
		await frames(1)
		for v in ExpressionEngine.VOWELS:
			moved = maxf(moved, face.get_blend_shape_value(face.find_blend_shape_by_name(v)))
	check(moved > 0.1, "the mouth moves while talking (max vowel weight %.2f)" % moved)
	button(main, "idle").pressed.emit()
	await frames(30)
	check(not eng.speaking, "the mouth stops moving with another expression")

	if DisplayServer.get_name() == "headless":
		print("SKIP  real clicks need a window (run without --headless)")
		print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
		quit(0 if failures == 0 else 1)
		return
	# the same with real clicks at the buttons' positions, like a user (menu starts collapsed)
	check(not main._bar.visible, "menu starts collapsed")
	await click(center(button(main, "Menu")))
	await frames(2)
	check(main._bar.visible, "clicking 'Menu' opens it")
	await click(center(button(main, "cheer")))
	await frames(3)
	check(g.current == "cheer", "a real click on 'cheer' starts the gesture")
	await click(center(button(main, "stop gesture")))
	await frames(3)
	check(g.current == "", "a real click on 'stop gesture' ends the gesture (button at %s)" % center(button(main, "stop gesture")))
	check((main._buttons["gesture:cheer"] as Button).modulate == Color.WHITE, "the highlight of 'cheer' is gone after stop")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
