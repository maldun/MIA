extends SceneTree
# Checks the background pictures (background_manager.gd) with pictures made on the fly.
# Run: godot --headless --path ui/godot --script res://tools/test_background.gd

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

func picture(color: Color, width: int, height: int) -> Image:
	var image := Image.create(width, height, false, Image.FORMAT_RGB8)
	image.fill(color)
	return image

func _init() -> void:
	var dir := ProjectSettings.globalize_path("user://bg_test")
	DirAccess.make_dir_recursive_absolute(dir)
	for old in DirAccess.get_files_at(dir):
		DirAccess.remove_absolute(dir.path_join(old))
	picture(Color(0.2, 0.4, 0.8), 640, 360).save_png(dir.path_join("b_room.png"))
	picture(Color(0.9, 0.5, 0.2), 320, 640).save_jpg(dir.path_join("a_sunset.jpg"))
	picture(Color(0.1, 0.1, 0.1), 3000, 1000).save_png(dir.path_join("c_huge.png"))
	var garbage := FileAccess.open(dir.path_join("d_broken.png"), FileAccess.WRITE)
	garbage.store_string("this is not a picture")
	garbage.close()
	var notes := FileAccess.open(dir.path_join("notes.txt"), FileAccess.WRITE)
	notes.store_string("not a picture either")
	notes.close()

	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	for i in 4:
		await process_frame
	var bg: BackgroundManager = main.backgrounds
	bg.local_dir = dir
	var listed := [[]]
	bg.list_changed.connect(func(names, default_name): listed[0] = [names, default_name])
	bg.refresh()
	check(bg.names == ["a_sunset.jpg", "b_room.png", "c_huge.png", "d_broken.png"], "lists only pictures, sorted (got %s)" % [bg.names])
	check(bg.default_name == "a_sunset.jpg" and bg.current == "a_sunset.jpg", "the first picture is shown at the start")
	check(listed[0].size() == 2 and listed[0][1] == "a_sunset.jpg", "list_changed announces the list and the default")

	var shown := bg._picture
	check(shown.visible and shown.texture.get_size() == Vector2(320, 640), "the jpg is shown at its size")
	check(shown.stretch_mode == TextureRect.STRETCH_KEEP_ASPECT_COVERED, "it covers the view (cropped, not stretched)")

	bg.show_background("b_room.png")
	check(bg.current == "b_room.png" and shown.texture.get_size() == Vector2(640, 360), "switching to the png works")
	bg.show_background("c_huge.png")
	check(shown.texture.get_width() == BackgroundManager.MAX_SIZE and absi(shown.texture.get_height() - 683) <= 1, "huge pictures are scaled down (got %s)" % shown.texture.get_size())

	bg.show_background("b_room.png")
	bg.show_background("d_broken.png")
	check(bg.current == "" and not shown.visible, "a broken picture falls back to the plain colour")
	bg.show_background("b_room.png")
	bg.show_background("nope.png")
	check(bg.current == "" and not shown.visible, "an unknown name falls back to the plain colour")
	bg.show_background("b_room.png")
	bg.show_background("")
	check(not shown.visible and bg.current == "", "'' shows the plain colour")

	# the menu offers the pictures (row "Background") and switches them
	var by_text := {}
	for b in main.find_children("*", "Button", true, false):
		by_text[(b as Button).text] = b
	check(by_text.has("none") and by_text.has("b_room.png"), "the menu has a Background row with the pictures")
	if by_text.has("b_room.png"):
		(by_text["b_room.png"] as Button).pressed.emit()
		check(bg.current == "b_room.png", "the menu button shows the picture")
		check((main._buttons["background:b_room.png"] as Button).modulate != Color.WHITE, "and highlights it")
		(by_text["none"] as Button).pressed.emit()
		check(bg.current == "", "'none' shows the plain colour")

	# the page can switch the background through the bridge
	check(main.bridge.handle_json('{"type": "background", "name": "a_sunset.jpg"}') and bg.current == "a_sunset.jpg", "bridge message changes the picture")
	main.bridge.handle_json('{"type": "background", "name": ""}')
	check(bg.current == "", "bridge message with an empty name removes it")

	# it is drawn behind the character: canvas layer -1 and the environment shows it
	check(bg._layer.layer == -1, "the picture is on canvas layer -1")
	var env: Environment = (main.find_children("*", "WorldEnvironment", true, false)[0] as WorldEnvironment).environment
	check(env.background_mode == Environment.BG_CANVAS and env.background_canvas_max_layer == -1, "the environment shows canvas layers up to -1")

	# without a folder nothing breaks
	bg.local_dir = dir.path_join("does_not_exist")
	bg.refresh()
	check(bg.names.is_empty() and bg.current == "", "a missing folder gives an empty list and the plain colour")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
