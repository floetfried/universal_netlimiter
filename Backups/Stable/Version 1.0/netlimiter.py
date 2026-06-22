#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import tempfile
import os
import stat
import re


class NetlimiterApp:
    MAX_DL_MBPS = 213
    LIMIT_PCT = 75

    def __init__(self, root):
        self.root = root
        self.root.title("Limiter")
        self.root.resizable(False, False)

        self.iface = self._detect_phys_iface()
        self.active = False
        self.status_var = tk.StringVar(value="Aus")
        self.limit_mbps = int(self.MAX_DL_MBPS * self.LIMIT_PCT / 100)

        self._setup_ui()

    def _detect_phys_iface(self):
        r = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            for iface in re.findall(r'dev\s+(\S+)', line):
                if not re.search(r'^(tun|tap|wg|br|docker|veth)', iface):
                    return iface
        return "enp9s0"

    def _setup_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack()

        ttk.Label(frame, text=f"Max {self.MAX_DL_MBPS} Mbit/s → Limit {self.limit_mbps} Mbit/s ({self.LIMIT_PCT}%)",
                  font=("", 9)).pack()
        ttk.Label(frame, text=f"Interface: {self.iface}", foreground="gray").pack()

        self.toggle_btn = ttk.Button(frame, text="EINSCHALTEN", command=self.toggle, width=22)
        self.toggle_btn.pack(pady=(15, 5))

        ttk.Label(frame, textvariable=self.status_var, foreground="#555").pack()

    def toggle(self):
        self.toggle_btn.config(state="disabled")
        if self.active:
            threading.Thread(target=self._deactivate, daemon=True).start()
        else:
            threading.Thread(target=self._activate, daemon=True).start()

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
        self.toggle_btn.config(state="normal")
        if ok:
            self.active = True
            self.toggle_btn.config(text="AUSSCHALTEN")
            self.status_var.set(f"Limit: {self.limit_mbps} Mbit/s")
        else:
            self.toggle_btn.config(text="EINSCHALTEN")
            messagebox.showerror("Fehler", f"Konnte Limit nicht setzen auf {self.iface}:\n{err}")

    def _deactivate(self):
        script = f"""set -e
tc qdisc del dev {self.iface} ingress 2>/dev/null || true
"""
        ok, err = self._run_root(script)
        self.root.after(0, self._cb_deactivate, ok, err)

    def _cb_deactivate(self, ok, err):
        self.toggle_btn.config(state="normal", text="EINSCHALTEN")
        if ok:
            self.active = False
            self.status_var.set("Aus")
        else:
            messagebox.showerror("Fehler", f"Konnte Limit nicht entfernen:\n{err}")

    def _make_askpass(self):
        c = """#!/usr/bin/env python3
import tkinter as tk
from tkinter import simpledialog
r = tk.Tk()
r.withdraw()
pw = simpledialog.askstring("Passwort", "Root-Passwort für Limiter:", show="*")
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
                try:
                    os.unlink(p)
                except OSError:
                    pass


if __name__ == "__main__":
    root = tk.Tk()
    NetlimiterApp(root)
    root.mainloop()
