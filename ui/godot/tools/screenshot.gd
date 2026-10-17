extends SceneTree
# Renders the main scene once and saves a PNG (needs a display, not --headless).
# Run: godot --path ui/godot --script res://tools/screenshot.gd -- <out.png> [yaw_degrees]

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out := args[0] if args.size() > 0 else "user://shot.png"
	var root := get_root()
	root.size = Vector2i(720, 960)
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	if args.size() > 1:
		main.yaw = deg_to_rad(float(args[1]))
	if args.size() > 2:
		main.distance = float(args[2])
	main._update_camera()
	for i in 10:
		await process_frame
	var img := root.get_texture().get_image()
	img.save_png(out)
	print("SAVED ", out, " ", img.get_size())
	quit()
