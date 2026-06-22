#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import tempfile
import os
import stat
import re
import time
import speedtest

BG = "#1e1e1e"
CARD = "#2b2b2b"
FG = "#dcdcdc"
FG2 = "#888"
FG3 = "#666"
GREEN = "#2ecc71"
YELLOW = "#f39c12"
RED = "#e74c3c"
BLUE = "#3daee9"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(SCRIPT_DIR, "limiter_icon.png")
IFACE_ICON = os.path.join(SCRIPT_DIR, "iface_icon.png")
DL_ICON = os.path.join(SCRIPT_DIR, "dl_icon.png")
UL_ICON = os.path.join(SCRIPT_DIR, "ul_icon.png")


def _create_icon():
    if os.path.exists(ICON_PATH):
        return ICON_PATH
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, 61, 61], fill="#2b2b2b", outline=BLUE, width=3)
        d.rectangle([28, 16, 35, 38], fill=GREEN)
        d.polygon([(20, 36), (43, 36), (32, 50)], fill=GREEN)
        d.rectangle([14, 12, 49, 17], fill=RED)
        img.save(ICON_PATH)
    except Exception:
        pass
    return ICON_PATH


def _create_small_icons():
    if all(os.path.exists(p) for p in (IFACE_ICON, DL_ICON, UL_ICON)):
        return
    try:
        from PIL import Image, ImageDraw
        sz = 16
        def save(path, draw_fn):
            img = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
            draw_fn(ImageDraw.Draw(img))
            img.save(path)

        save(IFACE_ICON, lambda d: (
            d.rectangle([2, 4, 6, 12], fill=BLUE, outline="#55b5f0"),
            d.rectangle([8, 4, 12, 12], fill=BLUE, outline="#55b5f0"),
            d.rectangle([6, 6, 8, 10], fill=BLUE),
        ))
        save(DL_ICON, lambda d: (
            d.rectangle([6, 2, 10, 10], fill=GREEN),
            d.polygon([(2, 9), (14, 9), (8, 15)], fill=GREEN),
        ))
        save(UL_ICON, lambda d: (
            d.rectangle([6, 6, 10, 14], fill=YELLOW),
            d.polygon([(2, 7), (14, 7), (8, 1)], fill=YELLOW),
        ))
    except Exception:
        pass


try:
    import gi
    gi.require_version("AppIndicator3", "0.1")
    gi.require_version("Gtk", "3.0")
    from gi.repository import AppIndicator3, Gtk, GLib
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False


