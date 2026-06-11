# Limiter

Einfacher Bandbreitenbegrenzer für Linux. GUI mit einem Kippschalter – limitiert den Download auf 75% der maximalen Leitung.

## Voraussetzungen

- Linux mit `tc` (iproute2) – auf jedem Linux vorinstalliert
- Python 3 mit tkinter (`sudo pacman -S tk` oder `sudo apt install python3-tk`)
- `sudo`-Zugriff (wird nur beim Betätigen des Schalters via Passwort-Dialog benötigt)

## Installation

```bash
git clone https://github.com/floetfried/floet.git
cd floet
python3 netlimiter.py
```

Oder die `netlimiter.py` einfach woanders hinkopieren und starten.

## Verwendung

1. `python3 netlimiter.py` starten
2. Schalter antippen
3. Root-Passwort eingeben
4. Fertig – der Download des gesamten Systems wird auf ~75% der Leitung begrenzt

Erneutes Antipper entfernt das Limit wieder.

## Funktionsweise

Legt via `tc` (traffic control) einen **Ingress Policer** auf dem physischen Netzwerk-Interface an. Pakete, die das Limit überschreiten, werden verworfen – TCP bremst dadurch automatisch runter. Erzeugt keine neuen Interfaces, kein IFB, keine Kernel-Module.

## Anpassung

Die Werte in den ersten Zeilen der Datei:

```python
MAX_DL_MBPS = 213   # deine maximale Leitung in Mbit/s
LIMIT_PCT = 75       # Prozent, auf die limitiert werden soll
```

Einfach ändern und neustarten.
