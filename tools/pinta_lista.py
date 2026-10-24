#!/usr/bin/env python3
"""Pinta una lista de tiles (p00:5363: X, Y, tiles; 0xFE X Y; 0xFF) de una ROM con la hoja de tiles
de la pagina 1 de un volcado de VRAM: para ver menus que la partida no saca sola.

Uso: pinta_lista.py rom vram-N.bin vdp-N.txt banco:DIR salida.png"""
import re
import sys

from PIL import Image

BASE = {0: 0x4000, 1: 0x6000, 2: 0x8000, 3: 0xA000, 4: 0xA000}


def main(rom_f, vram_f, vdp_f, sitio, sal):
    rom = open(rom_f, "rb").read()
    vram = open(vram_f, "rb").read()
    pal = [(0, 0, 0)] * 16
    for m in re.finditer(r"P(\d+) = 0x([0-9A-Fa-f]{4})", open(vdp_f).read()):
        i, v = int(m.group(1)), int(m.group(2), 16)
        pal[i] = (((v >> 4) & 7) * 255 // 7, ((v >> 8) & 7) * 255 // 7, (v & 7) * 255 // 7)
    b, d = sitio.split(":")
    b = int(b)
    o = b * 0x2000 + int(d, 16) - BASE[b]
    im = Image.new("RGB", (512, 424), (30, 30, 30))
    px = im.load()
    x, y = rom[o], rom[o + 1]
    o += 2
    while rom[o] != 0xFF:
        t = rom[o]
        o += 1
        if t == 0xFE:
            x, y = rom[o], rom[o + 1]
            o += 2
            continue
        tx, ty = (t & 0x1F) * 16, 0xB0 + (t >> 5) * 8
        for yy in range(8):
            for xx in range(16):
                v = vram[0x10000 + (ty + yy) * 256 + (tx + xx) // 2]
                c = pal[v >> 4 if (tx + xx) % 2 == 0 else v & 15]
                px[2 * x + xx, 2 * (y + yy)] = c
                px[2 * x + xx, 2 * (y + yy) + 1] = c
        x += 8
    im.save(sal)


if __name__ == "__main__":
    main(*sys.argv[1:6])