class ToggleSwitch(ttk.Frame):
    def __init__(self, parent, command=None, width=72):
        super().__init__(parent, width=width, height=36)
        self.pack_propagate(False)
        self._cmd = command
        self._state = False
        self._sw = width
        self._r = 14
        c = tk.Canvas(self, width=width, height=36, highlightthickness=0, bg=CARD)
        c.pack()
        c.bind("<Button-1>", lambda _: self.toggle())
        y = 18
        self._bg = c.create_rectangle(2, y - self._r, width - 2, y + self._r, fill="#555", outline="")
        self._knob = c.create_oval(4, y - self._r + 2, 4 + 2 * self._r - 4, y + self._r - 2, fill="#ddd", outline="")
        self._c = c
        self._draw()

    def _draw(self):
        if self._state:
            self._c.itemconfig(self._bg, fill=GREEN)
            cx = self._sw - self._r - 4
        else:
            self._c.itemconfig(self._bg, fill="#555")
            cx = self._r + 4
        self._c.coords(self._knob, cx - self._r + 2, 18 - self._r + 2, cx + self._r - 2, 18 + self._r - 2)

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
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Universal Netlimiter")
        self.root.resizable(True, True)
        self.root.minsize(440, 340)

        self.iface = ""
        self.active = False
        self.limit_dl_mbps = 100
        self.limit_ul_mbps = 10
        self.dl_pct = tk.DoubleVar(value=100)
        self.ul_pct = tk.DoubleVar(value=100)
        self._updating = False

        self._traffic_rx = [0, 0]
        self._traffic_tx = [0, 0]

        _create_icon()
        _create_small_icons()
        self._load_icons()
        self._set_window_icon()

        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", background=BG)
        s.configure("card.TFrame", background=CARD, relief="flat")
        s.configure("stat.TLabel", background=CARD, foreground=FG2, font=("Segoe UI", 10))
        s.configure("bold.TLabel", background=CARD, foreground=FG, font=("Segoe UI", 12, "bold"))
        s.configure("hint.TLabel", background=CARD, foreground=FG3, font=("Segoe UI", 8))
        s.configure("small.TLabel", background=CARD, foreground=FG2, font=("Segoe UI", 9))
        s.configure("result.TLabel", background=CARD, foreground=FG, font=("Segoe UI", 10))
        s.configure("TScale", background=CARD, troughcolor="#444", sliderlength=20)
        s.configure("measure.TButton", foreground=FG, background="#3d3d3d", bordercolor="#555",
                     lightcolor="#3d3d3d", darkcolor="#3d3d3d", focuscolor="#3d3d3d")
        s.map("measure.TButton", foreground=[("active", FG)], background=[("active", "#4a4a4a")])

        self._setup_ui()
        self._detect_interfaces()
        self._setup_tray()

    def _load_icons(self):
        self._iface_img = None
        self._dl_img = None
        self._ul_img = None
        try:
            from PIL import Image, ImageTk
            if os.path.exists(IFACE_ICON):
                self._iface_img = ImageTk.PhotoImage(Image.open(IFACE_ICON))
            if os.path.exists(DL_ICON):
                self._dl_img = ImageTk.PhotoImage(Image.open(DL_ICON))
            if os.path.exists(UL_ICON):
                self._ul_img = ImageTk.PhotoImage(Image.open(UL_ICON))
        except Exception:
            pass

    def _set_window_icon(self):
        try:
            if os.path.exists(ICON_PATH):
                from PIL import Image, ImageTk
                img = ImageTk.PhotoImage(Image.open(ICON_PATH).resize((32, 32)))
                self.root.iconphoto(True, img)
        except Exception:
            pass

    def _setup_ui(self):
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        outer = ttk.Frame(self.root, padding=(36, 20), style="card.TFrame")
        outer.pack(fill="both", expand=True)

        def _row_label(parent, text, img):
            kw = dict(text=text, style="stat.TLabel", width=15)
            if img:
                kw["image"] = img
                kw["compound"] = "left"
            ttk.Label(parent, **kw).pack(side="left")

        iface_frame = ttk.Frame(outer, style="card.TFrame")
        iface_frame.pack(fill="x", pady=(0, 24))
        _row_label(iface_frame, " Interface", self._iface_img)
        self.iface_combo = ttk.Combobox(iface_frame, state="readonly", width=22)
        self.iface_combo.pack(side="left", padx=(4, 2))

        dl_frame = ttk.Frame(outer, style="card.TFrame")
        dl_frame.pack(fill="x", pady=(0, 10))
        _row_label(dl_frame, " Download", self._dl_img)
        self.dl_entry = ttk.Entry(dl_frame, width=8, justify="right")
        self.dl_entry.insert(0, str(self.limit_dl_mbps))
        self.dl_entry.bind("<KeyRelease>", lambda _: self._entry_to_slider("dl"))
        self.dl_entry.bind("<FocusOut>", lambda _: self._entry_to_slider("dl"))
        self.dl_entry.pack(side="left", padx=(4, 2))
        ttk.Label(dl_frame, text="Mbit/s", style="stat.TLabel").pack(side="left")
        self.dl_slider = ttk.Scale(dl_frame, from_=0, to=100, variable=self.dl_pct,
                                   command=self._on_dl_slider, length=140)
        self.dl_slider.pack(side="left", padx=(8, 0), fill="x", expand=True)

        ul_frame = ttk.Frame(outer, style="card.TFrame")
        ul_frame.pack(fill="x", pady=(0, 24))
        _row_label(ul_frame, " Upload", self._ul_img)
        self.ul_entry = ttk.Entry(ul_frame, width=8, justify="right")
        self.ul_entry.insert(0, str(self.limit_ul_mbps))
        self.ul_entry.bind("<KeyRelease>", lambda _: self._entry_to_slider("ul"))
        self.ul_entry.bind("<FocusOut>", lambda _: self._entry_to_slider("ul"))
        self.ul_entry.pack(side="left", padx=(4, 2))
        ttk.Label(ul_frame, text="Mbit/s", style="stat.TLabel").pack(side="left")
        self.ul_slider = ttk.Scale(ul_frame, from_=0, to=100, variable=self.ul_pct,
                                   command=self._on_ul_slider, length=140)
        self.ul_slider.pack(side="left", padx=(8, 0), fill="x", expand=True)

        measure_frame = ttk.Frame(outer, style="card.TFrame")
        measure_frame.pack(fill="x", pady=(0, 4))
        self.measure_btn = ttk.Button(measure_frame, text="Messen", command=self._start_measure,
                                      width=10, style="measure.TButton")
        self.measure_btn.pack()
        self.measure_result = ttk.Label(outer, text="", style="result.TLabel")
        self.measure_result.pack(pady=(0, 16))

        live_frame = ttk.Frame(outer, style="card.TFrame")
        live_frame.pack(fill="x")
        self.dl_label = ttk.Label(live_frame, text="\u2193 \u2014", style="small.TLabel")
        self.dl_label.pack(side="left")
        self.ul_label = ttk.Label(live_frame, text="\u2191 \u2014", style="small.TLabel")
        self.ul_label.pack(side="right")

        separator = ttk.Separator(outer, orient="horizontal")
        separator.pack(fill="x", pady=(8, 6))

        status_row = ttk.Frame(outer, style="card.TFrame")
        status_row.pack(fill="x")
        self.dot = tk.Canvas(status_row, width=12, height=12, highlightthickness=0, bg=CARD)
        self.dot.pack(side="left", padx=(0, 6))
        self._dot = self.dot.create_oval(2, 2, 10, 10, fill=FG3, outline="")
        self.status_label = ttk.Label(status_row, text="Aus", style="stat.TLabel")
        self.status_label.pack(side="left", fill="x", expand=True)
        ttk.Label(status_row, text="Limit On/Off", style="stat.TLabel").pack(side="right", padx=(0, 4))
        self.toggle = ToggleSwitch(status_row, command=self._on_toggle)
        self.toggle.pack(side="right")

        self._update_live()

    def _detect_interfaces(self):
        try:
            r = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True, timeout=5)
            ifaces = []
            for line in r.stdout.splitlines():
                m = re.match(r'\d+:\s+(\S+):', line)
                if m:
                    name = m.group(1).split('@')[0]
                    if name != "lo":
                        ifaces.append(name)
            if ifaces:
                self.iface_combo["values"] = ifaces
        except:
            pass
        self._auto_select_iface()

    def _auto_select_iface(self):
        ifaces = list(self.iface_combo["values"])
        phys = [i for i in ifaces if not re.search(r'^(tun|tap|wg)', i)]
        self.iface_combo.set(phys[0] if phys else ifaces[0] if ifaces else "")
        self.iface = self.iface_combo.get()

    def _on_dl_slider(self, _=None):
        if self._updating:
            return
        self._updating = True
        val = int(self.limit_dl_mbps * self.dl_pct.get() / 100)
        self.dl_entry.delete(0, "end")
        self.dl_entry.insert(0, str(val))
        self._updating = False

    def _on_ul_slider(self, _=None):
        if self._updating:
            return
        self._updating = True
        val = int(self.limit_ul_mbps * self.ul_pct.get() / 100)
        self.ul_entry.delete(0, "end")
        self.ul_entry.insert(0, str(val))
        self._updating = False

    def _entry_to_slider(self, which):
        if self._updating:
            return
        self._updating = True
        try:
            if which == "dl":
                val = int(self.dl_entry.get() or 0)
                self.limit_dl_mbps = max(0, val)
                self.dl_pct.set(100)
            else:
                val = int(self.ul_entry.get() or 0)
                self.limit_ul_mbps = max(0, val)
                self.ul_pct.set(100)
        except ValueError:
            pass
        self._updating = False

    def _start_measure(self):
        self.measure_btn.config(state="disabled", text="Messe\u2026")
        self._set_status("Messe Download \u2026", YELLOW)
        threading.Thread(target=self._do_measure, daemon=True).start()

    def _do_measure(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()
            self.root.after(0, lambda: self._set_status("Messe Download \u2026", YELLOW))
            dl_bps = st.download()
            dl_mbps = int(dl_bps / 1_000_000)
            self.root.after(0, lambda: self._set_status("Messe Upload \u2026", YELLOW))
            ul_bps = st.upload()
            ul_mbps = int(ul_bps / 1_000_000)
            self.root.after(0, self._finish_measure, dl_mbps, ul_mbps)
        except Exception as e:
            self.root.after(0, self._fail_measure, str(e))

    def _finish_measure(self, dl, ul):
        self.limit_dl_mbps = dl
        self.limit_ul_mbps = ul
        self._updating = True
        self.dl_entry.delete(0, "end")
        self.dl_entry.insert(0, str(dl))
        self.ul_entry.delete(0, "end")
        self.ul_entry.insert(0, str(ul))
        self.dl_pct.set(100)
        self.ul_pct.set(100)
        self._updating = False
        self.measure_result.config(text=f"Download {dl} Mbit/s - Upload {ul} Mbit/s")
        self._set_status("Gemessen", GREEN)
        self.measure_btn.config(state="normal", text="Messen")

    def _fail_measure(self, err):
        self._set_status("Fehler beim Messen", RED)
        self.measure_btn.config(state="normal", text="Messen")
        messagebox.showerror("Fehler", f"Speedtest fehlgeschlagen:\n{err}")

    def _update_live(self):
        try:
            with open(f"/sys/class/net/{self.iface}/statistics/rx_bytes") as f:
                rx = int(f.read())
            with open(f"/sys/class/net/{self.iface}/statistics/tx_bytes") as f:
                tx = int(f.read())
            if self._traffic_rx[0]:
                drx = (rx - self._traffic_rx[0]) / 1024 / 1024 * 8
                dtx = (tx - self._traffic_tx[0]) / 1024 / 1024 * 8
                self.dl_label.config(text=f"\u2193 {drx:.1f} Mbit/s")
                self.ul_label.config(text=f"\u2191 {dtx:.1f} Mbit/s")
            else:
                self.dl_label.config(text="\u2193 \u2014")
                self.ul_label.config(text="\u2191 \u2014")
            self._traffic_rx = [rx, time.monotonic()]
            self._traffic_tx = [tx, time.monotonic()]
        except:
            pass
        self.root.after(2000, self._update_live)

    def _on_toggle(self, state):
        if not self.iface:
            self.toggle.set(False)
            return
        if state:
            self._set_status("wird aktiviert \u2026", YELLOW)
            threading.Thread(target=self._activate, daemon=True).start()
        else:
            self._set_status("wird deaktiviert \u2026", YELLOW)
            threading.Thread(target=self._deactivate, daemon=True).start()

    def _set_status(self, text, color):
        self.dot.itemconfig(self._dot, fill=color)
        self.status_label.config(text=text)
        if HAS_TRAY:
            self._update_tray()

    def _activate(self):
        dl_actual = int(self.limit_dl_mbps * self.dl_pct.get() / 100)
        ul_actual = int(self.limit_ul_mbps * self.ul_pct.get() / 100)
        if dl_actual <= 0 and ul_actual <= 0:
            self.root.after(0, lambda: self.toggle.set(False))
            return
        limit_dl_kbit = dl_actual * 1000
        limit_ul_kbit = ul_actual * 1000
        burst = max(256, int(max(limit_dl_kbit, limit_ul_kbit) * 0.05))
        script = f"""set -e
tc qdisc del dev {self.iface} ingress 2>/dev/null || true
tc qdisc add dev {self.iface} ingress
tc filter add dev {self.iface} parent ffff: protocol all prio 1 u32 match u32 0 0 police rate {limit_dl_kbit}kbit burst {burst}kbit drop
tc qdisc del dev {self.iface} root 2>/dev/null || true
tc qdisc add dev {self.iface} root tbf rate {limit_ul_kbit}kbit burst {burst}kbit latency 50ms
"""
        ok, err = self._run_root(script)
        self.root.after(0, self._cb_activate, ok, err, dl_actual, ul_actual)

    def _cb_activate(self, ok, err, dl_actual, ul_actual):
        if ok:
            self.active = True
            self._set_status(f"Download: {dl_actual} / Upload: {ul_actual} Mbit/s", GREEN)
        else:
            self.toggle.set(False)
            self._set_status("Fehler", RED)
            messagebox.showerror("Fehler", f"Konnte Limit nicht setzen:\n{err}")

    def _deactivate(self):
        script = f"""set -e
tc qdisc del dev {self.iface} ingress 2>/dev/null || true
tc qdisc del dev {self.iface} root 2>/dev/null || true
"""
        ok, err = self._run_root(script)
        self.root.after(0, self._cb_deactivate, ok, err)

    def _cb_deactivate(self, ok, err):
        if ok:
            self.active = False
            self._set_status("Aus", FG3)
        else:
            self.toggle.set(True)
            self._set_status("Fehler", RED)
            messagebox.showerror("Fehler", f"Konnte Limit nicht entfernen:\n{err}")

    def _make_askpass(self):
        c = """#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog
r = tk.Tk()
r.withdraw()
pw = simpledialog.askstring("Passwort", "Root-Passwort f\u00fcr Limiter:", show="*")
if pw: print(pw, end="")
r.destroy()
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(c)
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
                try: os.unlink(p)
                except: pass

# --- System Tray ---
    def _setup_tray(self):
        self._indicator = None
        if not HAS_TRAY:
            return
        try:
            self._indicator = AppIndicator3.Indicator.new(
                "netlimiter", ICON_PATH,
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )
            self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self._indicator_menu = Gtk.Menu()
            self._tray_items = {}
            items = [
                ("show", "Fenster anzeigen", self._tray_show),
                ("toggle", "Limit einschalten", self._tray_toggle),
            ]
            for key, label, cb in items:
                item = Gtk.MenuItem(label=label)
                item.connect("activate", lambda _, c=cb: self.root.after(0, c))
                self._indicator_menu.append(item)
                self._tray_items[key] = item
            self._indicator_menu.append(Gtk.SeparatorMenuItem())
            quit_item = Gtk.MenuItem(label="Beenden")
            quit_item.connect("activate", lambda _: self.root.after(0, self._tray_quit))
            self._indicator_menu.append(quit_item)
            self._indicator_menu.show_all()
            self._indicator.set_menu(self._indicator_menu)
            self.root.after(100, self._pump_glib)
        except Exception:
            self._indicator = None

    def _pump_glib(self):
        if self._indicator:
            GLib.main_context_default().iteration(False)
            self.root.after(100, self._pump_glib)

    def _update_tray(self):
        if not self._indicator or "toggle" not in self._tray_items:
            return
        self._tray_items["toggle"].set_label("Limit ausschalten" if self.active else "Limit einschalten")
        label = f"Limiter {'Aktiv' if self.active else 'Aus'}"
        self._indicator.set_title(label)
        try:
            self._indicator.set_label(label, "")
        except Exception:
            pass

    def _tray_show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_toggle(self):
        if not self.iface:
            return
        new_state = not self.active
        self.toggle.set(new_state)
        self._on_toggle(new_state)

    def _tray_quit(self):
        self.root.quit()

    def _on_close(self):
        self.root.withdraw()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
