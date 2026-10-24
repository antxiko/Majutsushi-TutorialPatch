#!/usr/bin/env python3
"""El logotipo del titulo en ingles (牌の魔術師 -> TILE MAGICIAN).

El titulo lo carga p00:5CB2: la imagen p10:9502 (paletas en la tabla p10:94B2) y el mapa de
bloques p11:A453 (p00:58C9: X, Y y bloques; un tile por casilla de 8 x 8, filas de 32). El kanji ocupa las filas 7-13, columnas 5-27
(en la fila 12, columnas 27-28, va el TM); el ingles va en las filas 8-12, columnas 5-26, y el resto de
casillas del kanji se vacian. El mapa se copia opaco a otra pagina y el titulo lo barre sobre el bambu
con transparencia: el color 0 deja ver el bambu. Los tiles salen de cuatro entradas de la imagen:
  0x04-0x12  1 bit,  paleta 1 = (rojo 9, negro 15)                    desde p10:9571, 8 B por tile
  0x13-0x43  2 bits, paleta 2 = (0, azul 8, rojo 9, negro 15)          desde p10:95E9, 16 B
  0x44-0x6C  2 bits, paleta 3 = (naranja 2, azul 8, rojo 9, negro 15)  desde p10:98F9, 16 B
             (la entrada carga 57, pero 0x6D-0x7C los pisa la siguiente)
  0x6D-0x7D  3 bits, paleta 4 = (0, 1, 2, 7, 8, 9, 14, 15)             desde p10:9B89, 24 B
Un tile es de 8 x 8 puntos logicos (cada uno, dos de SCREEN 7); a 2 bits, dos bytes por fila y el
color es 2 x (bit del segundo) + (bit del primero); a 3 bits, tres bytes y 4 x tercero + 2 x segundo
+ primero; a 1 bit, un byte.

Se dibuja el texto letra a letra (la I estrecha y la M ancha; relleno rojo, rayas naranjas en la mitad de
abajo, un punto de azul y dos de negro alrededor), se corta en casillas, cada una va al grupo de tiles cuya paleta tiene sus colores (las iguales
comparten tile; las vacias, el tile 0x00 como en el original) y se escribe de nuevo el mapa entero
con el mismo RLE.

El dibujo queda en traduccion/logotipo.txt (un caracter por punto: . fondo, o naranja, A azul, R rojo,
N negro) y es lo que lee la construccion; solo `dibuja` usa PIL y la fuente Impact de Windows.

Uso: logotipo.py dibuja             (rehace traduccion/logotipo.txt)
     logotipo.py majutsushi.rom     (escribe work/logotipo.png y dice cuanto ocupa)"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTO = "TILE MAGICIAN"
FUENTE = r"C:\Windows\Fonts\impact.ttf"
DIBUJO = os.path.join(RAIZ, "traduccion", "logotipo.txt")
LETRAS = {0: ".", 2: "o", 8: "A", 9: "R", 15: "N"}
MAPA = 0xA453                        # p11
FILAS, COLS = (8, 13), (5, 27)       # casillas del texto ingles (fin excluido)
ALTO, ARRIBA = 34, 3                 # alto de las letras y linea de arriba dentro de las casillas
NARANJA = (16, 40)                   # lineas con rayas naranjas (dentro de las casillas)
PESO = {"I": 0.5, "M": 1.35, "T": 0.9, "L": 0.85, "E": 0.85}   # anchura de cada letra (1 = la normal)
GRUPOS = [  # (paleta como lista de colores, bits, primer codigo, cuantos, origen en p10)
    ([9, 15], 1, 0x04, 15, 0x9571),
    ([0, 8, 9, 15], 2, 0x13, 49, 0x95E9),
    ([2, 8, 9, 15], 2, 0x44, 41, 0x98F9),
    ([0, 1, 2, 7, 8, 9, 14, 15], 3, 0x6D, 17, 0x9B89),
]


def off10(d):
    return 10 * 0x2000 + d - 0x8000


def off11(d):
    return 11 * 0x2000 + d - 0xA000


def lee_mapa(rom):
    o = off11(MAPA)
    x, y = rom[o], rom[o + 1]
    o += 2
    pos = (y // 8) * 32 + x // 8
    celdas = {}
    while rom[o] != 0xFF:
        n = rom[o]
        if n & 0x80:
            for i in range(n & 0x7F):
                celdas[pos] = rom[o + 1 + i]
                pos += 1
            o += 1 + (n & 0x7F)
        else:
            for _ in range(n):
                celdas[pos] = rom[o + 1]
                pos += 1
            o += 2
    return (x, y), celdas, o + 1 - off11(MAPA)


def escribe_mapa(xy, celdas):
    pos = sorted(celdas)
    vals = [celdas[p] for p in pos]
    assert pos == list(range(pos[0], pos[-1] + 1))
    out = bytearray(xy)
    i = 0
    lit = []

    def suelta():
        while lit:
            t = lit[:126]                  # 0x80 | 127 seria 0xFF, el final
            out.append(0x80 | len(t))
            out.extend(t)
            del lit[:126]
    while i < len(vals):
        n = 1
        while i + n < len(vals) and vals[i + n] == vals[i] and n < 127:
            n += 1
        if n >= 3:
            suelta()
            out += bytes([n, vals[i]])
        else:
            lit.extend(vals[i:i + n])
        i += n
    suelta()
    out.append(0xFF)
    return bytes(out)


def letra(ch, ancho):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FUENTE, 160)
    im = Image.new("L", (300, 260), 0)
    ImageDraw.Draw(im).text((40, 10), ch, font=f, fill=255)
    im = im.crop(im.point(lambda v: 255 if v > 128 else 0).getbbox())
    return im.resize((ancho, ALTO), Image.LANCZOS).point(lambda v: 255 if v > 120 else 0)


def dibujo():
    """La imagen del texto (traduccion/logotipo.txt): filas de colores desde la casilla (FILAS[0], COLS[0])."""
    color = {v: k for k, v in LETRAS.items()}
    filas = [ln.rstrip("\r\n") for ln in open(DIBUJO, encoding="utf-8") if not ln.startswith("#")]
    assert len(filas) == 8 * (FILAS[1] - FILAS[0]) and all(len(f) == 8 * (COLS[1] - COLS[0]) for f in filas)
    return [[color[c] for c in f] for f in filas]


def dibuja():
    """Dibuja el texto con la fuente Impact: una lista de filas de colores."""
    ancho, alto = 8 * (COLS[1] - COLS[0]), 8 * (FILAS[1] - FILAS[0])
    hueco, blanco = 2, 6                         # entre letras y el espacio
    libre = ancho - 8 - hueco * (len(TEXTO) - 1) - blanco
    total = sum(PESO.get(c, 1) for c in TEXTO if c != " ")
    anchos = [blanco if c == " " else round(libre * PESO.get(c, 1) / total) for c in TEXTO]
    anchos[-1] += ancho - 8 - sum(anchos) - hueco * (len(TEXTO) - 1)
    m = [[0] * ancho for _ in range(alto)]
    x = 4
    for c, w in zip(TEXTO, anchos):
        if c != " ":
            im = letra(c, w)
            for y in range(ALTO):
                for dx in range(w):
                    if im.getpixel((dx, y)):
                        m[ARRIBA + y][x + dx] = 1
        x += w + hueco

    def engorda(a, n):
        b = [fila[:] for fila in a]
        for _ in range(n):
            c = [fila[:] for fila in b]
            for y in range(alto):
                for x in range(ancho):
                    if not b[y][x] and any(0 <= y + dy < alto and 0 <= x + dx < ancho and b[y + dy][x + dx]
                                           for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                        c[y][x] = 1
            b = c
        return b
    azul = engorda(m, 1)
    negro = engorda(azul, 2)
    out = []
    for y in range(alto):
        fila = []
        for x in range(ancho):
            if m[y][x]:
                raya = NARANJA[0] <= y < NARANJA[1] and x % 4 == 1 and all(
                    m[y + d][x] for d in (-2, -1, 1, 2) if 0 <= y + d < alto)
                fila.append(2 if raya else 9)
            elif azul[y][x]:
                fila.append(8)
            elif negro[y][x]:
                fila.append(15)
            else:
                fila.append(0)
        out.append(fila)
    return out


def codifica(celda, paleta, bits):
    idx = [[paleta.index(c) for c in fila] for fila in celda]
    out = bytearray()
    for fila in idx:
        for b in range(bits):
            v = 0
            for k, i in enumerate(fila):
                if i >> b & 1:
                    v |= 0x80 >> k
            out.append(v)
    return bytes(out)


def aplica(rom):
    """Cambia los tiles del logotipo y el mapa. Devuelve (zonas, informe)."""
    img = dibujo()
    xy, celdas, tam = lee_mapa(rom)
    for p, t in celdas.items():               # vacia el kanji (tiles 0x04-0x7D) y deja el TM y lo demas
        if 0x04 <= t <= 0x7D:
            celdas[p] = 0x00
    libres = [list(range(g[2], g[2] + g[3])) for g in GRUPOS]
    hechos = {}
    zonas = []
    for r in range(*FILAS):
        for c in range(*COLS):
            celda = tuple(tuple(img[(r - FILAS[0]) * 8 + y][(c - COLS[0]) * 8 + x] for x in range(8))
                          for y in range(8))
            colores = {v for fila in celda for v in fila}
            if colores == {0}:
                celdas[r * 32 + c] = 0x00
                continue
            if celda not in hechos:
                for k, (paleta, bits, ini, n, src) in enumerate(GRUPOS):
                    if colores <= set(paleta) and libres[k]:
                        cod = libres[k].pop(0)
                        o = off10(src) + (cod - ini) * 8 * bits
                        rom[o:o + 8 * bits] = codifica(celda, paleta, bits)
                        hechos[celda] = cod
                        break
                else:
                    raise SystemExit("logotipo: no hay tile para una casilla de colores %s" % sorted(colores))
            celdas[r * 32 + c] = hechos[celda]
    for paleta, bits, ini, n, src in GRUPOS:
        zonas.append((off10(src), off10(src) + n * 8 * bits))
    nuevo = escribe_mapa(xy, celdas)
    if len(nuevo) > tam:
        raise SystemExit("logotipo: el mapa ocupa %d y caben %d" % (len(nuevo), tam))
    o = off11(MAPA)
    rom[o:o + tam] = nuevo + b"\xff" * (tam - len(nuevo))
    zonas.append((o, o + tam))
    usados = [g[3] - len(l) for g, l in zip(GRUPOS, libres)]
    return zonas, "logotipo: %d tiles (%s), mapa %d de %d bytes" % (
        sum(usados), "+".join(map(str, usados)), len(nuevo), tam)


def main(argv):
    from PIL import Image
    if argv[1] == "dibuja":
        with open(DIBUJO, "w", encoding="utf-8", newline="\n") as f:
            f.write("# El logotipo en ingles para tools/logotipo.py: %s, Impact a %d lineas, filas %d-%d y\n"
                    "# columnas %d-%d del mapa p11:A453; . fondo, o naranja, A azul, R rojo, N negro.\n" % (
                        TEXTO, ALTO, FILAS[0], FILAS[1] - 1, COLS[0], COLS[1] - 1))
            for fila in dibuja():
                f.write("".join(LETRAS[v] for v in fila) + "\n")
        return
    img = dibujo()
    col = {0: (40, 90, 40), 2: (255, 146, 0), 8: (0, 0, 255), 9: (255, 0, 0), 15: (0, 0, 0)}
    alto, ancho = len(img), len(img[0])
    im = Image.new("RGB", (ancho * 2, alto))
    for y in range(alto):
        for x in range(ancho):
            im.putpixel((2 * x, y), col[img[y][x]])
            im.putpixel((2 * x + 1, y), col[img[y][x]])
    im = im.resize((ancho * 6, alto * 6), Image.NEAREST)
    im.save(os.path.join(RAIZ, "work", "logotipo.png"))
    rom = bytearray(open(argv[1], "rb").read())
    print(aplica(rom)[1])


if __name__ == "__main__":
    main(sys.argv)
