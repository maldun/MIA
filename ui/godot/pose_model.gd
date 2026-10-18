class_name PoseModel
extends RefCounted
## Angles -> arm poses. A gesture made in the gesture editor is only its FINAL pose as a few angles (see pose_model.py, which defines the
## ranges and checks the numbers): this class turns them into the directions the gesture engine plays. The character moves from the
## neutral pose to that pose in "reach" seconds, holds it for "hold" seconds and eases back.
##
## Directions are [forward, up, outward] in the character's view (forward = towards the viewer); the same numbers work for both arms.
##   upper arm:  upper_raise (0 hanging ... 90 level ... 180 up) and upper_direction (0 sideways, 90 forward, 180 across, -90 backward)
##   forearm:    elbow_bend (0 straight ... 150) and elbow_turn (0 swings forward, 90 inward, -90 outward, 180 backward)
##   palm:       hand_turn (0 towards the body, 90 forward, -90 backward, 180 away); wrist bends the hand (+ towards the palm)
##   torso:      torso_lean (+ forward), torso_side (+ to the character's left), torso_turn (+ to the character's left)
## Not given = neutral (NEUTRAL reproduces the relaxed arm of GestureEngine.BASE).

const NEUTRAL := {"upper_raise": 22.0, "upper_direction": 0.0, "elbow_bend": 9.0, "elbow_turn": 37.0, "hand_turn": 0.0, "wrist": 0.0}
const FORWARD := Vector3(1, 0, 0)
const UP := Vector3(0, 1, 0)
const INWARD := Vector3(0, 0, -1)

static func value(params: Dictionary, name: String) -> float:
	return float(params.get(name, NEUTRAL[name]))

static func vec(v: Vector3) -> Array:
	return [snappedf(v.x, 0.0001), snappedf(v.y, 0.0001), snappedf(v.z, 0.0001)]

## direction of the upper arm from the angle away from "hanging down" and the direction of the lift
static func upper_direction(raise_deg: float, direction_deg: float) -> Vector3:
	var el := deg_to_rad(raise_deg)
	var az := deg_to_rad(direction_deg)
	return Vector3(sin(el) * sin(az), -cos(el), sin(el) * cos(az)).normalized()

## the part of `reference` that is perpendicular to `axis` (`fallback` when they are parallel)
static func _perpendicular(reference: Vector3, axis: Vector3, fallback: Vector3) -> Vector3:
	var p := reference - axis * reference.dot(axis)
	if p.length() < 0.05:
		p = fallback - axis * fallback.dot(axis)
	return p.normalized()

## the forearm swings away from the upper arm by `bend`, towards the direction `turn` around the upper arm (0 = forward, 90 = inward)
static func forearm_direction(upper: Vector3, bend_deg: float, turn_deg: float) -> Vector3:
	var r := _perpendicular(FORWARD, upper, UP)
	var s := r.cross(upper)
	var b := deg_to_rad(bend_deg)
	var t := deg_to_rad(turn_deg)
	return (upper * cos(b) + (r * cos(t) + s * sin(t)) * sin(b)).normalized()

## where the palm faces: 0 = towards the body, turned around the forearm by `turn` (90 = forward)
static func palm_direction(forearm: Vector3, turn_deg: float) -> Vector3:
	var n0 := _perpendicular(INWARD, forearm, FORWARD)
	var t := deg_to_rad(turn_deg)
	return (n0 * cos(t) + forearm.cross(n0) * sin(t)).normalized()

## the gesture engine's entry for one arm from its angles (missing angles are neutral)
static func arm_entry(params: Dictionary) -> Dictionary:
	var up := upper_direction(value(params, "upper_raise"), value(params, "upper_direction"))
	var lo := forearm_direction(up, value(params, "elbow_bend"), value(params, "elbow_turn"))
	var palm := palm_direction(lo, value(params, "hand_turn"))
	var entry := {"upper": vec(up), "lower": {"dir": vec(lo), "palm": vec(palm)}, "fingers": params.get("fingers", "relaxed")}
	var wrist := deg_to_rad(value(params, "wrist"))
	if absf(wrist) > 0.001:
		entry["hand"] = {"dir": vec((lo * cos(wrist) + palm * sin(wrist)).normalized()),
				"palm": vec((palm * cos(wrist) - lo * sin(wrist)).normalized())}
	return entry

## torso angles of the pose as euler degrees in the engine's convention: pitch (+ forward), yaw (+ to the left), roll (+ to the right)
static func torso_euler(torso: Dictionary) -> Vector3:
	return Vector3(float(torso.get("torso_lean", 0.0)), float(torso.get("torso_turn", 0.0)), -float(torso.get("torso_side", 0.0)))

## the final pose of a gesture document as one key of the gesture engine (without a time)
static func final_key(doc: Dictionary) -> Dictionary:
	var pose: Dictionary = doc.get("pose", {})
	var final := {}
	for side in ["R", "L"]:
		if pose.has(side):
			final[side] = arm_entry(pose[side])
	if pose.has("torso"):
		var e := torso_euler(pose["torso"])
		final["torso"] = [e.x, e.y, e.z]
	return final

## A gesture made of angles ({"name", "pose": {"R", "L", "torso"}, "reach", "hold", "expression", "description"}) as the gesture engine
## plays it: the first key is the neutral pose (nothing set), the second the final pose after `reach`, held until reach + hold.
static func gesture_from_pose(doc: Dictionary) -> Dictionary:
	var reach := clampf(float(doc.get("reach", 0.6)), 0.05, 10.0)
	var hold := clampf(float(doc.get("hold", 1.5)), 0.0, 20.0)
	var final := final_key(doc)
	var first := {"t": 0.0}
	var second := final.duplicate(true)
	second["t"] = reach
	var third := final.duplicate(true)
	third["t"] = reach + hold
	var gesture := {"name": str(doc.get("name", "")), "description": str(doc.get("description", "")), "duration": reach + hold,
			"kind": "pose", "keys": [first, second, third]}
	if str(doc.get("expression", "")) != "":
		gesture["expression"] = str(doc["expression"])
	return gesture
