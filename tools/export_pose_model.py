"""
Writes the slider definition of the gesture editor (pose_model.py) as ui/godot/presets/pose_model.json, the copy the character loads (it works
offline, the server serves the same numbers at /api/pose-model). Run it after changing pose_model.py; tests/test_gestures_api.py fails when the
file is out of date.

  python tools/export_pose_model.py
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
import pose_model  # noqa: E402

TARGET = os.path.join(REPO, "ui", "godot", "presets", "pose_model.json")


def main():
    with open(TARGET, "w", encoding="utf-8") as fp:
        json.dump(pose_model.describe(), fp, indent=1, ensure_ascii=False)
        fp.write("\n")
    print("written", TARGET)


if __name__ == "__main__":
    main()
