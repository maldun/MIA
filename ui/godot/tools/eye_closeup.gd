extends SceneTree
# Close-up of the eyes for material debugging (needs a display).
# Run: godot --path ui/godot --script res://tools/eye_closeup.gd -- <out.png> [hide:<surface name part>|noengine]
func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var root := get_root()
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await process_frame
	for layer in main.find_children("*", "CanvasLayer", true, false):
		layer.visible = false
	main.engine.blink_enabled = false
	main.engine.idle_enabled = false
	if args.size() > 1 and args[1].begins_with("no"):
		main.engine.set_process(false)
		if args[1] == "noarms":
			for b in ["LeftUpperArm", "RightUpperArm"]:
				main.skeleton.set_bone_pose_rotation(main.skeleton.find_bone(b), Quaternion.IDENTITY)
		if args[1] in ["noengine", "nobones"]:
			main.skeleton.reset_bone_poses()
		if args[1] in ["noengine", "noshapes"]:
			for mi in main.character.find_children("*", "MeshInstance3D", true, false):
				for i in mi.mesh.get_blend_shape_count():
					mi.set_blend_shape_value(i, 0.0)
	elif args.size() > 1:
		var face := main.character.find_child("Face", true, false) as MeshInstance3D
		var hidden := StandardMaterial3D.new()
		hidden.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		hidden.albedo_color = Color(1, 0, 1, 0)
		for i in face.mesh.get_surface_count():
			if String(face.mesh.surface_get_name(i)).contains(args[1]):
				face.set_surface_override_material(i, hidden)
	main.set_camera(Vector3(0, main.head_height + 0.04, 0), 0.3)
	for i in 6:
		await process_frame
	root.get_texture().get_image().save_png(args[0])
	quit()
