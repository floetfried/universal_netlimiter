# Universal Netlimiter

GUI bandwidth limiter for Linux. Set a percentage slider to cap download speed — with live traffic display and built-in speedtest.

## Features

- **Slider** (1-100%) — set your limit intuitively
- **Speedtest** — measures DL + UL, auto-fills the max value
- **Live bandwidth** — current ↓/↑ Mbit/s updated every 2s
- **System tray** — minimizes to tray, status always visible
- **No VPN conflict** — limits the physical interface only, no virtual interfaces created
- **No persistent root** — password prompt only when toggling

## Requirements

- Linux with `tc` (iproute2) — preinstalled on every distribution
- Python 3 with tkinter (`sudo pacman -S tk` or `sudo apt install python3-tk`)
- `sudo` access (only needed when toggling the limiter)
- Packages: `python-speedtest-cli`, `python-pillow` (for the icon)

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
3. Adjust the max value manually if needed
4. Drag the slider to your desired percentage
5. Flip the toggle switch — enter your root password
6. Done — download is now limited

Toggle off to remove the limit. Closing the window minimizes to the system tray.

## How it works

Creates an **ingress policer** via `tc` on the physical network interface. Packets exceeding the limit are dropped — TCP automatically backs off. No extra interfaces, no IFB, no kernel modules needed.

## Uninstall

```bash
rm -rf ~/universal_netlimiter
rm ~/.local/share/applications/netlimiter.desktop
rm ~/.config/autostart/netlimiter.desktop
```
