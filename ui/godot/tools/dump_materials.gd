extends SceneTree
# Prints the materials of the Face mesh (debugging eye rendering).
func _init() -> void:
	var root: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(root)
	var face: MeshInstance3D = root.find_child("Face", true, false)
	for i in face.mesh.get_surface_count():
		var m = face.get_active_material(i)
		print("SURF ", i, " ", face.mesh.surface_get_name(i), " -> ", m.resource_name if m else "none", " ", m.get_class() if m else "")
		if m is ShaderMaterial:
			print("   shader=", m.shader.resource_path.get_file(), " prio=", m.render_priority, " next=", m.next_pass.resource_name if m.next_pass else "-")
			for p in m.shader.get_shader_uniform_list():
				var n: String = p["name"]
				var v = m.get_shader_parameter(n)
				if v is Texture2D:
					print("   ", n, " = tex ", (v as Texture2D).get_size())
				elif n.contains("alpha") or n.contains("Cutoff") or n.contains("cutoff") or n.contains("color") or n.contains("Color"):
					print("   ", n, " = ", v)
	quit()
