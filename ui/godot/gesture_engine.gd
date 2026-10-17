class_name GestureEngine
extends Node
## Arm poses and gestures (ui/REQUIREMENTS.md 4.4a). Without a gesture the arms hang relaxed (BASE).
##
## Arm bones are posed with absolute angles relative to the T-pose of the model, in degrees:
##   [elev, swing, twist]   per limb: "shoulder", "upper", "lower", "hand"
##   elev  : 0 = straight out to the side, +90 = straight up, -90 = straight down, beyond +-90 leans inwards
##   swing : turns the limb forward (+) / backward (-) around the vertical axis (after elev)
##   twist : rotation around the limb's own axis
## Both sides use the same sign convention ("R" is the character's right arm).
## A missing limb keeps the base pose; "hand" follows "lower" if not given.
##
## Gesture: {"name", "description", "duration", "keys": [{"t": seconds, "R": {limb: [e, s, t]}, "L": {...}}]}
## Between keys the angles are interpolated; after "duration" the arms return to BASE.

signal gesture_started(gesture_name: String)
signal gesture_finished(gesture_name: String)

const LIMBS := ["shoulder", "upper", "lower", "hand"]
const BONES := {"shoulder": "Shoulder", "upper": "UpperArm", "lower": "LowerArm", "hand": "Hand"}
const BASE := {
	"shoulder": [0.0, 0.0, 0.0],
	"upper": [-68.0, 0.0, 0.0],
	"lower": [-72.0, 12.0, 0.0],
}
## how fast the arms follow the target (1/s); higher = snappier
const FOLLOW_SPEED := 9.0

var library := {}
var library_order: Array[String] = []
var current := ""

var _skeleton: Skeleton3D
var _bones := {}      # "R" / "L" -> {limb: bone index}
var _shown := {}      # "R" / "L" -> {limb: Vector3(elev, swing, twist)}
var _time := 0.0
var _gesture: Dictionary = {}

func setup(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
	for side in ["R", "L"]:
		_bones[side] = {}
		_shown[side] = {}
		var prefix := "Right" if side == "R" else "Left"
		for limb in LIMBS:
			_bones[side][limb] = skeleton.find_bone(prefix + BONES[limb])
			_shown[side][limb] = _base(limb)
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

## Returns the arms to the relaxed base pose.
func stop() -> void:
	_finish()

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
			_shown[side][limb] = (_shown[side][limb] as Vector3).lerp(_target(side, limb), k)
	_apply()

func _finish() -> void:
	if _gesture.is_empty():
		return
	var done := current
	_gesture = {}
	current = ""
	gesture_finished.emit(done)

func _base(limb: String) -> Vector3:
	var b: Array = BASE.get(limb, BASE["lower"])
	return Vector3(b[0], b[1], b[2])

## the angles the arms should have right now
func _target(side: String, limb: String) -> Vector3:
	if _gesture.is_empty():
		return _base_with_hand(limb, side)
	var keys: Array = _gesture["keys"]
	var prev: Dictionary = {}
	var next: Dictionary = {}
	for key in keys:
		if float(key.get("t", 0.0)) <= _time:
			prev = key
		elif next.is_empty():
			next = key
	if prev.is_empty():
		prev = next
	if next.is_empty():
		next = prev
	var a := _key_value(prev, side, limb)
	var b := _key_value(next, side, limb)
	var span := float(next.get("t", 0.0)) - float(prev.get("t", 0.0))
	var f := 0.0 if span <= 0.0 else clampf((_time - float(prev.get("t", 0.0))) / span, 0.0, 1.0)
	f = f * f * (3.0 - 2.0 * f)
	return a.lerp(b, f)

func _key_value(key: Dictionary, side: String, limb: String) -> Vector3:
	var arm: Dictionary = key.get(side, {})
	var src = arm.get(limb)
	if src == null and limb == "hand":
		src = arm.get("lower")  # the hand follows the forearm
	if src == null:
		return _base_with_hand(limb, side)
	return Vector3(src[0], src[1], src[2])

func _base_with_hand(limb: String, _side: String) -> Vector3:
	return _base("lower" if limb == "hand" else limb)

# --- posing ------------------------------------------------------------------------------

func _apply() -> void:
	if _skeleton == null:
		return
	for side in ["R", "L"]:
		for limb in LIMBS:  # parents first, so every bone sees its parent's final pose
			var i: int = _bones[side][limb]
			if i >= 0:
				_pose_bone(i, side, _shown[side][limb])

func _pose_bone(i: int, side: String, a: Vector3) -> void:
	# left arm points to +X and right arm to -X in the T-pose
	var s := 1.0 if side == "L" else -1.0
	var r := Basis(Vector3.UP, deg_to_rad(-s * a.y)) * Basis(Vector3.BACK, deg_to_rad(s * a.x)) \
			* Basis(Vector3.RIGHT, deg_to_rad(s * a.z))
	var rest_global := _skeleton.get_bone_global_rest(i).basis
	var parent_global := _skeleton.get_bone_global_pose(_skeleton.get_bone_parent(i)).basis
	var local := parent_global.inverse() * r * rest_global
	_skeleton.set_bone_pose_rotation(i, local.get_rotation_quaternion())
