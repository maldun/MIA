extends SceneTree
# Renders the character once and saves a PNG (needs a display, not --headless).
# Run: godot --path ui/godot --script res://tools/screenshot.gd -- <out.png>

func _init() -> void:
	var out := "user://shot.png"
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out = args[0]
	var root := get_root()
	root.size = Vector2i(720, 960)
	var character: Node = (load("res://assets/mia.vrm") as PackedScene).instantiate()
	root.add_child(character)
	var cam := Camera3D.new()
	root.add_child(cam)
	cam.position = Vector3(0, 1.35, 1.1)
	cam.look_at_from_position(cam.position, Vector3(0, 1.3, 0))
	var light := DirectionalLight3D.new()
	root.add_child(light)
	light.rotation_degrees = Vector3(-30, -20, 0)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color(0.85, 0.87, 0.9)
	root.add_child(env)
	for i in 10:
		await process_frame
	var img := root.get_texture().get_image()
	img.save_png(out)
	print("SAVED ", out, " ", img.get_size())
	quit()
