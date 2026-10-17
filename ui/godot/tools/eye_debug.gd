extends SceneTree
func _init() -> void:
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	await process_frame
	main.engine.blink_enabled = false
	main.engine.idle_enabled = false
	for i in 5:
		await process_frame
	var sk: Skeleton3D = main.skeleton
	for n in ["Head", "UpperChest", "Chest", "LeftEye", "RightEye"]:
		var i := sk.find_bone(n)
		print("BONE ", n, " pose_rot=", sk.get_bone_pose_rotation(i), " pose_pos=", sk.get_bone_pose_position(i), " rest_pos=", sk.get_bone_rest(i).origin)
	quit()
