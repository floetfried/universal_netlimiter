#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import tempfile
import os
import stat
import re

MAX_DL_MBPS = 213
LIMIT_PCT = 75


class ToggleSwitch(ttk.Frame):
    def __init__(self, parent, command=None, width=80):
        super().__init__(parent, width=width, height=36)
        self.pack_propagate(False)
        self._cmd = command
        self._state = False
        self._width = width
        self._r = 14

        self._canvas = tk.Canvas(self, width=width, height=36, highlightthickness=0, bg=self._get_bg())
        self._canvas.pack()
        self._canvas.bind("<Button-1>", self._click)

        c = self._width // 2
        y = 18
        self._bg_rect = self._canvas.create_rectangle(2, y - self._r, self._width - 2, y + self._r,
                                                       fill="#555", outline="")
        self._knob = self._canvas.create_oval(4, y - self._r + 2, 4 + 2 * self._r - 4, y + self._r - 2,
                                              fill="#ddd", outline="")
        self._draw()

    def _get_bg(self):
        p = self
        while p:
            try:
                return p.cget("background")
            except:
                p = p.master
        return "#f0f0f0"

    def _draw(self):
        c = self._canvas
        if self._state:
            c.itemconfig(self._bg_rect, fill="#2ecc71")
            cx = self._width - self._r - 4
        else:
            c.itemconfig(self._bg_rect, fill="#555")
            cx = self._r + 4
        c.coords(self._knob, cx - self._r + 2, 18 - self._r + 2, cx + self._r - 2, 18 + self._r - 2)

    def _click(self, _):
        self.toggle()

    def toggle(self):
        self._state = not self._state
        self._draw()
        if self._cmd:
            self._cmd(self._state)

    def set(self, state):
        self._state = state
        self._draw()

    def get(self):
        return self._state


class App:
    BG = "#1e1e1e"
    CARD = "#2b2b2b"
    FG = "#dcdcdc"
    FG_MUTED = "#888"
    FG_DIM = "#666"
    GREEN = "#2ecc71"
    YELLOW = "#f39c12"
    RED = "#e74c3c"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Limiter")
        self.root.resizable(False, False)
        iface = self._detect_iface()
        self.iface = iface
        self.active = False
        self.limit_mbps = int(MAX_DL_MBPS * LIMIT_PCT / 100)

        self._setup_styles()
        self._setup_ui()
        self._center()

    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=self.BG)
        s.configure("card.TFrame", background=self.CARD, relief="flat")
        s.configure("stat.TLabel", background=self.CARD, foreground=self.FG_MUTED, font=("Segoe UI", 10))
        s.configure("value.TLabel", background=self.CARD, foreground=self.FG, font=("Segoe UI", 22, "bold"))
        s.configure("hint.TLabel", background=self.CARD, foreground=self.FG_DIM, font=("Segoe UI", 8))

    def _detect_iface(self):
        try:
            r = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                for iface in re.findall(r'dev\s+(\S+)', line):
                    if not re.search(r'^(tun|tap|wg|br|docker|veth)', iface):
                        return iface
        except:
            pass
        return "enp9s0"

    def _setup_ui(self):
        self.root.configure(bg=self.BG)
        outer = ttk.Frame(self.root, padding=20, style="card.TFrame")
        outer.pack()

        sub = ttk.Label(outer, text=f"Interface {self.iface}   ·   max {MAX_DL_MBPS} Mbit/s", style="stat.TLabel")
        sub.pack()

        self.toggle = ToggleSwitch(outer, command=self._on_toggle, width=72)
        self.toggle.pack(pady=(12, 5))

        pct = ttk.Label(outer, text=f"{LIMIT_PCT}% der maximalen Leitung", style="hint.TLabel")
        pct.pack(pady=(0, 4))

        self.status_frame = ttk.Frame(outer, style="card.TFrame")
        self.status_frame.pack(pady=(12, 0), fill="x")

        self.dot = tk.Canvas(self.status_frame, width=12, height=12, highlightthickness=0, bg=self.CARD)
        self.dot.pack(side="left", padx=(0, 6))
        self._dot = self.dot.create_oval(2, 2, 10, 10, fill=self.FG_DIM, outline="")

        self.status_label = ttk.Label(self.status_frame, text="Aus", style="stat.TLabel")
        self.status_label.pack(side="left")

        self.toggle.set(False)

    def _center(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"+{sw//2 - w//2}+{sh//2 - h//2}")

    def _on_toggle(self, state):
        if state:
            self._set_status("wird aktiviert …", self.YELLOW)
            threading.Thread(target=self._activate, daemon=True).start()
        else:
            self._set_status("wird deaktiviert …", self.YELLOW)
            threading.Thread(target=self._deactivate, daemon=True).start()

    def _set_status(self, text, color):
        self.dot.itemconfig(self._dot, fill=color)
        self.status_label.config(text=text)

    def _activate(self):
        limit_kbit = self.limit_mbps * 1000
        burst = max(256, int(limit_kbit * 0.05))

        script = f"""set -e
tc qdisc del dev {self.iface} ingress 2>/dev/null || true
tc qdisc add dev {self.iface} ingress
tc filter add dev {self.iface} parent ffff: protocol all prio 1 u32 match u32 0 0 police rate {limit_kbit}kbit burst {burst}kbit drop
"""
        ok, err = self._run_root(script)
        self.root.after(0, self._cb_activate, ok, err)

    def _cb_activate(self, ok, err):
        if ok:
            self.active = True
            self._set_status(f"Limitiert auf {self.limit_mbps} Mbit/s", self.GREEN)
        else:
            self.toggle.set(False)
            self._set_status("Fehler", self.RED)
            messagebox.showerror("Fehler", f"Konnte Limit nicht setzen:\n{err}")

    def _deactivate(self):
        script = f"""set -e
tc qdisc del dev {self.iface} ingress 2>/dev/null || true
"""
        ok, err = self._run_root(script)
        self.root.after(0, self._cb_deactivate, ok, err)

    def _cb_deactivate(self, ok, err):
        if ok:
            self.active = False
            self._set_status("Aus", self.FG_DIM)
        else:
            self.toggle.set(True)
            self._set_status("Fehler", self.RED)
            messagebox.showerror("Fehler", f"Konnte Limit nicht entfernen:\n{err}")

    def _make_askpass(self):
        content = """#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog
r = tk.Tk()
r.withdraw()
pw = simpledialog.askstring("Passwort", "Root-Passwort für Limiter:", show="*")
if pw: print(pw, end="")
r.destroy()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            p = f.name
        os.chmod(p, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        return p

    def _run_root(self, script):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write("export PATH=/sbin:/usr/sbin:/usr/local/sbin:$PATH\n")
            f.write("exec 2>&1\n")
            f.write(script)
            mp = f.name
        os.chmod(mp, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        ap = self._make_askpass()
        try:
            env = os.environ.copy()
            env["SUDO_ASKPASS"] = ap
            proc = subprocess.run(["sudo", "-A", "--", mp], capture_output=True, text=True, timeout=60, env=env)
            return proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip()
        except Exception as e:
            return False, str(e)
        finally:
            for p in (mp, ap):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
