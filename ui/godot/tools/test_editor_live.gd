extends SceneTree
# End-to-end: the editor against a running MIA web app (real HTTP), with a second client as "another device".
# Start MIA's web app first. Run: MIA_URL=http://localhost:8585 godot --headless --path ui/godot --script res://tools/test_editor_live.gd
# (needs a display or --headless; creates and deletes a preset called live_test_*)

var failures := 0

func check(cond: bool, what: String) -> void:
	print(("PASS  " if cond else "FAIL  ") + what)
	if not cond:
		failures += 1

## waits (at most `seconds`) until the condition holds; true if it did
func wait_for(cond: Callable, seconds := 8.0) -> bool:
	var end := Time.get_ticks_msec() + int(seconds * 1000.0)
	while Time.get_ticks_msec() < end:
		if cond.call():
			return true
		await process_frame
	return cond.call()

func _init() -> void:
	var url := OS.get_environment("MIA_URL")
	if url.is_empty():
		print("SKIP  MIA_URL is not set (address of MIA's web app, e.g. http://localhost:8585)")
		quit(0)
		return
	var main := (load("res://main.tscn") as PackedScene).instantiate()
	get_root().add_child(main)
	await process_frame
	var eng: ExpressionEngine = main.engine
	var ed: ExpressionEditor = main.editor
	var api: PresetApi = main.preset_api
	eng.blink_enabled = false
	eng.idle_enabled = false

	check(await wait_for(func(): return api.available), "the character connects to MIA's preset server (%s)" % url)
	check(await wait_for(func(): return eng.library.size() >= 14), "the presets of the server are loaded (%d)" % eng.library.size())
	check("idle" in api.protected_names, "the server tells which presets MIA's emotions use")

	var created := "live_test_%d" % (Time.get_ticks_msec() % 100000)
	ed.open()
	ed.start_new()
	(ed._rows["Fcl_EYE_Surprised"]["slider"] as HSlider).value = 0.8
	(ed._rows["Fcl_MTH_Small"]["slider"] as HSlider).value = 0.35
	(ed._bone_rows["head_roll"]["slider"] as HSlider).value = 7.0
	ed._name_edit.text = created
	ed._description_edit.text = "made by the live test"
	ed._tags_edit.text = "test, live"
	ed._save_new()
	check(await wait_for(func(): return eng.library.has(created) and ed.loaded_name == created), "'Save as new' reaches the server and comes back (%s)" % created)

	# another device: a separate client that only knows the server
	var other := PresetApi.new()
	main.add_child(other)
	other.setup(url)
	var seen := [[]]
	other.library_received.connect(func(presets: Array, _i): seen[0] = presets)
	other.refresh()
	await wait_for(func(): return not (seen[0] as Array).is_empty())
	var found: Dictionary = {}
	for p in seen[0]:
		if p["name"] == created:
			found = p
	check(not found.is_empty(), "another device sees the new preset")
	check(not found.is_empty() and absf(found["weights"]["Fcl_EYE_Surprised"] - 0.8) < 0.001 and absf(found["bones"]["head_roll"] - 7.0) < 0.01
			and found["description"] == "made by the live test" and found["tags"] == ["test", "live"] and found["source"] == "manual",
			"with weights, bones, description, tags and source")

	# change it on this device, the other device notices through the version
	(ed._rows["Fcl_MTH_Small"]["slider"] as HSlider).value = 0.6
	ed._overwrite()
	var old_version := other.version
	other.check_version()
	check(await wait_for(func(): return other.version != old_version), "the other device notices the change (version %s -> %s)" % [old_version, other.version])

	# rename and delete
	var renamed := created + "_renamed"
	ed._name_edit.text = renamed
	ed._rename()
	check(await wait_for(func(): return eng.library.has(renamed) and not eng.library.has(created)), "rename works")
	ed._delete()
	ed._delete()
	check(await wait_for(func(): return not eng.library.has(renamed)), "delete works")
	seen[0] = []   # forget the old answer, wait for the new one
	other.refresh()
	await wait_for(func(): return not (seen[0] as Array).is_empty())
	var still := false
	for p in seen[0]:
		still = still or p["name"] == renamed or p["name"] == created
	check(not still, "and the other device no longer sees it")

	# the server protects what MIA uses; invalid data is corrected
	ed.load_preset("idle")
	ed._delete()
	ed._delete()
	await wait_for(func(): return ed._status.text.contains("cannot be deleted"), 4.0)
	check(eng.library.has("idle") and ed._status.text.contains("MIA"), "the server refuses to delete 'idle' (used by MIA)")

	# the real corrections of the server: a made-up shape key
	var result := [{}]
	api.operation_done.connect(func(_k, _ok, _m, data: Dictionary): result[0] = data)
	var bad := {"name": created + "_c", "weights": {"Fcl_MTH_Joy": 4.0, "Not_A_Key": 1.0}, "gesture": "dance"}
	api.create(bad)
	await wait_for(func(): return not (result[0] as Dictionary).is_empty())
	var stored: Dictionary = (result[0] as Dictionary).get("preset", {})
	check(stored.get("weights", {}) == {"Fcl_MTH_Joy": 1.0} and stored.get("gesture", "x") == "" and (result[0]["corrections"] as Array).size() == 3,
			"the server corrects values like the character does (3 corrections)")
	result[0] = {}
	api.delete(created + "_c")
	await wait_for(func(): return not (result[0] as Dictionary).is_empty())   # wait until the server answered
	api.refresh()
	await wait_for(func(): return not eng.library.has(created + "_c"))
	check(not eng.library.has(created + "_c"), "cleaned up")

	print("RESULT ", "ALL PASSED" if failures == 0 else "%d FAILED" % failures)
	quit(0 if failures == 0 else 1)
