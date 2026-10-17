class_name ExpressionEngine
extends Node
## Central expression API (ui/REQUIREMENTS.md 4.4). Every input source (debug buttons,
## MIA bridge, editor, LLM, ...) only calls play() / apply_preset().
##
## Preset: {"name", "description", "weights": {shape key: 0..1}, "bones": {param: degrees},
##          "tags": [], "source": "manual" | "llm" | "llm_edited"}
## Bone params: head_pitch (+ = looks down), head_yaw (+ = turns to the viewer's right),
## head_roll (+ = top of the head to the viewer's left), eye_yaw, eye_pitch (same signs).

signal expression_changed(preset_name: String)

const BLINK_KEY := "Fcl_EYE_Close"
## keys that already close the eyes: no extra blinking while they are high
const EYE_CLOSING_KEYS := ["Fcl_EYE_Close", "Fcl_EYE_Close_L", "Fcl_EYE_Close_R", "Fcl_EYE_Joy"]
const EYE_CLOSED_LEVEL := 0.6
const BONE_PARAMS := ["head_pitch", "head_yaw", "head_roll", "eye_pitch", "eye_yaw"]
const BONE_LIMIT_DEG := 45.0
const BLINK_CLOSE_TIME := 0.07
const BLINK_OPEN_TIME := 0.12
const BLINK_MIN_INTERVAL := 2.5
const BLINK_MAX_INTERVAL := 6.0

var default_duration := 0.25
## "smooth" (smoothstep), "linear", "sine" or "cubic"
var easing := "smooth"
var blink_enabled := true
var idle_enabled := true
var library := {}        # preset name -> validated preset
var library_order: Array[String] = []
var current_name := ""

var _meshes: Array = []  # [{"mi": MeshInstance3D, "index": {shape name: index}}]
var _shapes := {}        # all known shape key names
var _skeleton: Skeleton3D
var _bone := {}          # "Head" -> index, ...

var _from_w := {}
var _to_w := {}
var _from_b := {}
var _to_b := {}
var _shown_w := {}       # blended weights without blink
var _shown_b := {}
var _t := 1.0
var _dur := 0.0
var _applied := {}       # shape keys written last frame

var _clock := 0.0
var _blink_wait := 3.0
var _blink_time := -1.0  # < 0: not blinking

func setup(character: Node, skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
	for mi in character.find_children("*", "MeshInstance3D", true, false):
		var mesh = mi.mesh
		var n: int = mesh.get_blend_shape_count() if mesh != null else 0
		if n == 0:
			continue
		var index := {}
		for i in n:
			var key := String(mesh.get_blend_shape_name(i))
			index[key] = i
			_shapes[key] = true
		_meshes.append({"mi": mi, "index": index})
	if skeleton != null:
		for b in ["Spine", "Chest", "UpperChest", "Neck", "Head", "LeftEye", "RightEye"]:
			_bone[b] = skeleton.find_bone(b)
	_blink_wait = randf_range(BLINK_MIN_INTERVAL, BLINK_MAX_INTERVAL)

func get_shape_names() -> Array:
	var names := _shapes.keys()
	names.sort()
	return names

# --- library -------------------------------------------------------------------------

## Loads {"presets": [...]} (the documented library format). Returns the number of valid presets.
func load_library(path: String) -> int:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("presets")) != TYPE_ARRAY:
		push_error("expression library %s is not {\"presets\": [...]}" % path)
		return 0
	library.clear()
	library_order.clear()
	for raw in parsed["presets"]:
		var result := validate(raw)
		if result["preset"] == null:
			continue
		var preset: Dictionary = result["preset"]
		library[preset["name"]] = preset
		library_order.append(preset["name"])
	return library.size()

