#!/usr/bin/env python3
"""Las imagenes de la web (docs/imagenes) a partir de las capturas de openMSX en work/:

  work/w_*_jp, work/w_*_en   tools/lanza_tiles.ps1 con las mismas teclas en la ROM original y en la
                             parcheada (menu del modo y de ajustes, reglas, estilo): foto-*.png
  work/w_partida             la parcheada, partida con espacio cada 2 s y TIL_VOZ=1: sNb.png y voz*.png
  work/tuto_en               tools/omsx_tuto.tcl con la parcheada: menu, paginas 1-9 y vuelta

Todas las capturas se hacen con el throttle puesto (sin el, la captura va por detras de la VRAM).

Uso: imagenes_web.py"""
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
W = RAIZ / "work"
DOCS = RAIZ / "docs" / "imagenes"

PARES = [                      # nombre, carpeta (sin _jp/_en), captura
    ("modo", "w_menus", "foto-22.5.png"),
    ("ajustes", "w_menus", "foto-27.5.png"),
    ("reglas", "w_reglas", "foto-31.5.png"),
    ("estilo", "w_estilo", "foto-33.5.png"),
]
PARTIDA = [                    # nombre, captura de work/w_partida
    ("sorteo", "s20b.png"),
    ("llamada", "s25b.png"),
    ("yaku", "s33b.png"),
    ("aborto", "s37b.png"),
    ("pon", "voz3-1.png"),
]


def guarda(im, nombre):
    im.convert("RGB").save(DOCS / nombre, optimize=True)


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    for nombre, carpeta, foto in PARES:
        for idioma in ("jp", "en"):
            guarda(Image.open(W / ("%s_%s" % (carpeta, idioma)) / foto), "%s_%s.png" % (nombre, idioma))
    for nombre, foto in PARTIDA:
        guarda(Image.open(W / "w_partida" / foto), "partida_%s.png" % nombre)
    t = W / "tuto_en"
    for i in range(1, 10):
        guarda(Image.open(t / ("pagina%d.png" % i)), "tutorial_%d.png" % i)
    cuadros = [Image.open(t / f).convert("RGB").resize((640, 480), Image.LANCZOS)
               for f in ["menu.png"] + ["pagina%d.png" % i for i in range(1, 10)] + ["vuelta.png"]]
    cuadros = [c.quantize(colors=64, method=Image.MEDIANCUT) for c in cuadros]
    cuadros[0].save(DOCS / "tutorial.gif", save_all=True, append_images=cuadros[1:], duration=2000,
                    loop=0, optimize=True)
    print("->", DOCS)


if __name__ == "__main__":
    main()
