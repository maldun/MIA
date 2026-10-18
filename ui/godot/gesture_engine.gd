class_name GestureEngine
extends Node
## Arm poses, hand poses and gestures (ui/REQUIREMENTS.md 4.4a). Without a gesture the arms hang relaxed (BASE).
##
## Directions are written from the character's point of view as [forward, up, outward]
## (forward = towards the viewer, outward = away from the body, the same numbers work for both arms).
## Limb value: [f, u, o]  or  {"dir": [f, u, o], "palm": [f, u, o]}  (palm = where the palm should face).
## Limbs: "shoulder", "upper" (upper arm), "lower" (forearm), "hand" (follows "lower" if missing).
## Fingers: "fingers": a name from FINGER_POSES ("relaxed", "open", "fist", "point").
##
## Fingers: a name from FINGER_POSES, or {"thumb", "index", "middle", "ring", "little"}: 0 (open) ... 100 (closed) each.
##
## Gesture: {"name", "description", "expression": optional preset name, "duration",
##           "keys": [{"t": seconds, "R": {limb: ..., "fingers": ...}, "L": {...}, "torso": [pitch, yaw, roll] degrees}]}
## Between keys everything is interpolated; after "duration" the arms ease back to BASE.
## Gestures made in the gesture editor (angles of the final pose, see pose_model.gd) are converted into such keys by set_pose_gestures().

signal gesture_started(gesture_name: String)
signal gesture_finished(gesture_name: String)
## gestures were added or removed (the ones made in the editor come and go)
signal library_changed

const LIMBS := ["shoulder", "upper", "lower", "hand"]
const BONES := {"shoulder": "Shoulder", "upper": "UpperArm", "lower": "LowerArm", "hand": "Hand"}
const FINGERS := ["Thumb", "Index", "Middle", "Ring", "Little"]
## bones per finger, proximal to distal (the thumb has a metacarpal instead of an intermediate bone)
const FINGER_BONES := {
	"Thumb": ["ThumbMetacarpal", "ThumbProximal", "ThumbDistal"],
	"Index": ["IndexProximal", "IndexIntermediate", "IndexDistal"],
	"Middle": ["MiddleProximal", "MiddleIntermediate", "MiddleDistal"],
	"Ring": ["RingProximal", "RingIntermediate", "RingDistal"],
	"Little": ["LittleProximal", "LittleIntermediate", "LittleDistal"],
}
## curl in degrees per joint (towards the palm), proximal to distal
const FINGER_POSES := {
	"relaxed": {"Thumb": [6, 8, 5], "Index": [10, 15, 8], "Middle": [14, 18, 10], "Ring": [18, 20, 10], "Little": [22, 22, 12]},
	"open": {"Thumb": [0, 0, 0], "Index": [0, 0, 0], "Middle": [0, 0, 0], "Ring": [0, 0, 0], "Little": [0, 0, 0]},
	"fist": {"Thumb": [30, 30, 20], "Index": [80, 95, 65], "Middle": [85, 95, 65], "Ring": [85, 95, 65], "Little": [85, 95, 65]},
	"point": {"Thumb": [30, 30, 20], "Index": [0, 0, 0], "Middle": [85, 95, 65], "Ring": [85, 95, 65], "Little": [85, 95, 65]},
}
const BASE := {
	"shoulder": {"dir": [0.0, 0.0, 1.0]},
	"upper": {"dir": [0.0, -0.93, 0.37]},
	"lower": {"dir": [0.12, -0.95, 0.28]},
}
const BASE_FINGERS := "relaxed"
## share of the palm twist taken by the forearm (the rest turns at the wrist)
const FOREARM_TWIST := 0.35
## how fast the arms follow the target (1/s); higher = snappier
const FOLLOW_SPEED := 9.0

var library := {}
var library_order: Array[String] = []
var current := ""
## the documents (angles) of the gestures made in the editor, by name: the editor loads them back into its sliders
var pose_docs := {}

## the torso of the gesture as euler degrees (pitch + forward, yaw + to the left, roll + to the right); the expression engine puts it on
## the spine bones (with the breathing). The arm directions are in the character's frame, not relative to the torso ("forward" is always
## towards the viewer, a hanging arm hangs down): only the shoulders move with the torso.
var torso_euler := Vector3.ZERO

