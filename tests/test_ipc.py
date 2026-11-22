import json
import time

import pytest

from slouchbuddy import ipc


def test_status_roundtrip(tmp_path):
    ipc.write_status({"score": 82, "state": "good"}, str(tmp_path))
    status = ipc.read_status(str(tmp_path))
    assert status["score"] == 82 and status["state"] == "good"


def test_missing_or_stale_status_is_none(tmp_path):
    assert ipc.read_status(str(tmp_path)) is None
    (tmp_path / "status.json").write_text(json.dumps({"score": 1, "updated": time.time() - 60}))
    assert ipc.read_status(str(tmp_path)) is None


def test_corrupt_status_is_none(tmp_path):
    (tmp_path / "status.json").write_text("{not json")
    assert ipc.read_status(str(tmp_path)) is None


def test_commands_are_delivered_once_in_order(tmp_path):
    ipc.send_command("show", str(tmp_path))
    ipc.send_command("calibrate", str(tmp_path))
    assert ipc.pop_commands(str(tmp_path)) == ["show", "calibrate"]
    assert ipc.pop_commands(str(tmp_path)) == []


def test_unknown_command_rejected_and_garbage_ignored(tmp_path):
    with pytest.raises(ValueError):
        ipc.send_command("rm -rf", str(tmp_path))
    (tmp_path / "control.txt").write_text("hide\nbogus\n")
    assert ipc.pop_commands(str(tmp_path)) == ["hide"]
