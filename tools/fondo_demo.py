#!/usr/bin/env python3
"""El fondo de la presentacion en ingles: el 麻雀 grande del puzle pasa a MAHJONG.

p04:B0EF llama a p00:5810, que dibuja el mapa p15:AAA0 (el formato de p00:58C5: X, Y y bloques; un
tile por casilla de 8 x 8, filas de 32) con los tiles que carga p00:56C6 (lista p10:806C, paletas en
la tabla p10:8000). El puzle son tiles de 0x0E-0x40 (colores 3 y 6 y el negro 15 de los huecos) y el
kanji, casillas que mezclan el puzle con el marron (12) y el borde oliva (11):
  0x41-0x65  1 bit,  paleta 8   = (11, 12)                           desde p10:8453, 8 B por tile
  0x67-0x6E  3 bits, paleta 10  = (3, 6, 10, 11, 12, 13, 14, 15)     desde p10:858B, 24 B
  0x6F-0xF9  2 bits, paleta 11  = (3, 6, 11, 12)                     desde p10:864B, 16 B
Debajo del kanji no hay puzle: se rellenan las casillas del kanji (las que tienen 11 o 12) y las de
la franja del texto con tiles de puzle que ya existen (0x00 y 0x0E-0x3F), escogidos para que cada
pareja de vecinas case punto a punto en el borde como alguna pareja del mapa original (en la franja
del texto, sin huecos negros). Encima va el texto de traduccion/fondo_demo.txt (. sin texto, o
borde oliva, M marron); las casillas que cambian se cortan, se reparten por colores entre los tres
grupos (las iguales comparten tile) y el mapa se escribe de nuevo con el mismo RLE.

Uso: fondo_demo.py dibuja             (rehace traduccion/fondo_demo.txt con la fuente Impact)
     fondo_demo.py majutsushi.rom     (escribe work/fondo_demo.png y dice cuanto ocupa)"""
import os
import random
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTO = "MAHJONG"
FUENTE = r"C:\Windows\Fonts\impact.ttf"
DIBUJO = os.path.join(RAIZ, "traduccion", "fondo_demo.txt")
LETRAS = {None: ".", 11: "o", 12: "M"}
LISTA, PALETAS, MAPA = 0x806C, 0x8000, 0xAAA0     # p10, p10, p15
FILAS, COLS = (10, 17), (4, 27)                   # la franja del texto (fin excluido)
BORDE = 2                                         # puntos de oliva alrededor
GRUPOS = [  # (paleta, bits, primer codigo, cuantos, origen en p10)
    ([11, 12], 1, 0x41, 37, 0x8453),
    ([3, 6, 11, 12], 2, 0x6F, 139, 0x864B),
    ([3, 6, 10, 11, 12, 13, 14, 15], 3, 0x67, 8, 0x858B),
]
SEMILLA = 1
HUECOS = ({r * 32 + c for r in range(7, 13) for c in range(4, 12)} |    # debajo del cuadro de texto
          {r * 32 + c for r in range(17, 21) for c in range(4, 10)})    # y del primer retrato: el relleno
                                                  # prefiere ahi el hueco 0x00, que va en tiradas
PASOS = 200000                                    # tope del backtracking


def off10(d):
    return 10 * 0x2000 + d - 0x8000


def off15(d):
    return 15 * 0x2000 + d - 0xA000


def lee_tiles(rom):
    """Los tiles de la lista p10:806C: {codigo: 8 filas de 8 colores}. El 0x00 no se carga: negro."""
    t = {0: [[15] * 8 for _ in range(8)]}
    o = off10(LISTA)
    while rom[o] != 0xFF:
        f, p, c, n = rom[o:o + 4]
        src = rom[o + 4] | rom[o + 5] << 8
        bits = (f & 6) // 2 + 1
        dp = off10(PALETAS) + 2 * p
        a = off10(rom[dp] | rom[dp + 1] << 8)
        pal = rom[a:a + (1 << bits)]
        for k in range(n):
            s = off10(src) + k * 8 * bits
            t[c + k] = [[pal[sum((rom[s + y * bits + b] >> (7 - x) & 1) << b for b in range(bits))]
                         for x in range(8)] for y in range(8)]
        o += 6
    return t


def lee_mapa(rom):
    o = off15(MAPA)
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
    return (x, y), celdas, o + 1 - off15(MAPA)


def escribe_mapa(xy, celdas):
    pos = sorted(celdas)
    vals = [celdas[p] for p in pos]
    assert pos == list(range(pos[0], pos[-1] + 1))
    out = bytearray(xy)
    lit = []

    def suelta():
        while lit:
            t = lit[:126]                  # 0x80 | 127 seria 0xFF, el final
            out.append(0x80 | len(t))
            out.extend(t)
            del lit[:126]
    i = 0
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


