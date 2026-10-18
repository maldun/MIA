#!/usr/bin/env python
# -*- coding: utf-8 -*-
#MIA - MIA Is not an Assistant
#Copyright (C) 2017  Stefan Reiterer

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
The pose of arms, hands and torso as a few angles: what the sliders of the gesture editor set (and what the language model will fill in).

A gesture made of angles is only its FINAL pose plus timing; the character moves from the neutral pose (the arms hanging relaxed) to that pose
in `reach` seconds, holds it for `hold` seconds and eases back (ui/README.md). Every angle that is not set is neutral, so a pose lists only
what changes. The same numbers describe the right and the left arm (the left one is the mirror image).

  arm (R and L)   upper_raise      0 = hanging down ... 90 = sideways/forward level ... 180 = straight up
                  upper_direction  where the lifted arm points: 0 = sideways (away from the body), 90 = forward, 180 = across the body, -90 = backward
                  elbow_bend       0 = straight ... 150 = hand at the shoulder
                  elbow_turn       the direction the forearm swings: 0 = forward, 90 = inward (across), -90 = outward, 180 = backward
                  hand_turn        turns the palm around the forearm: 0 = the palm faces the body, 90 = forward, -90 = backward, 180 = away from the body
                  wrist            bends the hand: positive towards the palm, negative towards the back of the hand
                  fingers          a name (relaxed, open, fist, point) or {"thumb", "index", "middle", "ring", "little"} from 0 (open) to 100 (closed)
  torso           torso_lean       positive = forward, negative = backward
                  torso_side       positive = to the character's left, negative = right
                  torso_turn       positive = to the character's left, negative = right

