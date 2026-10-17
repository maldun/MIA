extends SceneTree
# Prints the node tree and the skeleton bones of the imported character.
# Run: godot --headless --path ui/godot --script res://tools/dump_skeleton.gd

func _init() -> void:
	var root: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(root)
	_dump(root, 0)
	for sk in root.find_children("*", "Skeleton3D", true, false):
		var s: Skeleton3D = sk
		print("SKELETON ", s.get_path(), " bones=", s.get_bone_count())
		for i in s.get_bone_count():
			var n := s.get_bone_name(i)
			if n.contains("Arm") or n.contains("Head") or n.contains("Neck") or n.contains("Eye") or n.contains("Spine") or n.contains("Chest"):
				print("BONE ", i, " ", n, " rest=", s.get_bone_rest(i).basis.get_euler())
	quit()

func _dump(n: Node, d: int) -> void:
	print("NODE ", "  ".repeat(d), n.name, " (", n.get_class(), ")")
	if d < 2:
		for c in n.get_children():
			_dump(c, d + 1)
