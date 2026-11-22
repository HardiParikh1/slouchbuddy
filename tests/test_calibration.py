import json

from calibration import load_calibration, save_calibration


def test_load_returns_none_when_missing(tmp_path):
    assert load_calibration(str(tmp_path / "nope.json")) is None


def test_roundtrip(tmp_path):
    path = str(tmp_path / "nested" / "cal.json")
    data = {"shoulder_imbalance": 0.01, "head_tilt_angle": -3.5}
    save_calibration(data, path)
    assert load_calibration(path) == data


def test_save_overwrites(tmp_path):
    path = str(tmp_path / "cal.json")
    save_calibration({"a": 1}, path)
    save_calibration({"a": 2}, path)
    with open(path) as f:
        assert json.load(f) == {"a": 2}
