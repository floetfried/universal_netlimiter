# Universal Netlimiter

GUI-Bandbreitenbegrenzer für Linux. Regels via Schieberegler wie viel vom verfügbaren Download genutzt werden soll – mit Live-Anzeige und Speedtest.

## Features

- **Slider** (1-100%) – intuitiv, kein Rumrechnen
- **Speedtest** – misst DL + UL und trägt den Max-Wert automatisch ein
- **Live-Bandbreite** – aktuelle ↓/↑ Mbit/s alle 2s
- **System Tray** – minimiert in die Taskleiste, Status sichtbar
- **Kein VPN-Konflikt** – limitiert nur das physikalische Interface, erzeugt keine neuen Interfaces
- **Kein Root für Dauerbetrieb** – Passwort nur beim Umschalten

## Voraussetzungen

- Linux mit `tc` (iproute2) – auf jedem Linux vorinstalliert
- Python 3 mit tkinter (`sudo pacman -S tk` oder `sudo apt install python3-tk`)
- `sudo`-Zugriff (wird nur beim Betätigen des Schalters via Passwort-Dialog benötigt)
- Pakete: `python-speedtest-cli`, `python-pillow` (für Icon)

## Installation

```bash
git clone https://github.com/floetfried/universal_netlimiter.git
cd universal_netlimiter
python3 netlimiter.py
```

Oder via `.desktop`-Eintrag im Startmenü (wird bei `make install` oder manuellem Kopieren angelegt).

Autostart: `~/.config/autostart/netlimiter.desktop`

## Verwendung

1. `python3 netlimiter.py` starten (oder über Startmenü)
2. Optional: „Messen" klicken → Speedtest misst DL + UL
3. Max-Wert ggf. manuell anpassen
4. Schieberegler auf gewünschte Prozent stellen
5. Schalter antippen → Root-Passwort eingeben
6. Fertig – Download wird begrenzt

Erneutes Antippen entfernt das Limit. Schließen minimiert ins Tray.

## Funktionsweise

Legt via `tc` (traffic control) einen **Ingress Policer** auf dem physikalischen Netzwerk-Interface an. Pakete, die das Limit überschreiten, werden verworfen – TCP bremst dadurch automatisch runter. Erzeugt keine neuen Interfaces, kein IFB, keine Kernel-Module.

## Deinstallation

```bash
rm -rf ~/universal_netlimiter
rm ~/.local/share/applications/netlimiter.desktop
rm ~/.config/autostart/netlimiter.desktop
```
