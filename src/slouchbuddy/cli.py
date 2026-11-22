"""`slouchbuddy` command line entry point."""
import argparse
import subprocess
import sys

from slouchbuddy import __version__


def _default_command():
    # macOS gets the menu bar app; everywhere else the desktop buddy is the front end.
    return "menubar" if sys.platform == "darwin" else "buddy"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="slouchbuddy",
        description="Real-time posture monitoring with your webcam.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("run", help="open the live camera window (press C to calibrate, Q to quit)")
    sub.add_parser("buddy", help="Windows/Linux: koala companion window (on macOS the koala lives in the menu bar)")
    sub.add_parser("menubar", help="macOS: monitor in the background from the menu bar (default on macOS)")

    dash = sub.add_parser("dashboard", help="open the analytics dashboard in your browser")
    dash.add_argument("--port", type=int, default=8501)

    login = sub.add_parser("install-login", help="start automatically at every login")
    login.add_argument("--camera", type=int, default=None, help="camera index to use (default 0)")
    sound = sub.add_parser("test-sound", help="play the alert sound so you can hear it")
    sound.add_argument("name", nargs="?", help='chime, beep, off, or a macOS sound like Glass, Pop, Ping')
    sub.add_parser("uninstall-login", help="remove the login item")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    command = args.command or _default_command()

    # Imports are lazy so e.g. `dashboard` doesn't need OpenCV/MediaPipe loaded.
    if command == "run":
        from slouchbuddy.app import main as run_monitor

        run_monitor()
    elif command == "buddy":
        from slouchbuddy.buddy import main as run_buddy

        run_buddy([])
    elif command == "menubar":
        if sys.platform != "darwin":
            raise SystemExit("The menu bar app is macOS-only. Use `slouchbuddy run` instead.")
        from slouchbuddy.menubar import main as run_menubar

        run_menubar()
    elif command == "dashboard":
        import os

        from slouchbuddy import dashboard

        subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run", os.path.abspath(dashboard.__file__),
                "--server.port", str(args.port), "--client.toolbarMode", "minimal",
                "--theme.primaryColor", "#5b9a76",
            ],
            check=False,
        )
    elif command == "install-login":
        from slouchbuddy import launch_agent

        launch_agent.install(camera_index=args.camera)
    elif command == "test-sound":
        import time

        from slouchbuddy.notifications import play_alert_sound

        play_alert_sound(args.name)
        time.sleep(1.5)  # let it finish before the process exits
    elif command == "uninstall-login":
        from slouchbuddy import launch_agent

        launch_agent.uninstall()


if __name__ == "__main__":
    main()
