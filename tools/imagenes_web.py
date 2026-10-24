#!/usr/bin/env python3
"""Las imagenes de la web (docs/imagenes) a partir de las capturas de openMSX en work/:

  work/w_*_jp, work/w_*_en   tools/lanza_tiles.ps1 con las mismas teclas en la ROM original y en la
                             parcheada (menu del modo y de ajustes, reglas, estilo): foto-*.png
  work/w_titulo_*, w_demo_jp, w_fondo_en, w_caras_*   el titulo, la presentacion y las fichas (foto-*.png)
  work/w_partida_en          la parcheada, partida con espacio cada 2 s desde el segundo 20 y TIL_VOZ=1:
                             sNb.png (N, el numero de la lista en tiles.txt) y voz*.png
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
OTROS = [                      # nombre, carpeta japonesa, carpeta inglesa, captura
    ("titulo", "w_titulo_jp", "w_titulo_en", "foto-19.5.png"),
    ("demo", "w_demo_jp", "w_fondo_en", "foto-34.5.png"),
    ("fichas", "w_caras_jp", "w_caras_en", "foto-85.png"),
]
PARTIDA = [                    # nombre, captura de work/w_partida_en
    ("sorteo", "s20b.png"),    # T 8FFF
    ("llamada", "s25b.png"),   # S 98E3
    ("yaku", "s31b.png"),      # T 663B
    ("aborto", "s32b.png"),    # T B7CE
    ("pon", "voz2-3.png"),
]


def guarda(im, nombre):
    im.convert("RGB").save(DOCS / nombre, optimize=True)


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    for nombre, carpeta, foto in PARES:
        for idioma in ("jp", "en"):
            guarda(Image.open(W / ("%s_%s" % (carpeta, idioma)) / foto), "%s_%s.png" % (nombre, idioma))
    for nombre, jp, en, foto in OTROS:
        guarda(Image.open(W / jp / foto), "%s_jp.png" % nombre)
        guarda(Image.open(W / en / foto), "%s_en.png" % nombre)
    for nombre, foto in PARTIDA:
        guarda(Image.open(W / "w_partida_en" / foto), "partida_%s.png" % nombre)
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
