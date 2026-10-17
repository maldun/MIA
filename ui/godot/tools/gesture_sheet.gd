extends SceneTree
# Renders every gesture (at its second keyframe) into <out_dir>/<name>.png (needs a display).
# Run: godot --path ui/godot --script res://tools/gesture_sheet.gd -- <out_dir> [yaw_degrees] [distance] [pivot height factor] [hand]

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "user://gestures"
	DirAccess.make_dir_recursive_absolute(out_dir)
	var root := get_root()
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	for layer in main.find_children("*", "CanvasLayer", true, false):
		layer.visible = false
	var eng: ExpressionEngine = main.engine
	eng.blink_enabled = false
	eng.idle_enabled = false
	eng.play("neutral", 0.0)
	var g: GestureEngine = eng.gestures
	g.set_process(false)  # stepped by hand below
	main.yaw = deg_to_rad(float(args[1])) if args.size() > 1 else 0.0
	var dist := float(args[2]) if args.size() > 2 else 3.0
	var height := float(args[3]) if args.size() > 3 else 0.55
	main.set_camera(Vector3(0, main.head_height * height, 0), dist)
	var names: Array = ["(base)"] + g.library_order
	for gesture_name in names:
		g.stop()
		for i in 60:
			g.advance(1.0 / 30.0)
		var snap := 0.0
		if gesture_name != "(base)":
			g.play(gesture_name)
			var keys: Array = g.library[gesture_name]["keys"]
			snap = float(keys[1]["t"]) if keys.size() > 1 else float(keys[0]["t"])
			while g._time < snap:
				g.advance(1.0 / 30.0)
			for i in 30:  # let the arms settle on the key pose
				g._time = snap
				g.advance(1.0 / 30.0)
		if args.size() > 4 and args[4] == "hand":  # close-up of the right hand
			var sk: Skeleton3D = main.skeleton
			var hand := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("RightHand")).origin
			main.set_camera(hand, 0.55)
		for i in 3:
			await process_frame
		root.get_texture().get_image().save_png("%s/%s.png" % [out_dir, str(gesture_name).replace("(", "").replace(")", "")])
		print("SAVED ", gesture_name)
	quit()
