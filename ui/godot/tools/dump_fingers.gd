extends SceneTree
func _init() -> void:
	var root: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(root)
	var sk: Skeleton3D = root.find_child("GeneralSkeleton", true, false)
	for i in sk.get_bone_count():
		var n := sk.get_bone_name(i)
		if n.begins_with("Left") and (n.contains("Thumb") or n.contains("Index") or n.contains("Hand") or n.contains("Middle")):
			var g := sk.get_bone_global_rest(i)
			print("BONE ", n, " parent=", sk.get_bone_name(sk.get_bone_parent(i)), " dir_x=", g.basis.x.snapped(Vector3(0.01,0.01,0.01)), " y=", g.basis.y.snapped(Vector3(0.01,0.01,0.01)), " z=", g.basis.z.snapped(Vector3(0.01,0.01,0.01)))
	quit()
