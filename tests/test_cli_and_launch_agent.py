import plistlib
import sys

import pytest

from slouchbuddy import __version__, cli, launch_agent


def test_parser_knows_all_commands():
    parser = cli.build_parser()
    for cmd in ("run", "buddy", "menubar", "dashboard", "install-login", "uninstall-login"):
        assert parser.parse_args([cmd]).command == cmd


def test_version_flag(capsys):
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["--version"])
    assert __version__ in capsys.readouterr().out


def test_default_command_depends_on_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert cli._default_command() == "menubar"
    monkeypatch.setattr(sys, "platform", "linux")
    assert cli._default_command() == "buddy"
    monkeypatch.setattr(sys, "platform", "win32")
    assert cli._default_command() == "buddy"


def test_launch_agent_plist_is_valid_and_runs_menubar():
    data = plistlib.loads(plistlib.dumps(launch_agent.build_plist(python="/py", camera_index=1)))
    assert data["ProgramArguments"] == ["/py", "-m", "slouchbuddy.menubar"]
    assert data["EnvironmentVariables"] == {"CAMERA_INDEX": "1"}
    assert data["RunAtLoad"] is True


def test_data_root_override(monkeypatch, tmp_path):
    from slouchbuddy import config

    monkeypatch.setenv("SLOUCHBUDDY_HOME", str(tmp_path))
    assert config._find_data_root() == str(tmp_path)


def test_login_module_per_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert launch_agent.login_module() == "slouchbuddy.menubar"
    monkeypatch.setattr(sys, "platform", "win32")
    assert launch_agent.login_module() == "slouchbuddy.buddy"


def test_windows_command_uses_buddy_and_quotes_path(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    cmd = launch_agent.windows_command(python=r"C:\Program Files\Python\python.exe")
    assert cmd.startswith('"') and cmd.endswith("-m slouchbuddy.buddy")


def test_linux_desktop_entry(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    entry = launch_agent.build_desktop_entry(python="/usr/bin/python3")
    assert "Exec=/usr/bin/python3 -m slouchbuddy.buddy" in entry
    assert entry.startswith("[Desktop Entry]")