## Checks a preset: rejects unknown shape keys and bone params, clamps values.
## Returns {"preset": Dictionary or null, "corrections": Array[String]} and logs every correction.
func validate(raw) -> Dictionary:
	var corrections: Array[String] = []
	if typeof(raw) != TYPE_DICTIONARY or typeof(raw.get("name")) != TYPE_STRING or String(raw["name"]).is_empty():
		corrections.append("preset without a name rejected")
		_log_corrections("?", corrections)
		return {"preset": null, "corrections": corrections}
	var name: String = raw["name"]
	var weights := {}
	var raw_weights = raw.get("weights", {})
	if typeof(raw_weights) != TYPE_DICTIONARY:
		corrections.append("weights is not a dictionary, ignored")
		raw_weights = {}
	for key in raw_weights:
		var v = raw_weights[key]
		if not _shapes.is_empty() and not _shapes.has(key):
			corrections.append("unknown shape key '%s' removed" % key)
		elif typeof(v) != TYPE_FLOAT and typeof(v) != TYPE_INT:
			corrections.append("weight '%s' is not a number, removed" % key)
		else:
			var c := clampf(float(v), 0.0, 1.0)
			if not is_equal_approx(c, float(v)):
				corrections.append("weight '%s' clamped from %s to %s" % [key, v, c])
			weights[key] = c
	var bones := {}
	var raw_bones = raw.get("bones", {})
	if typeof(raw_bones) != TYPE_DICTIONARY:
		corrections.append("bones is not a dictionary, ignored")
		raw_bones = {}
	for key in raw_bones:
		var v = raw_bones[key]
		if not BONE_PARAMS.has(key):
			corrections.append("unknown bone parameter '%s' removed" % key)
		elif typeof(v) != TYPE_FLOAT and typeof(v) != TYPE_INT:
			corrections.append("bone '%s' is not a number, removed" % key)
		else:
			var c := clampf(float(v), -BONE_LIMIT_DEG, BONE_LIMIT_DEG)
			if not is_equal_approx(c, float(v)):
				corrections.append("bone '%s' clamped from %s to %s" % [key, v, c])
			bones[key] = c
	var source: String = raw.get("source", "manual")
	if not ["manual", "llm", "llm_edited"].has(source):
		corrections.append("unknown source '%s' set to manual" % source)
		source = "manual"
	var tags: Array = []
	if typeof(raw.get("tags")) == TYPE_ARRAY:
		for t in raw["tags"]:
			tags.append(str(t))
	_log_corrections(name, corrections)
	return {"preset": {"name": name, "description": str(raw.get("description", "")),
			"weights": weights, "bones": bones, "tags": tags, "source": source},
			"corrections": corrections}

func _log_corrections(name: String, corrections: Array) -> void:
	for c in corrections:
		push_warning("preset '%s': %s" % [name, c])

# --- the central API --------------------------------------------------------------------

## Plays a preset from the library. Unknown names keep the current expression.
func play(preset_name: String, duration := -1.0) -> bool:
	if not library.has(preset_name):
		push_warning("unknown expression '%s', keeping '%s'" % [preset_name, current_name])
		return false
	apply_preset(library[preset_name], duration)
	return true

## Plays any preset dictionary (e.g. from the editor or the LLM); it is validated first.
func apply_preset(preset: Dictionary, duration := -1.0) -> bool:
	var result := validate(preset)
	if result["preset"] == null:
		return false
	var p: Dictionary = result["preset"]
	_from_w = _shown_w.duplicate()
	_from_b = _shown_b.duplicate()
	_to_w = p["weights"]
	_to_b = p["bones"]
	_dur = default_duration if duration < 0.0 else duration
	_t = 0.0 if _dur > 0.0 else 1.0
	current_name = p["name"]
	if _dur <= 0.0:
		advance(0.0)
	expression_changed.emit(current_name)
	return true

# --- per frame ----------------------------------------------------------------------------

func _process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	_clock += delta
	if _t < 1.0:
		_t = minf(1.0, _t + delta / _dur)
	var k := _ease(_t)
	_shown_w = _mix(_from_w, _to_w, k)
	_shown_b = _mix(_from_b, _to_b, k)

	var out := _shown_w.duplicate()
	var blink := _update_blink(delta)
	if blink > 0.0:
		out[BLINK_KEY] = maxf(out.get(BLINK_KEY, 0.0), blink)
	_write_shapes(out)
	_write_bones()