def colores(cel):
    return {v for fila in cel for v in fila}


def rellena(t, celdas):
    """Pone tiles de puzle en las casillas del kanji y de la franja del texto (backtracking)."""
    def der(k): return tuple(f[7] for f in t[k])
    def izq(k): return tuple(f[0] for f in t[k])
    def aba(k): return tuple(t[k][7])
    def arr(k): return tuple(t[k][0])
    sh, sv, paridad = set(), set(), {}
    for pos, k in celdas.items():
        r, c = divmod(pos, 32)
        if k not in t or r > 25:
            continue
        if c < 31 and celdas.get(pos + 1) in t:
            sh.add((der(k), izq(celdas[pos + 1])))
        if r < 25 and celdas.get(pos + 32) in t:
            sv.add((aba(k), arr(celdas[pos + 32])))
        if 4 <= r <= 24:
            paridad.setdefault(k, set()).add((r % 2, c % 2))
    puzle = [k for k in [0] + list(range(0x0E, 0x40)) if colores(t[k]) <= {3, 6, 15}]
    franja = {r * 32 + c for r in range(*FILAS) for c in range(*COLS)}
    libres = sorted(p for p, k in celdas.items()
                    if 4 <= p // 32 <= 24 and (p in franja or colores(t[k]) & {11, 12}))
    asig = {p: k for p, k in celdas.items() if p not in libres}
    rnd = random.Random(SEMILLA)
    dom = {}
    for p in libres:
        op = [k for k in puzle if (p // 32 % 2, p % 32 % 2) in paridad.get(k, ())
              and not (p in franja and 15 in colores(t[k]))]
        rnd.shuffle(op)
        op.sort(key=lambda k: 15 in colores(t[k]))      # mejor piezas enteras que huecos
        if p in HUECOS and 0 in op:               # salvo donde se quieren tiradas de 0x00
            op.remove(0)
            op.insert(0, 0)
        dom[p] = op

    def casa(p, k):
        for q, izquierda in ((p - 1, True), (p + 1, False)):
            if q in asig and ((der(asig[q]), izq(k)) if izquierda else (der(k), izq(asig[q]))) not in sh:
                return False
        for q, arriba in ((p - 32, True), (p + 32, False)):
            if q in asig and ((aba(asig[q]), arr(k)) if arriba else (aba(k), arr(asig[q]))) not in sv:
                return False
        return True
    pila = [0]
    pasos = 0
    while pila:                                     # backtracking sin recursion
        pasos += 1
        if pasos > PASOS:
            break
        i = len(pila) - 1
        if i == len(libres):
            return asig
        p = libres[i]
        asig.pop(p, None)
        j = pila[-1]
        while j < len(dom[p]) and not casa(p, dom[p][j]):
            j += 1
        if j < len(dom[p]):
            asig[p] = dom[p][j]
            pila[-1] = j + 1
            pila.append(0)
        else:
            pila.pop()
    raise SystemExit("fondo_demo: el puzle no se puede rellenar")


def dibujo():
    """El texto (traduccion/fondo_demo.txt): filas de colores (None = puzle) desde (FILAS[0], COLS[0])."""
    color = {v: k for k, v in LETRAS.items()}
    filas = [ln.rstrip("\r\n") for ln in open(DIBUJO, encoding="utf-8") if not ln.startswith("#")]
    assert len(filas) == 8 * (FILAS[1] - FILAS[0]) and all(len(f) == 8 * (COLS[1] - COLS[0]) for f in filas)
    return [[color[c] for c in f] for f in filas]


def dibuja():
    """Dibuja el texto con la fuente Impact: marron con BORDE puntos de oliva."""
    from PIL import Image, ImageDraw, ImageFont
    ancho, alto = 8 * (COLS[1] - COLS[0]), 8 * (FILAS[1] - FILAS[0])
    f = ImageFont.truetype(FUENTE, 200)
    im = Image.new("L", (1600, 300), 0)
    ImageDraw.Draw(im).text((40, 10), TEXTO, font=f, fill=255)
    im = im.crop(im.point(lambda v: 255 if v > 128 else 0).getbbox())
    mw, mh = ancho - 2 * BORDE, alto - 2 * BORDE
    im = im.resize((mw, mh), Image.LANCZOS).point(lambda v: 255 if v > 120 else 0)
    m = [[0] * ancho for _ in range(alto)]
    for y in range(mh):
        for x in range(mw):
            if im.getpixel((x, y)):
                m[BORDE + y][BORDE + x] = 1
    b = [fila[:] for fila in m]
    for _ in range(BORDE):
        c = [fila[:] for fila in b]
        for y in range(alto):
            for x in range(ancho):
                if not b[y][x] and any(0 <= y + dy < alto and 0 <= x + dx < ancho and b[y + dy][x + dx]
                                       for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                    c[y][x] = 1
        b = c
    return [[12 if m[y][x] else 11 if b[y][x] else None for x in range(ancho)] for y in range(alto)]


def codifica(celda, paleta, bits):
    out = bytearray()
    for fila in celda:
        idx = [paleta.index(c) for c in fila]
        for b in range(bits):
            v = 0
            for k, i in enumerate(idx):
                if i >> b & 1:
                    v |= 0x80 >> k
            out.append(v)
    return bytes(out)


def pantalla(rom):
    """(t, celdas nuevas sin texto, imagen de la franja con el texto, xy, tam)."""
    t = lee_tiles(rom)
    xy, celdas, tam = lee_mapa(rom)
    asig = rellena(t, celdas)
    texto = dibujo()
    return t, asig, texto, xy, tam


def aplica(rom):
    """Cambia los tiles del kanji y el mapa. Devuelve (zonas, informe)."""
    t, asig, texto, xy, tam = pantalla(rom)
    libres = [list(range(g[2], g[2] + g[3])) for g in GRUPOS]
    hechos = {}
    for r in range(*FILAS):
        for c in range(*COLS):
            p = r * 32 + c
            fondo = t[asig[p]]
            celda = tuple(tuple(texto[(r - FILAS[0]) * 8 + y][(c - COLS[0]) * 8 + x] or fondo[y][x]
                                for x in range(8)) for y in range(8))
            if celda == tuple(map(tuple, fondo)):
                continue
            if celda not in hechos:
                for k, (paleta, bits, ini, n, src) in enumerate(GRUPOS):
                    if colores(celda) <= set(paleta) and libres[k]:
                        cod = libres[k].pop(0)
                        o = off10(src) + (cod - ini) * 8 * bits
                        rom[o:o + 8 * bits] = codifica(celda, paleta, bits)
                        hechos[celda] = cod
                        break
                else:
                    raise SystemExit("fondo_demo: no hay tile para una casilla de colores %s" %
                                     sorted(colores(celda)))
            asig[p] = hechos[celda]
    nuevo = escribe_mapa(xy, {p: asig[p] for p in lee_mapa(rom)[1]})
    if len(nuevo) > tam:
        raise SystemExit("fondo_demo: el mapa ocupa %d y caben %d" % (len(nuevo), tam))
    o = off15(MAPA)
    rom[o:o + tam] = nuevo + b"\xff" * (tam - len(nuevo))
    zonas = [(off10(g[4]), off10(g[4]) + g[3] * 8 * g[1]) for g in GRUPOS] + [(o, o + tam)]
    usados = [g[3] - len(lo) for g, lo in zip(GRUPOS, libres)]
    return zonas, "fondo de la demo: %d tiles (%s), mapa %d de %d bytes" % (
        sum(usados), "+".join(map(str, usados)), len(nuevo), tam)


def main(argv):
    if argv[1] == "dibuja":
        with open(DIBUJO, "w", encoding="utf-8", newline="\n") as f:
            f.write("# El fondo de la demo en ingles para tools/fondo_demo.py: %s, Impact, filas %d-%d y\n"
                    "# columnas %d-%d del mapa p15:AAA0; . puzle, o borde oliva, M marron.\n" % (
                        TEXTO, FILAS[0], FILAS[1] - 1, COLS[0], COLS[1] - 1))
            for fila in dibuja():
                f.write("".join(LETRAS[v] for v in fila) + "\n")
        return
    from PIL import Image
    rom = bytearray(open(argv[1], "rb").read())
    print(aplica(rom)[1])
    t = lee_tiles(rom)
    _, celdas, _ = lee_mapa(rom)
    pal = {3: (146, 146, 182), 6: (109, 109, 146), 10: (146, 36, 72), 11: (146, 146, 0), 12: (146, 72, 72),
           13: (255, 255, 109), 14: (255, 255, 255), 15: (0, 0, 0)}
    im = Image.new("RGB", (256, 216), (60, 0, 60))
    for pos, k in celdas.items():
        r, c = divmod(pos, 32)
        if 4 <= r <= 24 and k in t:
            for y in range(8):
                for x in range(8):
                    im.putpixel((c * 8 + x, r * 8 + y), pal.get(t[k][y][x], (255, 0, 255)))
    im.resize((768, 648), Image.NEAREST).save(os.path.join(RAIZ, "work", "fondo_demo.png"))


if __name__ == "__main__":
    main(sys.argv)