var _skeleton: Skeleton3D
var _bones := {}      # "R"/"L" -> {limb: index}
var _finger_bones := {}  # "R"/"L" -> {finger: [indices]}
var _dir := {}        # "R"/"L" -> {limb: Vector3}   shown values
var _palm := {}       # "R"/"L" -> {limb: Vector3}   (zero = no palm control)
var _curl := {}       # "R"/"L" -> {finger: Vector3}
var _time := 0.0
var _gesture: Dictionary = {}

func setup(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
	for side in ["R", "L"]:
		_bones[side] = {}
		_finger_bones[side] = {}
		_dir[side] = {}
		_palm[side] = {}
		_curl[side] = {}
		var prefix := "Right" if side == "R" else "Left"
		for limb in LIMBS:
			_bones[side][limb] = skeleton.find_bone(prefix + BONES[limb])
			_dir[side][limb] = _base_dir(limb)
			_palm[side][limb] = Vector3.ZERO
		for finger in FINGERS:
			var idx := []
			for b in FINGER_BONES[finger]:
				idx.append(skeleton.find_bone(prefix + b))
			_finger_bones[side][finger] = idx
			_curl[side][finger] = _pose_curl(BASE_FINGERS, finger)
	_apply()

func load_library(path: String) -> int:
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("gestures")) != TYPE_ARRAY:
		push_error("gesture library %s is not {\"gestures\": [...]}" % path)
		return 0
	library.clear()
	library_order.clear()
	for g in parsed["gestures"]:
		if typeof(g) == TYPE_DICTIONARY and typeof(g.get("name")) == TYPE_STRING and typeof(g.get("keys")) == TYPE_ARRAY:
			library[g["name"]] = g
			library_order.append(g["name"])
		else:
			push_warning("gesture without name/keys ignored")
	return library.size()

## The gestures made in the editor (their documents from the server): the ones that were set before are replaced.
func set_pose_gestures(docs: Array) -> void:
	for gesture_name in library_order.duplicate():
		if str(library[gesture_name].get("kind", "")) == "pose":
			library.erase(gesture_name)
			library_order.erase(gesture_name)
	pose_docs.clear()
	for doc in docs:
		if typeof(doc) == TYPE_DICTIONARY and typeof(doc.get("name")) == TYPE_STRING and not library.has(doc["name"]):
			library[doc["name"]] = PoseModel.gesture_from_pose(doc)
			library_order.append(doc["name"])
			pose_docs[doc["name"]] = doc
	library_changed.emit()

const PREVIEW := "_preview"
const TRY := "_try"

## Shows the final pose of a gesture document and keeps it (the editor calls it while a slider moves). No face, no sound, no end.
func preview(doc: Dictionary) -> void:
	var final := PoseModel.final_key(doc)
	var first := final.duplicate(true)
	first["t"] = 0.0
	var second := final.duplicate(true)
	second["t"] = 1.0e9
	_gesture = {"name": PREVIEW, "duration": 2.0e9, "keys": [first, second]}
	current = PREVIEW
	_time = 0.0

## Leaves the preview: the arms ease back to neutral.
func end_preview() -> void:
	if current == PREVIEW:
		_gesture = {}
		current = ""

## Puts arms, fingers and torso at once to the neutral pose (no easing).
func snap_to_base() -> void:
	for side in ["R", "L"]:
		for limb in LIMBS:
			_dir[side][limb] = _base_dir(limb)
			_palm[side][limb] = Vector3.ZERO
		for finger in FINGERS:
			_curl[side][finger] = _pose_curl(BASE_FINGERS, finger)
	torso_euler = Vector3.ZERO
	_apply()

## Plays a gesture document once from the neutral pose, like it will be played later (with its face).
func try_doc(doc: Dictionary) -> bool:
	if PoseModel.final_key(doc).is_empty():
		return false
	end_preview()
	_gesture = {}
	snap_to_base()
	library[TRY] = PoseModel.gesture_from_pose(doc)
	return play(TRY)

## Starts a gesture; unknown names keep the current one running.
func play(gesture_name: String) -> bool:
	if not library.has(gesture_name):
		push_warning("unknown gesture '%s'" % gesture_name)
		return false
	_gesture = library[gesture_name]
	current = gesture_name
	_time = 0.0
	gesture_started.emit(gesture_name)
	return true

