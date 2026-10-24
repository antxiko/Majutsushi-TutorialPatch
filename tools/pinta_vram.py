#!/usr/bin/env python3
"""Pinta la pagina visible de un volcado de VRAM de openMSX en SCREEN 7 (512 x 212, 4 bits) con la
paleta del vdp-N.txt; cada punto 1 x 2 para que se vea en proporcion. La captura de openMSX sin
throttle va por detras de la VRAM: esto es lo que hay de verdad.

Uso: pinta_vram.py vram-N.bin vdp-N.txt salida.png [pagina]"""
import re
import sys

from PIL import Image


def main(vram_f, vdp_f, sal, pagina=None):
    vram = open(vram_f, "rb").read()
    txt = open(vdp_f).read()
    pal = [(0, 0, 0)] * 16
    for m in re.finditer(r"P(\d+) = 0x([0-9A-Fa-f]{4})", txt):
        i, v = int(m.group(1)), int(m.group(2), 16)
        pal[i] = (((v >> 4) & 7) * 255 // 7, ((v >> 8) & 7) * 255 // 7, (v & 7) * 255 // 7)
    if pagina is None:
        r2 = int(re.search(r"R2 = 0x([0-9A-Fa-f]{2})", txt).group(1), 16)
        pagina = (r2 >> 5) & 1
    pagina = int(pagina)
    im = Image.new("RGB", (512, 424))
    px = im.load()
    for y in range(212):
        for x in range(512):
            b = vram[pagina * 0x10000 + y * 256 + x // 2]
            c = pal[b >> 4 if x % 2 == 0 else b & 15]
            px[x, 2 * y] = c
            px[x, 2 * y + 1] = c
    im.save(sal)


if __name__ == "__main__":
    main(*sys.argv[1:])
