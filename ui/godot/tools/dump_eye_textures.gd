extends SceneTree
func _init() -> void:
	var out := OS.get_cmdline_user_args()[0]
	var root: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	get_root().add_child(root)
	var face: MeshInstance3D = root.find_child("Face", true, false)
	for i in face.mesh.get_surface_count():
		var n := String(face.mesh.surface_get_name(i))
		var m := face.get_active_material(i) as ShaderMaterial
		for key in ["Iris", "Highlight", "EyeWhite"]:
			if n.contains(key):
				var tex := m.get_shader_parameter("_MainTex") as Texture2D
				var img := tex.get_image()
				if img.is_compressed():
					img.decompress()
				img.convert(Image.FORMAT_RGBA8)
				img.save_png("%s/tex_%s.png" % [out, key])
				print("TEX ", key, " ", img.get_size(), " alpha-min-max: ", _alpha(img))
	quit()
func _alpha(img: Image) -> String:
	var lo := 1.0
	var hi := 0.0
	for y in range(0, img.get_height(), 8):
		for x in range(0, img.get_width(), 8):
			var a := img.get_pixel(x, y).a
			lo = minf(lo, a)
			hi = maxf(hi, a)
	return "%.2f-%.2f" % [lo, hi]