## Returns the arms to the relaxed base pose right away (they ease back).
func stop() -> void:
	_finish()

func is_playing() -> bool:
	return not _gesture.is_empty()

func _process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	if not _gesture.is_empty():
		_time += delta
		if _time >= float(_gesture.get("duration", 2.0)):
			_finish()
	var k := 1.0 - exp(-FOLLOW_SPEED * delta) if delta > 0.0 else 1.0
	for side in ["R", "L"]:
		for limb in LIMBS:
			_dir[side][limb] = (_dir[side][limb] as Vector3).lerp(_target_dir(side, limb), k).normalized()
			_palm[side][limb] = (_palm[side][limb] as Vector3).lerp(_target_palm(side, limb), k)
		for finger in FINGERS:
			_curl[side][finger] = (_curl[side][finger] as Vector3).lerp(_target_curl(side, finger), k)
	torso_euler = torso_euler.lerp(_target_torso(), k)
	_apply()

## poses the arms and fingers again with the bones as they are now. The arm bones are set relative to their parents, so this is called
## after the torso moved (ExpressionEngine): the arm directions then never depend on which of the two engines runs first.
func reapply() -> void:
	_apply()

func _finish() -> void:
	if _gesture.is_empty():
		return
	var done := current
	_gesture = {}
	current = ""
	gesture_finished.emit(done)

# --- reading the data -------------------------------------------------------------------------

func _vec(a) -> Vector3:
	return Vector3(a[0], a[1], a[2])

func _base_dir(limb: String) -> Vector3:
	return _vec(BASE["lower" if limb == "hand" else limb]["dir"]).normalized()

func _pose_curl(pose: String, finger: String) -> Vector3:
	var c: Array = FINGER_POSES.get(pose, FINGER_POSES["relaxed"])[finger]
	return Vector3(c[0], c[1], c[2])

## the two keys around the current time and how far we are between them
func _span() -> Array:
	var prev: Dictionary = {}
	var next: Dictionary = {}
	for key in _gesture["keys"]:
		if float(key.get("t", 0.0)) <= _time:
			prev = key
		elif next.is_empty():
			next = key
	if prev.is_empty():
		prev = next
	if next.is_empty():
		next = prev
	var span := float(next.get("t", 0.0)) - float(prev.get("t", 0.0))
	var f := 0.0 if span <= 0.0 else clampf((_time - float(prev.get("t", 0.0))) / span, 0.0, 1.0)
	return [prev, next, f * f * (3.0 - 2.0 * f)]

# a limb entry is [f, u, o] or {"dir": [...], "palm": [...]}; "hand" falls back to "lower"
func _entry(key: Dictionary, side: String, limb: String):
	var arm: Dictionary = key.get(side, {})
	var e = arm.get(limb)
	if e == null and limb == "hand":
		e = arm.get("lower")
	return e

func _entry_dir(e, limb: String) -> Vector3:
	if e == null:
		return _base_dir(limb)
	return _vec(e["dir"] if typeof(e) == TYPE_DICTIONARY else e).normalized()

func _entry_palm(e) -> Vector3:
	if e != null and typeof(e) == TYPE_DICTIONARY and e.has("palm"):
		return _vec(e["palm"]).normalized()
	return Vector3.ZERO

func _target_dir(side: String, limb: String) -> Vector3:
	if _gesture.is_empty():
		return _base_dir(limb)
	var s := _span()
	return _entry_dir(_entry(s[0], side, limb), limb).lerp(_entry_dir(_entry(s[1], side, limb), limb), s[2]).normalized()

func _target_palm(side: String, limb: String) -> Vector3:
	if _gesture.is_empty() or limb == "shoulder" or limb == "upper":
		return Vector3.ZERO
	var s := _span()
	var a := _entry_palm(_entry(s[0], side, limb))
	var b := _entry_palm(_entry(s[1], side, limb))
	if a == Vector3.ZERO or b == Vector3.ZERO:
		return a if s[2] < 0.5 else b
	return a.lerp(b, s[2])

