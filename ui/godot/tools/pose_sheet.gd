extends SceneTree
# Renders gestures made of angles (documents like the gesture editor saves them) into <out_dir>/<name>.png at their final pose (needs a display).
# Run: godot --path ui/godot --script res://tools/pose_sheet.gd -- <out_dir> <docs.json> [yaw_degrees] [distance] [pivot height factor] [hand]
# docs.json: {"gestures": [{"name": "...", "pose": {"R": {...}, "L": {...}, "torso": {...}}, "reach": 0.6, "hold": 1.5}, ...]}

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "user://poses"
	DirAccess.make_dir_recursive_absolute(out_dir)
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(args[1])) if args.size() > 1 else null
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("pose_sheet: docs.json is missing or not an object")
		quit(1)
		return
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
	g.set_process(false)
	g.set_pose_gestures(parsed["gestures"])
	main.yaw = deg_to_rad(float(args[2])) if args.size() > 2 else 0.0
	var dist := float(args[3]) if args.size() > 3 else 3.0
	var height := float(args[4]) if args.size() > 4 else 0.55
	main.set_camera(Vector3(0, main.head_height * height, 0), dist)
	for doc in parsed["gestures"]:
		g.stop()
		for i in 90:
			g.advance(1.0 / 30.0)
			eng.advance(1.0 / 30.0)
		g.play(doc["name"])
		var until: float = float(doc.get("reach", 0.6)) + minf(float(doc.get("hold", 1.5)), 1.0) * 0.8
		while g._time < until:
			g.advance(1.0 / 30.0)
			eng.advance(1.0 / 30.0)
		for i in 20:       # let the arms settle on the final pose
			g._time = until
			g.advance(1.0 / 30.0)
			eng.advance(1.0 / 30.0)
		if args.size() > 5 and args[5] == "hand":
			var sk: Skeleton3D = main.skeleton
			var hand := sk.global_transform * sk.get_bone_global_pose(sk.find_bone("RightHand")).origin
			main.set_camera(hand, 0.55)
		for i in 3:
			await process_frame
		root.get_texture().get_image().save_png("%s/%s.png" % [out_dir, str(doc["name"])])
		print("SAVED ", doc["name"])
	quit()
