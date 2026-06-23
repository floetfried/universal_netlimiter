# Universal Netlimiter

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

GUI Bandwidth Limiter for Linux. Precise control over your network bandwidth using native Linux kernel mechanisms — without interfering with VPNs or requiring external kernel modules.

## Features

- **Download + Upload limiting** — ingress policer for DL, TBF qdisc for UL
- **Direct Mbit/s entry** — type your desired limit; the slider fine-tunes 1–100% of the cap
- **Integrated speedtest** — measures DL + UL and populates the limit fields automatically
- **Live traffic monitor** — real-time view of current ↓/↑ Mbit/s, updated every 2s
- **System tray** — minimizes to tray via AppIndicator3; status always visible
- **No VPN conflicts** — limits only the physical interface, ignores virtual interfaces
- **No persistent root** — `sudo -A` password prompt only when toggling on/off

## How it works

- **Download limiting** — `tc` ingress policer drops packets exceeding the threshold; TCP backs off gracefully
- **Upload limiting** — `tc` TBF (Token Bucket Filter) on egress traffic
- Pure kernel mechanisms, zero additional modules, no IFB, no NetworkManager workarounds

## Requirements (running from source)

- Linux with `tc` (iproute2) — preinstalled on virtually every distribution
- `sudo` access — only needed for toggling limits

**Arch:**
```
sudo pacman -S tk python-pillow python-speedtest-cli
```

**Debian/Ubuntu:**
```
sudo apt install python3-tk python3-pillow python3-speedtest-cli
```

> **Note on system tray:** The tray icon requires `gi` (python-gobject / libappindicator3). The script handles this gracefully via `try/except` — the app runs perfectly without it.

## Portable AppImage (zero dependencies)

Download the latest AppImage from the [releases page](https://github.com/floetfried/universal_netlimiter/releases):

```bash
chmod +x Universal-Netlimiter-x86_64.AppImage
./Universal-Netlimiter-x86_64.AppImage
```

No Python, no pip, no packages required. The AppImage bundles:
- **Python 3.12** with tkinter + Tcl/Tk 8.6
- **speedtest-cli** and **Pillow** pre-installed

## Installation (from source)

```bash
git clone https://github.com/floetfried/universal_netlimiter.git
cd universal_netlimiter
python3 netlimiter.py
```

A `.desktop` entry is provided at `~/.local/share/applications/netlimiter.desktop` for the application menu.

For autostart: `~/.config/autostart/netlimiter.desktop`

## Usage

1. Launch the app (via menu, AppImage, or `python3 netlimiter.py`)
2. Optionally click **Speedtest** — runs a speedtest for DL + UL
3. Type the desired Mbit/s limit; the slider fine-tunes the percentage
4. Flip the toggle switch — enter your root password
5. Done — download and upload are now limited

Toggle off to remove the limits. Closing the window minimizes to the system tray.

## Uninstall

```bash
rm -rf ~/universal_netlimiter
rm ~/.local/share/applications/netlimiter.desktop
rm ~/.config/autostart/netlimiter.desktop
```

## License

Distributed under the **GNU General Public License v3**. Free and open-source for everyone, but strictly prohibited from being bundled into proprietary products.

## Windows Edition

Also available for Windows: [Universal Netlimiter Windows Edition](https://github.com/floetfried/universal_netlimiter_windows)
– same features, same dark theme, built with WinDivert instead of `tc`.
