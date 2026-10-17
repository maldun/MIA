extends SceneTree
# Loads the imported character, lists every blend shape (shape key) per mesh and
# checks that each one can be driven (set + read back).
# Run: godot --headless --path ui/godot --script res://tools/verify_shapekeys.gd

const CHARACTER := "res://assets/mia.vrm"

func _init() -> void:
	var packed = load(CHARACTER)
	if packed == null:
		push_error("cannot load " + CHARACTER)
		quit(1)
		return
	var root: Node = packed.instantiate()
	get_root().add_child(root)
	var failed := 0
	var names := {}
	for mi in _meshes(root):
		var mesh = mi.mesh
		var n: int = mesh.get_blend_shape_count()
		if n == 0:
			continue
		print("MESH ", mi.name, " blend shapes: ", n)
		for i in n:
			var bs_name := String(mesh.get_blend_shape_name(i))
			names[bs_name] = true
			mi.set_blend_shape_value(i, 0.5)
			if not is_equal_approx(mi.get_blend_shape_value(i), 0.5):
				failed += 1
				print("NOT DRIVABLE ", mi.name, ":", bs_name)
			mi.set_blend_shape_value(i, 0.0)
	var sorted: Array = names.keys()
	sorted.sort()
	print("UNIQUE ", sorted.size())
	for s in sorted:
		print("KEY ", s)
	print("FAILED ", failed)
	quit(0 if failed == 0 else 1)

func _meshes(node: Node) -> Array:
	var out := []
	if node is MeshInstance3D:
		out.append(node)
	for c in node.get_children():
		out.append_array(_meshes(c))
	return out
