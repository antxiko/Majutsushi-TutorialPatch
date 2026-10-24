#!/usr/bin/env python3
"""Las caras de las fichas en ingles: cifras 1-9 en los 萬 (el 萬 rojo se queda, como en los juegos
occidentales) y E S W N en los vientos; 中, 發 y 白 se quedan.

Al empezar la partida p00:5746 y 570E componen las fichas en la pagina 1 de la VRAM: cada juego carga
una imagen de tiles (p00:5911 con 0xC0B9 = 1: el codigo A va en la hoja en X = (A & 0x3F) x 8 puntos
de SCREEN 7, Y = 0xB0 + (A >> 6) x 8, un tile de la ROM por codigo) y dibuja una disposicion de
codigos (p00:576A: 3 x 3 por ficha, o 5 x 2 en las tumbadas; 0xFE baja de linea, 0xFF acaba):
  imagen 8151, paletas 8039, disposicion B4F9, Y 0x00: de pie        (3 x 3, 12 x 24)
  imagen 81BE, paletas 805D, disposicion B636, Y 0x24: al reves      (3 x 3)
  imagen 8225, paletas 807F, disposicion B773, Y 0x48: tumbadas      (5 x 2, 20 x 16)
  imagen 82AA, paletas 80AB, disposicion B8D5, Y 0x78: tumbadas al otro lado
(todo en los bancos 7-8-9). Las fichas van en el orden 1-9 萬, 1-9 筒, 1-9 索, 東南西北, 白 發 中.

En cada juego: los puntos en que difieren los nueve 萬 son el numeral (lo que comparten, el 萬 y el
borde, se queda) y en los vientos, todo lo que no tiene la 白; eso se borra con lo que hay en la 白 y
se pinta el glifo de traduccion/fuentes/caras.txt girado como la ficha, centrado en el hueco y con
la tinta del numeral. Las fichas se cortan de nuevo en codigos: un codigo se reescribe si todas las
fichas que lo usan quieren lo mismo; si no, la ficha cambiada toma un codigo que la disposicion no
usa, de un grupo cuya paleta tenga sus colores.

Uso: caras.py majutsushi.rom     (escribe work/caras.png y dice que ha cambiado)"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(RAIZ, "traduccion", "fuentes", "caras.txt")
BANCOS = {0x6000: 7, 0x8000: 8, 0xA000: 9}
JUEGOS = [  # imagen, paletas, disposicion, ancho x alto en codigos, giro de la ficha (en cuartos de vuelta)
    (0x8151, 0x8039, 0xB4F9, 3, 3, 0),
    (0x81BE, 0x805D, 0xB636, 3, 3, 2),
    (0x8225, 0x807F, 0xB773, 5, 2, 1),
    (0x82AA, 0x80AB, 0xB8D5, 5, 2, 3),
]
MAN, VIENTOS, BLANCA = range(9), range(27, 31), 31
LETRAS_VIENTO = "ESWN"
BLANCO = 14                                       # la cara de la ficha


def off(d):
    v = d & 0xE000
    return BANCOS[v] * 0x2000 + d - v


def fuente():
    glifos, nombre = {}, None
    for ln in open(FUENTE, encoding="utf-8"):
        ln = ln.rstrip("\r\n")
        if ln.startswith("glifo "):
            nombre = ln[6:]
            glifos[nombre] = []
        elif nombre and ln:                           # los comentarios, solo antes del primero
            glifos[nombre].append([c == "#" for c in ln])
    return glifos


def gira(g, cuartos):
    """Gira un glifo (filas de puntos logicos) en cuartos de vuelta a la izquierda."""
    for _ in range(cuartos % 4):
        h, w = len(g), len(g[0])
        g = [[g[c][w - 1 - r] for c in range(h)] for r in range(w)]
    return g


def grupos(rom, lista, paletas):
    o, out = off(lista), []
    while rom[o] != 0xFF:
        f, p, c, n = rom[o:o + 4]
        bits = (f & 6) // 2 + 1
        dp = off(paletas) + 2 * p
        a = off(rom[dp] | rom[dp + 1] << 8)
        out.append(dict(c=c, n=n, src=off(rom[o + 4] | rom[o + 5] << 8), bits=bits,
                        pal=list(rom[a:a + (1 << bits)])))
        o += 6
    return out


def lee_tile(rom, g, k):
    s, b = g["src"] + k * 8 * g["bits"], g["bits"]
    return tuple(tuple(g["pal"][sum((rom[s + y * b + i] >> (7 - x) & 1) << i for i in range(b))]
                       for x in range(8)) for y in range(8))


def escribe_tile(rom, g, k, celda):
    s, b = g["src"] + k * 8 * g["bits"], g["bits"]
    for y, fila in enumerate(celda):
        for i in range(b):
            v = 0
            for x, c in enumerate(fila):
                if g["pal"].index(c) >> i & 1:
                    v |= 0x80 >> x
            rom[s + y * b + i] = v


def disposicion(rom, disp, w, h):
    """[(sitio en la ROM del primer codigo, [codigos])] por ficha, y el tamano."""
    o, out = off(disp), []
    while rom[o] != 0xFF:
        if rom[o] == 0xFE:
            o += 1
            continue
        out.append((o, list(rom[o:o + w * h])))
        o += w * h
    return out


def compone(cods, w, hoja):
    img = [[None] * (8 * w) for _ in range(8 * (len(cods) // w))]
    for i, k in enumerate(cods):
        for y in range(8):
            for x in range(8):
                img[(i // w) * 8 + y][(i % w) * 8 + x] = hoja[k][y][x]
    return img


def pinta(img, base, zona, glifo, tinta, nombre, vetado):
    """Borra la zona (con la base) y pinta el glifo lo mas centrado en ella que se pueda sin salir de
    la cara blanca ni tocar un punto vetado (los de codigos que usan otras fichas)."""
    for y, x in zona:
        img[y][x] = base[y][x]
    ys = [y for y, _ in zona]
    xs = [x for _, x in zona]
    alto, ancho = len(glifo), 2 * len(glifo[0])
    cy = (min(ys) + max(ys) + 1 - alto) // 2
    cx = (min(xs) + max(xs) + 1 - ancho) // 2
    puntos = [(r, 2 * c + d) for r, fila in enumerate(glifo) for c, on in enumerate(fila) if on for d in (0, 1)]

    def cabe(y0, x0):
        return all(0 <= y0 + r < len(img) and 0 <= x0 + c < len(img[0]) and base[y0 + r][x0 + c] == BLANCO
                   and (y0 + r, x0 + c) not in vetado for r, c in puntos)
    sitios = sorted(((abs(dy) + abs(dx) / 2, cy + dy, cx + dx) for dy in range(-4, 5) for dx in range(-8, 9)
                     if (cx + dx) % 2 == 0), key=lambda s: s[0])
    for _, y0, x0 in sitios:
        if cabe(y0, x0):
            for r, c in puntos:
                img[y0 + r][x0 + c] = tinta
            return
    raise SystemExit("caras: el glifo %s no cabe en su ficha" % nombre)


def aplica(rom):
    """Cambia los tiles y las disposiciones. Devuelve (zonas, informe)."""
    glifos = fuente()
    zonas, cambiados, nuevos = [], 0, 0
    for lista, paletas, disp, w, h, giro in JUEGOS:
        gs = grupos(rom, lista, paletas)
        de = {}                                   # codigo -> (grupo, indice)
        for g in gs:
            for k in range(g["n"]):
                de[g["c"] + k] = (g, k)
        hoja = {k: lee_tile(rom, g, i) for k, (g, i) in de.items()}
        fichas = disposicion(rom, disp, w, h)
        imgs = [compone(c, w, hoja) for _, c in fichas]
        base = imgs[BLANCA]
        alto, ancho = len(base), len(base[0])
        todo = [(y, x) for y in range(alto) for x in range(ancho)]
        cambia = {}
        usos = {}
        for i, (_, cods) in enumerate(fichas):
            for k in cods:
                usos.setdefault(k, set()).add(i)

        def vetado(i):
            return {((j // w) * 8 + y, (j % w) * 8 + x) for j, k in enumerate(fichas[i][1]) if usos[k] != {i}
                    for y in range(8) for x in range(8)}
        num = [(y, x) for y, x in todo if len({imgs[i][y][x] for i in MAN}) > 1]
        for n, i in enumerate(MAN):
            img = [fila[:] for fila in imgs[i]]
            tintas = [img[y][x] for y, x in num if img[y][x] != base[y][x]]
            pinta(img, base, num, gira(glifos[str(n + 1)], giro), max(set(tintas), key=tintas.count), str(n + 1),
                  vetado(i))
            cambia[i] = img
        for n, i in enumerate(VIENTOS):
            img = [fila[:] for fila in imgs[i]]
            ajenos = {((j // w) * 8 + y, (j % w) * 8 + x) for j, k in enumerate(fichas[i][1])
                      if usos[k] - set(VIENTOS) for y in range(8) for x in range(8)}
            zona = [(y, x) for y, x in todo if img[y][x] != base[y][x] and (y, x) not in ajenos]
            tintas = [img[y][x] for y, x in zona]
            pinta(img, base, zona, gira(glifos[LETRAS_VIENTO[n] + ('11' if giro % 2 else '')], giro), max(set(tintas), key=tintas.count),
                  LETRAS_VIENTO[n], vetado(i))
            cambia[i] = img
        # lo que cada codigo tiene que llevar, segun todas las fichas que lo usan
        quiere = {}
        for i, (_, cods) in enumerate(fichas):
            img = cambia.get(i, imgs[i])
            for j, k in enumerate(cods):
                celda = tuple(tuple(img[(j // w) * 8 + y][(j % w) * 8 + x] for x in range(8)) for y in range(8))
                quiere.setdefault(k, []).append((i, j, celda))
        libres = sorted(set(de) - set(quiere))
        for k, pide in sorted(quiere.items()):
            distintas = {c for _, _, c in pide}
            if len(distintas) == 1:
                celda = distintas.pop()
                if celda != hoja[k]:
                    g, idx = de[k]
                    if not {v for f in celda for v in f} <= set(g["pal"]):
                        raise SystemExit("caras: el codigo %02X no tiene esos colores" % k)
                    escribe_tile(rom, g, idx, celda)
                    zonas.append((g["src"] + idx * 8 * g["bits"], g["src"] + (idx + 1) * 8 * g["bits"]))
                    cambiados += 1
                continue
            # se queda con lo que quieren las fichas sin cambiar; las cambiadas toman codigos libres
            for i, j, celda in pide:
                if i not in cambia or celda == hoja[k]:
                    continue
                colores = {v for f in celda for v in f}
                for nk in libres:
                    g, idx = de[nk]
                    if colores <= set(g["pal"]):
                        break
                else:
                    raise SystemExit("caras: no queda codigo libre para la ficha %d (codigo %02X, de %s)" % (
                        i, k, sorted({u for u, _, _ in pide})))
                libres.remove(nk)
                escribe_tile(rom, g, idx, celda)
                zonas.append((g["src"] + idx * 8 * g["bits"], g["src"] + (idx + 1) * 8 * g["bits"]))
                sitio = fichas[i][0] + j
                rom[sitio] = nk
                zonas.append((sitio, sitio + 1))
                nuevos += 1
    return zonas, "caras de las fichas: %d codigos redibujados y %d nuevos" % (cambiados, nuevos)


def main(argv):
    from PIL import Image
    rom = bytearray(open(argv[1], "rb").read())
    print(aplica(rom)[1])
    pal = {0: (0, 0, 0), 2: (0, 160, 0), 4: (0, 0, 220), 5: (100, 100, 255), 7: (110, 110, 110),
           8: (0, 0, 255), 9: (220, 0, 0), 10: (140, 0, 0), 11: (200, 200, 0), 12: (180, 40, 40),
           13: (255, 255, 120), 14: (255, 255, 255), 15: (0, 0, 0)}
    im = Image.new("RGB", (13 * 42, 4 * 28), (60, 0, 60))
    for n, (lista, paletas, disp, w, h, giro) in enumerate(JUEGOS):
        gs = grupos(rom, lista, paletas)
        hoja = {g["c"] + k: lee_tile(rom, g, k) for g in gs for k in range(g["n"])}
        fichas = disposicion(rom, disp, w, h)
        for m, i in enumerate(list(MAN) + list(VIENTOS)):
            for y, fila in enumerate(compone(fichas[i][1], w, hoja)):
                for x, v in enumerate(fila):
                    im.putpixel((m * 42 + x, n * 28 + y), pal.get(v, (255, 0, 255)))
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(RAIZ, "work", "caras.png"))


if __name__ == "__main__":
    main(sys.argv)
