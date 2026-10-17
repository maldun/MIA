extends SceneTree
# Renders the expression editor into a PNG (needs a display). With MIA_URL set the editor is connected to the server.
# Run: godot --path ui/godot --script res://tools/editor_shot.gd -- <out.png> [width] [height] [preset] [filter]

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out := args[0] if args.size() > 0 else "user://editor.png"
	var size := Vector2i(int(args[1]) if args.size() > 2 else 1280, int(args[2]) if args.size() > 2 else 720)
	var preset := args[3] if args.size() > 3 else "smug"
	var filter := args[4] if args.size() > 4 else ""
	DisplayServer.window_set_size(size)
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	for i in 6:
		await process_frame
	var eng: ExpressionEngine = main.engine
	eng.blink_enabled = false
	eng.idle_enabled = false
	var deadline := Time.get_ticks_msec() + 6000
	while not main.preset_api.available and Time.get_ticks_msec() < deadline and not OS.get_environment("MIA_URL").is_empty():
		await process_frame
	main.show_view("bust")
	main.open_editor()
	main.editor.load_preset(preset)
	if not filter.is_empty():
		main.editor._filter.text = filter
		main.editor._filter.text_changed.emit(filter)
	eng.gestures.stop()
	for i in 40:
		await process_frame
	print("EDITOR rect ", main.editor.get_global_rect(), " anchors ", [main.editor.anchor_left, main.editor.anchor_top, main.editor.anchor_right, main.editor.anchor_bottom], " min ", main.editor.get_combined_minimum_size())
	get_root().get_texture().get_image().save_png(out)
	print("SAVED ", out, " window ", DisplayServer.window_get_size(), " viewport ", get_root().get_visible_rect().size)
	quit()