func eyes_closed_level() -> float:
	var level := 0.0
	for key in EYE_CLOSING_KEYS:
		level = maxf(level, _shown_w.get(key, 0.0))
	return level

func _update_blink(delta: float) -> float:
	if not blink_enabled:
		_blink_time = -1.0
		return 0.0
	if _blink_time < 0.0:
		_blink_wait -= delta
		if _blink_wait > 0.0:
			return 0.0
		_blink_wait = randf_range(BLINK_MIN_INTERVAL, BLINK_MAX_INTERVAL)
		if eyes_closed_level() >= EYE_CLOSED_LEVEL:
			return 0.0  # eyes are closed anyway
		_blink_time = 0.0
	_blink_time += delta
	if _blink_time < BLINK_CLOSE_TIME:
		return _blink_time / BLINK_CLOSE_TIME
	if _blink_time < BLINK_CLOSE_TIME + BLINK_OPEN_TIME:
		return 1.0 - (_blink_time - BLINK_CLOSE_TIME) / BLINK_OPEN_TIME
	_blink_time = -1.0
	return 0.0

func _write_shapes(out: Dictionary) -> void:
	for key in out:
		_set_shape(key, out[key])
	for key in _applied:
		if not out.has(key):
			_set_shape(key, 0.0)  # keys not in the preset blend back to 0
	_applied = out

func _set_shape(key: String, value: float) -> void:
	for m in _meshes:
		if m["index"].has(key):
			(m["mi"] as MeshInstance3D).set_blend_shape_value(m["index"][key], value)

func _write_bones() -> void:
	if _skeleton == null:
		return
	var sway := Vector3.ZERO
	var breath := 0.0
	if idle_enabled:
		sway = Vector3(
				sin(_clock * 0.29 + 1.0) * 0.8 + sin(_clock * 0.71) * 0.3,
				sin(_clock * 0.37) * 1.2 + sin(_clock * 0.91) * 0.5,
				sin(_clock * 0.23 + 2.0) * 0.9)
		breath = sin(_clock * TAU * 0.22) * 0.6
	var head := Vector3(_shown_b.get("head_pitch", 0.0) + sway.x,
			_shown_b.get("head_yaw", 0.0) + sway.y, _shown_b.get("head_roll", 0.0) + sway.z)
	_rotate("Head", head)
	_rotate("UpperChest", Vector3(breath, 0, 0))
	_rotate("Chest", Vector3(breath * 0.5, 0, 0))
	var eye := Vector3(_shown_b.get("eye_pitch", 0.0), _shown_b.get("eye_yaw", 0.0), 0.0)
	_rotate("LeftEye", eye)
	_rotate("RightEye", eye)

## Rotates a bone by euler degrees (pitch about X, yaw about Y, roll about Z) in its parent's frame.
func _rotate(bone_name: String, degrees: Vector3) -> void:
	var i: int = _bone.get(bone_name, -1)
	if i < 0:
		return
	var r := Basis(Vector3.UP, deg_to_rad(degrees.y)) * Basis(Vector3.RIGHT, deg_to_rad(degrees.x)) \
			* Basis(Vector3.BACK, deg_to_rad(degrees.z))
	var rest := _skeleton.get_bone_rest(i).basis
	_skeleton.set_bone_pose_rotation(i, (rest.inverse() * r * rest).get_rotation_quaternion())

func _mix(a: Dictionary, b: Dictionary, k: float) -> Dictionary:
	var out := {}
	for key in a:
		out[key] = lerpf(a[key], b.get(key, 0.0), k)
	for key in b:
		if not a.has(key):
			out[key] = lerpf(0.0, b[key], k)
	return out

func _ease(t: float) -> float:
	match easing:
		"linear":
			return t
		"sine":
			return 0.5 - 0.5 * cos(PI * t)
		"cubic":
			return 4.0 * t * t * t if t < 0.5 else 1.0 - pow(-2.0 * t + 2.0, 3.0) / 2.0
		_:
			return t * t * (3.0 - 2.0 * t)
