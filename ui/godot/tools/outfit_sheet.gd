extends SceneTree
# Renders every surface (material slot) of the character on its own, plus the whole character, into <out_dir>/<mesh>_<index>.png (needs a display; use LIBGL_ALWAYS_SOFTWARE=1 for the CPU).
# Shows which part of the outfit is which: input of the character variants (ui/REQUIREMENTS_CORE.md 7).
# Run: godot --path ui/godot --script res://tools/outfit_sheet.gd -- <out_dir> [width] [height] [distance]

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir := args[0] if args.size() > 0 else "user://outfit"
	DirAccess.make_dir_recursive_absolute(out_dir)
	var root := get_root()
	root.size = Vector2i(int(args[1]) if args.size() > 1 else 300, int(args[2]) if args.size() > 2 else 520)
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	for layer in main.find_children("*", "CanvasLayer", true, false):
		layer.visible = false
	main.engine.blink_enabled = false
	main.engine.idle_enabled = false
	main.engine.play("neutral", 0.0)
	main._inset = Vector4.ZERO         # no page covers the window here
	main._inset_goal = Vector4.ZERO
	main.yaw = 0.0
	var hips: Vector3 = main.skeleton.global_transform * main.skeleton.get_bone_global_pose(main.skeleton.find_bone("Hips")).origin
	print("hips at ", hips, " head height ", main.head_height)
	main.set_camera(Vector3(hips.x, main.head_height * 0.55, hips.z), float(args[3]) if args.size() > 3 else 3.4)
	var hidden := StandardMaterial3D.new()
	hidden.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	hidden.albedo_color = Color(1, 1, 1, 0)
	var meshes: Array = main.find_children("*", "MeshInstance3D", true, false)
	for i in 4:
		await process_frame
	root.get_texture().get_image().save_png("%s/whole.png" % out_dir)
	print("SAVED whole")
	for mi in meshes:
		for s in mi.mesh.get_surface_count():
			for other in meshes:
				for t in other.mesh.get_surface_count():
					other.set_surface_override_material(t, null if (other == mi and t == s) else hidden)
			for i in 4:
				await process_frame
			var file := "%s/%s_%d.png" % [out_dir, mi.name, s]
			root.get_texture().get_image().save_png(file)
			print("SAVED ", file.get_file(), " ", mi.mesh.surface_get_name(s))
	quit()
