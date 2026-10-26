extends SceneTree
# Reduced motion (REQ-CHV-009, TC-CHV-009): with the system preference the idle sway of the head and the breathing shrink to a quarter.
# Run: godot --headless --path ui/godot --script res://tools/test_reduced_motion.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

## the largest angle (degrees) that a bone leaves its rest pose within 60 s of idle clock
func largest_swing(eng: ExpressionEngine, bone_name: String) -> float:
	var i: int = eng._bone[bone_name]
	var rest: Quaternion = eng._skeleton.get_bone_rest(i).basis.get_rotation_quaternion()
	var biggest := 0.0
	var t := 0.0
	while t < 60.0:
		eng._clock = t
		eng._write_bones()
		var pose: Quaternion = eng._skeleton.get_bone_pose_rotation(i)
		biggest = maxf(biggest, rad_to_deg(rest.angle_to(pose)))
		t += 0.25
	return biggest

func _init() -> void:
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	for i in 5:
		await process_frame
	var eng: ExpressionEngine = main.engine
	eng.idle_enabled = true
	eng.blink_enabled = false

	check(not eng.reduced_motion, "reduced motion is off by default")
	var head_normal := largest_swing(eng, "Head")
	var chest_normal := largest_swing(eng, "UpperChest")
	check(head_normal > 0.5, "the head sways when motion is normal (%.2f degrees)" % head_normal)
	check(chest_normal > 0.2, "the chest breathes when motion is normal (%.2f degrees)" % chest_normal)

	eng.reduced_motion = true
	var head_reduced := largest_swing(eng, "Head")
	var chest_reduced := largest_swing(eng, "UpperChest")
	check(head_reduced < head_normal * 0.35, "reduced: the head sways a quarter as much (%.2f of %.2f degrees)" % [head_reduced, head_normal])
	check(chest_reduced < chest_normal * 0.35, "reduced: the chest breathes a quarter as much (%.2f of %.2f degrees)" % [chest_reduced, chest_normal])
	check(head_reduced > 0.0, "reduced is not frozen: a little motion is left (%.2f degrees)" % head_reduced)

	eng.reduced_motion = false
	check(absf(largest_swing(eng, "Head") - head_normal) < 0.01, "turning it off gives the normal motion back")

	eng.idle_enabled = false
	check(largest_swing(eng, "Head") < 0.01, "idle switched off: no sway at all")

	print("RESULT " + ("ALL PASSED" if failures == 0 else "%d FAILED" % failures))
	quit(1 if failures > 0 else 0)
