#!/usr/bin/env python3
"""Inventario de los textos de 16 puntos: cada llamada a las rutinas de texto del cartucho, la
cadena que le llega en HL (buscada hacia atras en el listado) y lo que dice.

Uso: inventario.py <carpeta del desensamblado> > traduccion/inventario.txt"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuente16  # noqa: E402

RUTINAS = r"escribe_texto|0?5acdh|L_5ACF|05acfh|L_5AB1|05ab1h|L_5AB8|05ab8h|L_5ABF|05abfh|L_5AC6|05ac6h|L_5B23|05b23h|L_5B25|05b25h"
BASE = {0: 0x4000, 1: 0x6000, 2: 0x8000, 3: 0xA000, 4: 0xA000}


def main(argv):
    raiz = argv[1]
    rom = open(os.path.join(raiz, "majutsushi.rom"), "rb").read()
    for p in range(5):
        lineas = open(os.path.join(raiz, "src", "majutsushi_p%02d.asm" % p), encoding="utf-8").read().split("\n")
        for i, ln in enumerate(lineas):
            if not re.search(r"\b(call|jp)\b.*\b(%s)\b" % RUTINAS, ln, re.I):
                continue
            pc = re.search(r";([0-9a-f]{4})", ln)
            hl = de = None
            for k in range(i - 1, max(i - 10, 0), -1):
                m = re.search(r"ld hl,0?([0-9a-f]{4})h", lineas[k], re.I)
                if m and hl is None:
                    hl = int(m.group(1), 16)
                m = re.search(r"ld de,0?([0-9a-f]{4})h", lineas[k], re.I)
                if m and de is None:
                    de = int(m.group(1), 16)
            txt = ""
            if hl is not None:
                b = 0 if hl < 0x6000 else p
                off = b * 0x2000 + hl - BASE[b]
                cod = []
                while rom[off] != 0xFF and len(cod) < 40:
                    cod.append(rom[off])
                    off += 1
                txt = "%s  [%s]" % (fuente16.lee(cod), " ".join("%02X" % c for c in cod))
            print("p%02d:%s  HL=%s DE=%s  %s" % (p, pc.group(1).upper() if pc else "?",
                                                 "%04X" % hl if hl is not None else "----",
                                                 "%04X" % de if de is not None else "----", txt))


if __name__ == "__main__":
    main(sys.argv)
