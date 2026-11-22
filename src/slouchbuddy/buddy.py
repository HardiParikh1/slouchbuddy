"""The desk buddy: a koala that sits in the top-right corner of your screen and reacts to
your posture.

    slouchbuddy buddy

Drag it anywhere; right-click for the menu. Needs the background monitor, which it
starts itself unless one is already running (e.g. from the macOS menu bar app).
"""
import argparse
import time
import tkinter as tk
import webbrowser

from PIL import Image, ImageTk

from slouchbuddy import buddy_brain as brain_mod
from slouchbuddy import ipc, koala, launcher
from slouchbuddy.buddy_brain import BuddyBrain

KOALA_SIZE = 170
WIDTH = 230
KOALA_HEIGHT = KOALA_SIZE + 16  # card height with just the koala
BUBBLE_HEIGHT = 84
CARD = (253, 246, 236)  # warm off-white card behind the koala
CARD_HEX = "#fdf6ec"
POLL_MS = 500
FRAME_MS = 110  # ~9 fps is smooth enough and keeps CPU use low
MESSAGE_SECONDS = 9
TOP_MARGIN = 34  # clear the macOS menu bar
RIGHT_MARGIN = 16
INK = "#353b44"


def window_position(screen_w, width=WIDTH):
    """Top-right corner of the screen."""
    return screen_w - width - RIGHT_MARGIN, TOP_MARGIN


class BuddyWindow:
    def __init__(self, own_monitor):
        self.root = tk.Tk()
        self.root.title("Slouchbuddy")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        x, y = window_position(self.root.winfo_screenwidth())
        self.height = KOALA_HEIGHT
        self.root.geometry(f"{WIDTH}x{self.height}+{x}+{y}")
        self.root.config(bg=CARD_HEX)

        # A solid card (no transparency tricks) so it renders the same on every OS.
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=BUBBLE_HEIGHT + KOALA_HEIGHT,
                                bg=CARD_HEX, highlightthickness=2, highlightbackground=INK)
        self.canvas.pack(fill="both", expand=True)

        self.brain = BuddyBrain()
        self.mood = brain_mod.SLEEPING
        self.message = None
        self.message_until = 0
        self.status = None
        self.monitor = launcher.spawn_monitor() if own_monitor and ipc.read_status() is None else None
        self.dashboard = None
        self._photo = None
        self._drag = (0, 0)

        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        for right_click in ("<Button-2>", "<Button-3>", "<Control-Button-1>"):
            self.canvas.bind(right_click, self._show_menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Calibrate (sit upright first)", command=lambda: ipc.send_command("calibrate"))
        self.menu.add_command(label="I took a break", command=lambda: ipc.send_command("break"))
        self.pause_index = self.menu.index("end") + 1
        self.menu.add_command(label="Pause monitoring", command=self._toggle_pause)
        self.menu.add_command(label="Show / hide camera view", command=lambda: ipc.send_command("toggle"))
        self.menu.add_separator()
        self.menu.add_command(label="Open dashboard", command=self._open_dashboard)
        self.menu.add_separator()
        self.menu.add_command(label="Quit buddy", command=self.quit)

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self._poll()
        self._animate()

    # --- window plumbing -------------------------------------------------
    def _start_drag(self, event):
        self._drag = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_move(self, event):
        self.root.geometry(f"+{event.x_root - self._drag[0]}+{event.y_root - self._drag[1]}")

    def _show_menu(self, event):
        paused = bool(self.status and self.status.get("state") == "paused")
        self.menu.entryconfig(self.pause_index, label="Resume monitoring" if paused else "Pause monitoring")
        self.menu.tk_popup(event.x_root, event.y_root)

    def _toggle_pause(self):
        paused = bool(self.status and self.status.get("state") == "paused")
        ipc.send_command("resume" if paused else "pause")

    def _open_dashboard(self):
        if self.dashboard is None or self.dashboard.poll() is not None:
            self.dashboard = launcher.spawn_dashboard()
        webbrowser.open(f"http://localhost:{launcher.DASHBOARD_PORT}")

    def quit(self):
        if self.monitor is not None and self.monitor.poll() is None:
            ipc.send_command("quit")
            try:
                self.monitor.wait(timeout=3)
            except Exception:
                self.monitor.terminate()
        if self.dashboard is not None and self.dashboard.poll() is None:
            self.dashboard.terminate()
        self.root.destroy()

    # --- behaviour -------------------------------------------------------
    def _poll(self):
        self.status = ipc.read_status()
        view = self.brain.update(self.status)
        self.mood = view.mood
        if view.message:
            self.message = view.message
            self.message_until = time.time() + MESSAGE_SECONDS
        self.root.after(POLL_MS, self._poll)

    def _animate(self):
        self._draw(time.time())
        self.root.after(FRAME_MS, self._animate)

    # --- drawing ---------------------------------------------------------
    def _draw(self, t):
        img = koala.render(self.mood, t=t, size=KOALA_SIZE, supersample=2)
        card = Image.new("RGB", img.size, CARD)
        card.paste(img, mask=img.getchannel("A"))
        self._photo = ImageTk.PhotoImage(card)  # keep a reference or Tk garbage-collects it

        showing = bool(self.message and time.time() < self.message_until)
        wanted = KOALA_HEIGHT + (BUBBLE_HEIGHT if showing else 0)
        if wanted != self.height:  # grow/shrink the card downward so the koala stays put
            self.height = wanted
            self.root.geometry(f"{WIDTH}x{wanted}")

        c = self.canvas
        c.delete("all")
        c.create_image(WIDTH // 2, 8, image=self._photo, anchor="n")
        if showing:
            c.create_text(WIDTH // 2, KOALA_HEIGHT + BUBBLE_HEIGHT // 2 - 4, text=self.message,
                          width=WIDTH - 36, fill=INK, font=("Helvetica", 12), justify="center")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Slouchbuddy desk buddy")
    parser.add_argument("--no-monitor", action="store_true", help="don't start the background monitor")
    args = parser.parse_args(argv)
    BuddyWindow(own_monitor=not args.no_monitor).root.mainloop()


if __name__ == "__main__":
    main()