func _target_curl(side: String, finger: String) -> Vector3:
	if _gesture.is_empty():
		return _pose_curl(BASE_FINGERS, finger)
	var s := _span()
	var pa = (s[0].get(side, {}) as Dictionary).get("fingers", BASE_FINGERS)
	var pb = (s[1].get(side, {}) as Dictionary).get("fingers", BASE_FINGERS)
	return _curl_of(pa, finger).lerp(_curl_of(pb, finger), s[2])

## the curl of one finger for a finger spec: a pose name, or {"index": 0..100, ...} between open and fist (missing fingers stay relaxed)
func _curl_of(spec, finger: String) -> Vector3:
	if typeof(spec) == TYPE_DICTIONARY:
		var key := finger.to_lower()
		if spec.has(key):
			return _pose_curl("open", finger).lerp(_pose_curl("fist", finger), clampf(float(spec[key]) / 100.0, 0.0, 1.0))
		return _pose_curl(BASE_FINGERS, finger)
	return _pose_curl(str(spec), finger)

func _target_torso() -> Vector3:
	if _gesture.is_empty():
		return Vector3.ZERO
	var s := _span()
	return _key_torso(s[0]).lerp(_key_torso(s[1]), s[2])

func _key_torso(key: Dictionary) -> Vector3:
	var t = key.get("torso")
	if t == null:
		return Vector3.ZERO
	return Vector3(t[0], t[1], t[2])


# --- posing ---------------------------------------------------------------------------------------

func _apply() -> void:
	if _skeleton == null:
		return
	for side in ["R", "L"]:
		for limb in LIMBS:  # parents first, so every bone sees its parent's final pose
			var i: int = _bones[side][limb]
			if i >= 0:
				_pose_arm_bone(i, side, limb)
		for finger in FINGERS:
			_pose_finger(side, finger)

## model space vector from [forward, up, outward] (left arm = +X, right arm = -X in the T-pose)
func _to_model(v: Vector3, side: String) -> Vector3:
	var s := 1.0 if side == "L" else -1.0
	return Vector3(v.z * s, v.y, v.x)

func _pose_arm_bone(i: int, side: String, limb: String) -> void:
	var s := 1.0 if side == "L" else -1.0
	var rest_axis := Vector3(s, 0, 0)
	var d := _to_model(_dir[side][limb], side).normalized()
	if d.dot(rest_axis) < -0.999:  # exactly opposite: the shortest arc is undefined
		d = (d + Vector3(0, 0.01, 0)).normalized()
	var arc := Quaternion(rest_axis, d)
	var rot := Basis(arc)
	var palm: Vector3 = _palm[side][limb]
	if limb == "lower" or limb == "hand":
		if palm != Vector3.ZERO:
			var want := _to_model(palm, side)
			want = (want - d * want.dot(d))
			if want.length() > 0.05:
				var have := arc * Vector3(0, -1, 0)  # the palm faces down in the T-pose
				var twist := have.signed_angle_to(want.normalized(), d)
				rot = Basis(d, twist * (FOREARM_TWIST if limb == "lower" else 1.0)) * rot
	var rest_global := _skeleton.get_bone_global_rest(i).basis
	var parent_global := _skeleton.get_bone_global_pose(_skeleton.get_bone_parent(i)).basis
	var local := parent_global.inverse() * rot * rest_global
	_skeleton.set_bone_pose_rotation(i, local.get_rotation_quaternion())

## curls the joints of one finger about a fixed axis in the hand's rest frame
func _pose_finger(side: String, finger: String) -> void:
	var s := 1.0 if side == "L" else -1.0
	var curl: Vector3 = _curl[side][finger]
	var joints: Array = _finger_bones[side][finger]
	for j in joints.size():
		var i: int = joints[j]
		if i < 0:
			continue
		var parent_rest := _skeleton.get_bone_global_rest(_skeleton.get_bone_parent(i)).basis
		var bone_axis := _skeleton.get_bone_global_rest(i).basis.y
		var axis_model := bone_axis.cross(Vector3(0, -1, 0))  # flexion towards the palm side
		if axis_model.length() < 0.001:
			continue
		var axis_local := (parent_rest.inverse() * axis_model.normalized()).normalized()
		var rest_local := _skeleton.get_bone_rest(i).basis
		var local := Basis(axis_local, deg_to_rad(curl[j])) * rest_local
		_skeleton.set_bone_pose_rotation(i, local.get_rotation_quaternion())