The conversion of these angles into bone rotations is done by the character (ui/godot/pose_model.gd); this module defines the numbers, their
ranges and descriptions, and checks them (clamping like the presets do).
"""

SIDES = ("R", "L")
FINGER_NAMES = ("relaxed", "open", "fist", "point")
FINGER_KEYS = ("thumb", "index", "middle", "ring", "little")

# name -> (group, label, minimum, maximum, neutral, description). The neutral values reproduce the relaxed pose of the character (BASE in gesture_engine.gd).
ARM_PARAMS = {
    "upper_raise": ("arm", "Raise arm", 0.0, 180.0, 22.0, "how far the upper arm is lifted away from the body: 0 hanging, 90 level, 180 straight up"),
    "upper_direction": ("arm", "Arm direction", -120.0, 180.0, 0.0,
                        "where the lifted arm points: 0 sideways, 90 forward, 180 across the body, -90 backward"),
    "elbow_bend": ("arm", "Elbow bend", 0.0, 150.0, 9.0, "0 straight arm, 150 hand at the shoulder"),
    "elbow_turn": ("arm", "Elbow direction", -180.0, 180.0, -37.0,
                   "the direction the forearm swings when the elbow bends: 0 forward, 90 inward, -90 outward, 180 backward"),
    "hand_turn": ("hand", "Palm turn", -180.0, 180.0, 0.0, "turns the palm around the forearm: 0 towards the body, 90 forward, -90 backward, 180 away from the body"),
    "wrist": ("hand", "Wrist", -70.0, 70.0, 0.0, "bends the hand: positive towards the palm, negative towards the back of the hand"),
}
TORSO_PARAMS = {
    "torso_lean": ("torso", "Lean", -30.0, 30.0, 0.0, "positive leans forward, negative backward"),
    "torso_side": ("torso", "Tilt sideways", -25.0, 25.0, 0.0, "positive to the character's left, negative to the right"),
    "torso_turn": ("torso", "Turn", -40.0, 40.0, 0.0, "positive turns to the character's left, negative to the right"),
}
TIMING = {
    "reach": (0.2, 3.0, 0.6, "seconds from the neutral pose to the final pose"),
    "hold": (0.0, 8.0, 1.5, "seconds the final pose is held before the arms ease back"),
}
MAX_DESCRIPTION = 300


def describe():
    """everything the editor needs to build its sliders (and the model prompt to explain them)"""
    def entry(name, spec):
        group, label, low, high, neutral, text = spec
        return {"name": name, "group": group, "label": label, "min": low, "max": high, "neutral": neutral, "description": text}
    return {
        "sides": list(SIDES),
        "arm": [entry(n, s) for n, s in ARM_PARAMS.items()],
        "torso": [entry(n, s) for n, s in TORSO_PARAMS.items()],
        "fingers": {"names": list(FINGER_NAMES), "keys": list(FINGER_KEYS), "min": 0, "max": 100, "neutral": "relaxed"},
        "timing": {n: {"min": lo, "max": hi, "default": default, "description": text} for n, (lo, hi, default, text) in TIMING.items()},
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _clamped(name, value, low, high, corrections, prefix=""):
    clamped = min(high, max(low, float(value)))
    if clamped != float(value):
        corrections.append(f"{prefix}{name} clamped from {value} to {clamped:g}")
    return round(clamped, 2)


def normalize_fingers(raw, corrections, prefix=""):
    """a finger name, or an object of curls 0..100 (unknown keys and values removed, the rest clamped); None if nothing usable is left"""
    if isinstance(raw, str):
        if raw in FINGER_NAMES:
            return raw
        corrections.append(f"{prefix}unknown finger pose '{raw}' removed")
        return None
    if isinstance(raw, dict):
        fingers = {}
        for key, value in raw.items():
            if key not in FINGER_KEYS:
                corrections.append(f"{prefix}unknown finger '{key}' removed")
            elif not _is_number(value):
                corrections.append(f"{prefix}finger '{key}' is not a number, removed")
            else:
                fingers[key] = _clamped(key, value, 0.0, 100.0, corrections, prefix)
        return fingers or None
    corrections.append(f"{prefix}fingers must be a name or an object, removed")
    return None


def normalize_pose(raw):
    """
    The pose of a gesture: {"R": {...}, "L": {...}, "torso": {...}}, only the values that were given (the rest is neutral), unknown names removed
    and numbers clamped. Returns (pose, corrections). An unusable value is dropped with a message, never an exception.
    """
    corrections = []
    pose = {}
    if not isinstance(raw, dict):
        return {}, ["the pose must be an object"]
    for side in SIDES:
        if side not in raw:
            continue
        data = raw[side]
        if not isinstance(data, dict):
            corrections.append(f"{side} is not an object, removed")
            continue
        arm = {}
        for key, value in data.items():
            if key == "fingers":
                fingers = normalize_fingers(value, corrections, f"{side}.")
                if fingers is not None:
                    arm["fingers"] = fingers
            elif key in ARM_PARAMS:
                if _is_number(value):
                    _, _, low, high, _, _ = ARM_PARAMS[key]
                    arm[key] = _clamped(key, value, low, high, corrections, f"{side}.")
                else:
                    corrections.append(f"{side}.{key} is not a number, removed")
            else:
                corrections.append(f"unknown setting '{side}.{key}' removed")
        if arm:
            pose[side] = arm
    torso_raw = raw.get("torso")
    if torso_raw is not None:
        if not isinstance(torso_raw, dict):
            corrections.append("torso is not an object, removed")
        else:
            torso = {}
            for key, value in torso_raw.items():
                if key in TORSO_PARAMS and _is_number(value):
                    _, _, low, high, _, _ = TORSO_PARAMS[key]
                    torso[key] = _clamped(key, value, low, high, corrections, "torso.")
                else:
                    corrections.append(f"unknown or invalid setting 'torso.{key}' removed")
            if torso:
                pose["torso"] = torso
    for key in raw:
        if key not in SIDES and key != "torso":
            corrections.append(f"unknown part '{key}' removed")
    return pose, corrections


def normalize_timing(raw):
    """(reach, hold, corrections) with the defaults for what is missing"""
    corrections = []
    values = {}
    for name, (low, high, default, _) in TIMING.items():
        value = raw.get(name, default) if isinstance(raw, dict) else default
        if not _is_number(value):
            corrections.append(f"{name} is not a number, set to {default:g}")
            value = default
        values[name] = _clamped(name, value, low, high, corrections)
    return values["reach"], values["hold"], corrections
