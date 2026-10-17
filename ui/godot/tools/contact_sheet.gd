extends SceneTree
# Renders a close-up of the face for every preset into <out_dir>/<name>.png (needs a display).
# Run: godot --path ui/godot --script res://tools/contact_sheet.gd -- <out_dir>

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "user://sheet"
	DirAccess.make_dir_recursive_absolute(out_dir)
	var root := get_root()
	root.size = Vector2i(360, 400)
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	for layer in main.find_children("*", "CanvasLayer", true, false):
		layer.visible = false
	main.engine.blink_enabled = false
	main.engine.idle_enabled = false
	main.set_camera(Vector3(0, main.head_height - 0.02, 0), 0.8)
	for preset_name in main.engine.library_order:
		main.engine.play(preset_name, 0.0)
		for i in 4:
			await process_frame
		root.get_texture().get_image().save_png("%s/%s.png" % [out_dir, preset_name])
		print("SAVED ", preset_name)
	quit()
