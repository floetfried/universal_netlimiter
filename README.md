# Universal Netlimiter – Precise bandwidth control for Linux

[![Latest Release](https://img.shields.io/github/v/release/floetfried/universal_netlimiter)](https://github.com/floetfried/universal_netlimiter/releases)
[![License: GPL v3](https://img.shields.io/github/license/floetfried/universal_netlimiter)](https://www.gnu.org/licenses/gpl-3.0)
[![AppImageHub](https://img.shields.io/badge/AppImageHub-Available-blue)](https://appimage.github.io/)

A lightweight, cross‑platform graphical interface that precisely limits network bandwidth on Linux using native kernel mechanisms. No VPN conflicts, no extra kernel modules, no persistent root permissions.

## Table of Contents
- [Features](#features)
- [How It Works](#how-it-works)
- [System Requirements](#system-requirements)
- [Portable AppImage](#portable-appimage)
- [Installation from Source](#installation-from-source)
- [Usage](#usage)
- [Uninstall](#uninstall)
- [License](#license)
- [Windows Edition](#windows-edition)
- [Contributing](#contributing)
- [Changelog](#changelog)

## Features
- **Download & Upload limiting** – ingress policer for download, TBF queue for upload.
- **Direct Mbit/s input** – type the desired limit; a precision slider adjusts 1–100 % of the cap.
- **Integrated speed test** – automatically measures download and upload speeds and populates the limit fields.
- **Live traffic monitor** – real‑time display of current ↓/↑ Mbit/s, updated every two seconds.
- **System tray icon** – minimises to tray via AppIndicator3; status stays visible.
- **No VPN interference** – limits only the physical network interface; virtual interfaces and VPNs are ignored.
- **Minimal root usage** – `sudo -A` prompts only when toggling the limits on or off.

## How It Works
- **Download limiting** – Uses the `tc` ingress policer; packets that exceed the threshold are dropped, causing TCP to back off gracefully.
- **Upload limiting** – Implements the `tc` Token Bucket Filter (TBF) on egress traffic.
- **Pure kernel** – No additional modules, no IFB, no NetworkManager workarounds; relies solely on long‑standing kernel subsystems.

## System Requirements
When running from source the following prerequisites are needed:
- A Linux distribution with the `tc` utility (part of `iproute2`).
- `sudo` access – required only for activating or deactivating limits.
- Core Python packages:
  - On Arch: `sudo pacman -S tk python-pillow python-speedtest-cli`
  - On Debian/Ubuntu: `sudo apt install python3-tk python3-pillow python3-speedtest-cli`

## Portable AppImage
The AppImage contains:
- Python 3.12 with Tkinter and Tcl/Tk 8.6.
- `speedtest-cli` and `Pillow` pre‑installed.

Download the latest AppImage from the [releases page](https://github.com/floetfried/universal_netlimiter/releases) and run:
```bash
chmod +x Universal-Netlimiter-x86_64.AppImage
./Universal-Netlimiter-x86_64.AppImage
```
No additional packages or Python installations are required on the host.

## Installation from Source
```bash
git clone https://github.com/floetfried/universal_netlimiter.git
cd universal_netlimiter
python3 netlimiter.py
```
A `.desktop` entry is automatically installed in `~/.local/share/applications` for menu integration. For autostart, copy the file to `~/.config/autostart`.

## Usage
1. Launch the application (menu, AppImage, or `python3 netlimiter.py`).
2. Optional: click **Speedtest** to measure current speeds.
3. Enter the desired Mbit/s limit; adjust the slider for fine‑tuning.
4. Toggle the switch – a `sudo` password prompt appears.
5. Bandwidth is now limited.
6. Toggle off to remove limits; closing the window minimises to the system tray.

## Uninstall
```bash
rm -rf ~/universal_netlimiter
rm ~/.local/share/applications/netlimiter.desktop
rm ~/.config/autostart/netlimiter.desktop
```

## License
Distributed under the GNU General Public License v3.0. Free and open‑source for everyone, but prohibited from being bundled into proprietary products.

## Windows Edition
A Windows build is available: [Universal Netlimiter Windows Edition](https://github.com/floetfried/universal_netlimiter_windows). It offers the same features and dark theme, built with WinDivert instead of `tc`.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request. For detailed guidelines, see the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Changelog
See the [CHANGELOG.md](CHANGELOG.md) for a record of all changes.

