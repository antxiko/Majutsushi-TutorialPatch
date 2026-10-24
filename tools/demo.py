#!/usr/bin/env python3
"""La presentacion de la demo en ingles: el titulo ("X代表") y la frase de cada rival.

La secuencia de las estrellas (p04:B479) dibuja por cada rival una lista de tiles de la tabla de
p04:B535: el nombre (Y 0x30), dos filas de 8 tiles con el titulo (Y 0x40 y 0x48: cuatro tiles del
kanji de cada uno y los cuatro de 代表, comunes) y la frase (Y 0x58). Los tiles los carga la imagen
de p00:56DF (lista 0x8F87, bancos 10-11), a 1 bit por punto y 8 bytes por tile:
  0x92-0xCF desde p10:90FA y 0x33-0x3A desde p10:92DA (los dos ultimos se solapan con 0xCE-0xCF),
  todos con la paleta 1 (amarillo): 68 tiles para los titulos;
  0xD6-0xFD desde p10:931A y 0x1C-0x1D desde p10:945A, con la paleta 2 (azul): las frases.

El titulo va con letras de 8 x 16 (el alfabeto Konami 8 x 8 al doble de alto, un tile arriba y otro
abajo), compartidas por los ocho; la frase, con tiles de dos letras estrechas (3 x 7). Las ocho
listas se escriben de nuevo, seguidas, en el sitio de las viejas, y se corrige la tabla.
La frase de Moai son garabatos (0x1C) y una interrogacion: se queda."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traduce  # noqa: E402

TABLA = 0xB535                    # p04: ocho palabras
BASE10 = 10 * 0x2000 - 0x8000     # p10 visto en 0x8000
AMARILLO = 0x90FA                 # 68 tiles: los 62 de 0x92 y los 8 de 0x33 (solapados dos)
AZUL = 0x931A                     # 42 tiles: 40 de 0xD6 y 2 de 0x1C
TITULOS = ["KNIGHT", "THIEF", "ISLANDER", "VILLAIN", "PERVERT", "DEMON", "S. POLE", "WOMAN"]
FRASES = ["I'LL TAKE YOU ON", "BRING IT ON!!", None, "YOU WON'T LIVE.", "WHIP OF LOVE!",
          "HEH HEH HEH!!", "I READ THE TILES", "GO EASY ON ME♡"]
MOAI = (0x1C, 0x1D)               # los tiles de la frase de Moai, que no se tocan


def codigo_amarillo(s):
    return 0x92 + s if s < 60 else 0x33 + (s - 60)


def codigo_azul(s):
    return 0xD6 + s if s < 40 else 0x1C + (s - 40)


def tiles_letra(c):
    """Arriba y abajo (8 + 8 bytes) de una letra de 8 x 16."""
    filas = traduce.glifo(traduce.ANCHA, c)
    out = bytearray()
    for f in filas:
        v = sum(0x80 >> k for k, p in enumerate(f) if p == "#")
        out += bytes([v, v])
    return bytes(out[:8]), bytes(out[8:])


def tile_par(par):
    """Dos letras estrechas en un tile de 8 x 8: columnas 0-2 y 4-6, fila 0 vacia."""
    out = bytearray([0])
    for y in range(7):
        v = 0
        for i, c in enumerate(par.ljust(2)):
            f = traduce.glifo(traduce.ESTRECHA, c)[y]
            for k in range(3):
                if f[k] == "#":
                    v |= 0x80 >> (4 * i + k)
        out.append(v)
    return bytes(out)


def pares(texto, desplaza):
    t = " " * desplaza + texto
    return [t[i:i + 2].ljust(2) for i in range(0, len(t), 2)]


def lee_listas(rom):
    """Las ocho listas: [(direccion, [(x, y, tiles)])] y el final de la ultima."""
    out = []
    fin = 0
    for k in range(8):
        d = rom[traduce.dir_rom("4:%04X" % (TABLA + 2 * k))] | rom[traduce.dir_rom("4:%04X" % (TABLA + 2 * k)) + 1] << 8
        o = traduce.dir_rom("4:%04X" % d)
        filas = []
        x, y = rom[o], rom[o + 1]
        o += 2
        t = []
        while True:
            b = rom[o]
            o += 1
            if b in (0xFE, 0xFF):
                filas.append((x, y, t))
                if b == 0xFF:
                    break
                x, y, t = rom[o], rom[o + 1], []
                o += 2
            else:
                t.append(b)
        out.append((d, filas))
        fin = max(fin, o)
    return out, fin


def aplica(rom):
    """Cambia los tiles y las listas. Devuelve (zonas, informe)."""
    listas, fin = lee_listas(rom)
    ini = traduce.dir_rom("4:B545")
    # los titulos: un juego de letras de 8 x 16 y un tile vacio
    letras = {}
    tiles_t = [bytes(8)]                 # el 0: vacio
    for t in TITULOS:
        for c in t:
            if c != " " and c not in letras:
                letras[c] = len(tiles_t)
                tiles_t += list(tiles_letra(c))
    if len(tiles_t) > 68:
        raise SystemExit("demo: %d tiles de titulo y caben 68" % len(tiles_t))
    # las frases: tiles de dos letras, con el desplazamiento que menos tiles nuevos pide
    tiles_f = {}
    filas_f = []
    for f in FRASES:
        if f is None:
            filas_f.append(None)
            continue
        mejor = None
        for d in (0, 1):
            p = pares(f, d)
            if len(p) > 8:
                continue
            nuevos = len(set(p) - set(tiles_f))
            if mejor is None or nuevos < mejor[0]:
                mejor = (nuevos, p)
        for p in mejor[1]:
            tiles_f.setdefault(p, len(tiles_f))
        filas_f.append(mejor[1])
    if len(tiles_f) > 40:
        raise SystemExit("demo: %d tiles de frase y caben 40" % len(tiles_f))
    # los dibujos
    zonas = []
    o = BASE10 + AMARILLO
    for s, b in enumerate(tiles_t):
        rom[o + 8 * s:o + 8 * s + 8] = b
    zonas.append((o, o + 8 * 68))
    o = BASE10 + AZUL
    for p, s in tiles_f.items():
        rom[o + 8 * s:o + 8 * s + 8] = tile_par(p)
    zonas.append((o, o + 8 * 40))
    # las listas
    datos = bytearray()
    nuevas = []
    for k, (d, filas) in enumerate(listas):
        nuevas.append(0xB545 + len(datos))
        titulo = TITULOS[k]
        izq = (8 - len(titulo)) // 2
        arriba = [0] * 8
        abajo = [0] * 8
        for i, c in enumerate(titulo):
            if c != " ":
                arriba[izq + i] = letras[c]
                abajo[izq + i] = letras[c] + 1
        primero = True
        for x, y, t in filas:
            if y in (0x40, 0x48):
                # el recuadro se ha borrado antes (p04:B493): solo las letras, con la X movida
                fila = arriba if y == 0x40 else abajo
                t = [codigo_amarillo(s) for s in fila[izq:izq + len(titulo)]]
                x += 8 * izq
            elif y == 0x58 and filas_f[k] is not None:
                t = [codigo_azul(tiles_f[p]) for p in filas_f[k]]
            if not primero:
                datos.append(0xFE)
            datos += bytes([x, y] + t)
            primero = False
        datos.append(0xFF)
    if ini + len(datos) > fin:
        raise SystemExit("demo: las listas no caben (%d de %d)" % (len(datos), fin - ini))
    rom[ini:fin] = bytes(datos) + b"\xff" * (fin - ini - len(datos))
    zonas.append((ini, fin))
    for k, d in enumerate(nuevas):
        t = traduce.dir_rom("4:%04X" % (TABLA + 2 * k))
        rom[t] = d & 0xFF
        rom[t + 1] = d >> 8
    zonas.append((traduce.dir_rom("4:B535"), traduce.dir_rom("4:B545")))
    return zonas, "presentacion: %d tiles de titulo de 68, %d de frase de 40, listas %d de %d bytes" % (
        len(tiles_t), len(tiles_f), len(datos), fin - ini)


if __name__ == "__main__":
    rom = bytearray(open(sys.argv[1], "rb").read())
    print(aplica(rom)[1])
