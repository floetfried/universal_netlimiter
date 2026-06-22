# Universal Netlimiter

GUI bandwidth limiter for Linux. Set download and upload speed limits with direct Mbit/s entry and percentage sliders — with live traffic display and built-in speedtest.

## Features

- **Download + Upload limiting** — ingress policer for DL, TBF qdisc for UL
- **Direct Mbit/s entry** — type the limit, slider adjusts automatically
- **Percentage slider** — scale the measured max up/down
- **Speedtest** — measures DL + UL, fills limits at 100%
- **Live bandwidth** — current ↓/↑ Mbit/s updated every 2s
- **System tray** — minimizes to tray, status always visible
- **No VPN conflict** — limits the physical interface only, no virtual interfaces created
- **No persistent root** — password prompt only when toggling

## Requirements

- Linux with `tc` (iproute2) — preinstalled on every distribution
- Python 3 with tkinter (`sudo pacman -S tk` or `sudo apt install python3-tk`)
- `sudo` access (only needed when toggling the limiter)
- Packages: `python-speedtest-cli`, `python-pillow` (for icons)

## Installation

```bash
git clone https://github.com/floetfried/universal_netlimiter.git
cd universal_netlimiter
python3 netlimiter.py
```

A `.desktop` entry is provided at `~/.local/share/applications/netlimiter.desktop` so the app appears in your application menu.

For autostart: `~/.config/autostart/netlimiter.desktop`

## Usage

1. Launch the app (via menu or `python3 netlimiter.py`)
2. Optionally click "Messen" — runs a speedtest for DL + UL
3. Type the desired Mbit/s limit (or use the slider next to it)
4. Flip the toggle switch — enter your root password
5. Done — download and upload are now limited

Toggle off to remove the limits. Closing the window minimizes to the system tray.

## How it works

Creates an **ingress policer** via `tc` on the physical network interface for download limiting, and a **TBF (token bucket filter)** qdisc on egress for upload limiting. Packets exceeding the limit are dropped — TCP automatically backs off. No extra interfaces, no IFB, no kernel modules needed.

## Uninstall

```bash
rm -rf ~/universal_netlimiter
rm ~/.local/share/applications/netlimiter.desktop
rm ~/.config/autostart/netlimiter.desktop
```
