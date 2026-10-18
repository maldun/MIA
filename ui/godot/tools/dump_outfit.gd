extends SceneTree
# Lists what the character is made of, per mesh and per surface (material slot): triangles, where it sits (bounding box), the material with its colours and textures, and whether
# a surface could be shown or hidden on its own. Input of the character variants (ui/REQUIREMENTS_CORE.md 7). Prints JSON lines: one "mesh" line and one "surface" line per surface.
# Run: godot --headless --path ui/godot --script res://tools/dump_outfit.gd

func _color_text(c: Color) -> String:
	return "#%02x%02x%02x%s" % [int(c.r * 255), int(c.g * 255), int(c.b * 255), "" if c.a >= 0.999 else "/%.2f" % c.a]

func _init() -> void:
	var root: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(root)
	var skeleton: Skeleton3D = root.find_child("*", true, false) as Skeleton3D
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		print(JSON.stringify({"kind": "mesh", "name": mi.name, "visible": mi.visible, "surfaces": mi.mesh.get_surface_count(), "blend_shapes": mi.mesh.get_blend_shape_count(),
				"skinned": mi.skin != null, "path": str(root.get_path_to(mi))}))
		for i in mi.mesh.get_surface_count():
			var arrays: Array = mi.mesh.surface_get_arrays(i)
			var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var indices = arrays[Mesh.ARRAY_INDEX]
			var low := Vector3(1e9, 1e9, 1e9)
			var high := Vector3(-1e9, -1e9, -1e9)
			for v in verts:
				low = low.min(v)
				high = high.max(v)
			var mat = mi.get_active_material(i)
			var info := {"kind": "surface", "mesh": mi.name, "index": i, "name": mi.mesh.surface_get_name(i), "vertices": verts.size(),
					"triangles": (indices.size() / 3) if indices != null else verts.size() / 3, "min": [snappedf(low.x, 0.001), snappedf(low.y, 0.001), snappedf(low.z, 0.001)],
					"max": [snappedf(high.x, 0.001), snappedf(high.y, 0.001), snappedf(high.z, 0.001)], "material": mat.resource_name if mat else "", "class": mat.get_class() if mat else ""}
			if mat is ShaderMaterial:
				var colors := {}
				var textures := {}
				for p in mat.shader.get_shader_uniform_list():
					var n: String = p["name"]
					var value = mat.get_shader_parameter(n)
					if value is Color:
						colors[n] = _color_text(value)
					elif value is Texture2D:
						textures[n] = "%dx%d" % [(value as Texture2D).get_width(), (value as Texture2D).get_height()]
				info["colors"] = colors
				info["textures"] = textures
				info["outline_pass"] = mat.next_pass != null
				info["render_priority"] = mat.render_priority
			print(JSON.stringify(info))
	quit()
