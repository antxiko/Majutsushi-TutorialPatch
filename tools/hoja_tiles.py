#!/usr/bin/env python3
"""La hoja de tiles de 8 x 8 de la pagina 1 (p00:53DE: tile A en X = (A & 0x1F) x 8, Y = 0xB0 + (A >> 5) x 8;
las X van en puntos de 256 y vdp_copia las dobla: 16 puntos de SCREEN 7 por tile)
leida de un volcado de VRAM de openMSX (SCREEN 7), con la paleta del vdp-N.txt; ampliada y con el numero.

Uso: hoja_tiles.py vram-N.bin vdp-N.txt salida.png"""
import re
import sys

from PIL import Image, ImageDraw


def paleta(vdp):
    pal = [(0, 0, 0)] * 16
    for m in re.finditer(r"P(\d+) = 0x([0-9A-Fa-f]{4})", open(vdp).read()):
        i, v = int(m.group(1)), int(m.group(2), 16)
        r, b, g = (v >> 4) & 7, v & 7, (v >> 8) & 7
        pal[i] = (r * 255 // 7, g * 255 // 7, b * 255 // 7)
    return pal


def punto(vram, pag, x, y):
    b = vram[pag * 0x10000 + y * 256 + x // 2]
    return b >> 4 if x % 2 == 0 else b & 15


def main(vram_f, vdp_f, sal, esc=4):
    vram = open(vram_f, "rb").read()
    pal = paleta(vdp_f)
    im = Image.new("RGB", (32 * 10 * esc, 8 * 10 * esc), (40, 40, 40))
    d = ImageDraw.Draw(im)
    for t in range(256):
        tx, ty = (t & 0x1F) * 16, 0xB0 + (t >> 5) * 8
        ox, oy = (t & 0x1F) * 10 * esc, (t >> 5) * 10 * esc
        for y in range(8):
            for x in range(16):
                c = pal[punto(vram, 1, tx + x, ty + y)]
                d.rectangle([ox + x * esc // 2, oy + 2 * esc + y * esc, ox + x * esc // 2 + esc // 2 - 1,
                             oy + 2 * esc + y * esc + esc - 1], fill=c)
        d.text((ox, oy - 1), "%02X" % t, fill=(255, 255, 0))
    im.save(sal)


if __name__ == "__main__":
    main(*sys.argv[1:4])
