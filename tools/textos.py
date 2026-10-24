#!/usr/bin/env python3
"""Las pantallas del tutorial: de aqui sale src/datos.inc (bytes para pasmo).

Todo lo que se dibuja sale de la pagina 1 de la VRAM tal como la deja la mesa del juego
(p00:5746 y p00:5A22): el alfabeto de las filas 0xB0-0xB8, de 16 x 8 puntos, y la hoja de fichas
del jugador, de 24 x 18. Con la traduccion (tools/traduce.py) los katakana de la fila 0xC8 y los
kanji de la letra de 16 puntos son otros: el tutorial ya no los usa, y escribe los menus y las
llamadas como salen ahora en el juego.

Formato (las X van en unidades de 2 puntos, como en las rutinas del VDP del cartucho):
    Y, X, elementos..., 0xFE      un renglon; Y = 0xFF acaba la pantalla y 0xFD tras ella, el tutorial
    0x00                          espacio (8)
    0x01-0x7F                     letra: fila * 32 + columna en la rejilla de 0xB0 (avanza 8)
    0x80                          hueco entre grupos de fichas (avanza 6)
    0x81-0xB7                     la ficha (byte - 0x80): palo * 16 + numero (avanza 12)
    0xC0, lo, hi                  el texto en kanji del banco 0 que empieza en esa direccion (el
                                  codigo lo sabe dibujar; las pantallas ya no lo usan)

Uso: textos.py src/datos.inc
"""
import sys

# la rejilla de letras de la pagina 1: fila 0 (Y 0xB0) espacio, 0-9, A-I; fila 1 (Y 0xB8) J-Z,
# (c), -
FILA0 = " 0123456789ABCDEFGHI"
FILA1 = "JKLMNOPQRSTUVWXYZ@-"

# las fichas: palo 0 caracteres, 1 circulos, 2 bambues, 3 honores (1-4 vientos E S W N,
# 5 blanco, 6 verde, 7 rojo)
def F(nombre):
    if nombre in VIENTOS:
        return 0x30 + VIENTOS[nombre]
    palo = {"m": 0, "p": 1, "s": 2}[nombre[0]]
    return palo * 16 + int(nombre[1])


VIENTOS = {"E": 1, "S": 2, "W": 3, "N": 4, "BL": 5, "VE": 6, "RO": 7}

def letra(c):
    if c in FILA0:
        return FILA0.index(c)
    if c in FILA1:
        return 32 + FILA1.index(c)
    raise SystemExit("la letra %r no esta en la rejilla del cartucho" % c)


# los caracteres del texto empaquetado: el codigo de 5 bits es su posicion + 1 (0 acaba el renglon)
CINCO = " ABCDEFGHIKLMNOPQRSTUVWXY-0125"   # sin J ni Z, que no salen


def texto(y, s, x=None):
    """Un renglon de texto; sin X va centrado. Las letras van de tres en tres en 16 bits
    (0aaaaabb bbbccccc)."""
    if x is None:
        x = (256 - 8 * len(s)) // 2
    assert 0 <= x and x + 8 * len(s) <= 256, "el renglon %r se sale de la pantalla" % s
    cod = [CINCO.index(c) + 1 for c in s] + [0]
    while len(cod) % 3:
        cod.append(0)
    out = [y, x]
    for i in range(0, len(cod), 3):
        w = cod[i] << 10 | cod[i + 1] << 5 | cod[i + 2]
        out += [w >> 8, w & 0xFF]
    return out


def fichas(y, x, grupos):
    """Grupos de fichas separados por un hueco; grupos = "m1 m2 m3 | p4 p5 p6"."""
    assert x + ancho_fichas(grupos) <= 256, "las fichas %r se salen de la pantalla" % grupos
    out = [y, x]
    for i, g in enumerate(grupos.split("|")):
        if i:
            out.append(0x80)
        out += [0x80 + F(t) for t in g.split()]
    return out + [0xFE]


def ancho_fichas(grupos):
    g = grupos.split("|")
    return sum(12 * len(x.split()) for x in g) + 6 * (len(g) - 1)


def centradas(y, grupos):
    return fichas(y, (256 - ancho_fichas(grupos)) // 2, grupos)


FIN = [0xFF]

PANTALLAS = [
    # 1
    texto(8, "HOW TO PLAY")
    + texto(30, "YOU PLAY AGAINST THREE RIVALS")
    + centradas(70, "m2 m3 m4 p1 p1 p5 p6 p7 s3 s4 s8 E E | s5")
    + texto(104, "DRAW ONE THEN THROW ONE")
    + texto(130, "LEFT AND RIGHT PICK THE TILE")
    + texto(148, "SPACE THROWS IT")
    + FIN,
    # 2
    texto(8, "THE TILES")
    + texto(30, "THREE SUITS ONE TO NINE")
    + centradas(56, "m1 m2 m3 m4 m5 m6 m7 m8 m9")
    + centradas(86, "p1 p2 p3 p4 p5 p6 p7 p8 p9")
    + centradas(116, "s1 s2 s3 s4 s5 s6 s7 s8 s9")
    + texto(152, "FOUR OF EACH TILE")
    + FIN,
    # 3
    texto(8, "WINDS AND DRAGONS")
    + fichas(36, 40, "E") + texto(41, "EAST", 56)
    + fichas(64, 40, "S") + texto(69, "SOUTH", 56)
    + fichas(92, 40, "W") + texto(97, "WEST", 56)
    + fichas(120, 40, "N") + texto(125, "NORTH", 56)
    + fichas(36, 140, "BL") + texto(41, "WHITE", 156)
    + fichas(64, 140, "VE") + texto(69, "GREEN", 156)
    + fichas(92, 140, "RO") + texto(97, "RED", 156)
    + texto(170, "THEY NEVER MAKE A RUN")
    + FIN,
    # 4
    texto(8, "THE GOAL")
    + texto(30, "FOUR SETS AND ONE PAIR")
    + centradas(60, "m1 m2 m3 | s4 s5 s6")
    + centradas(90, "p7 p7 p7 | E E E")
    + centradas(120, "m9 m9")
    + texto(152, "FOURTEEN TILES IN ALL")
    + texto(170, "AND AT LEAST ONE YAKU")
    + FIN,
    # 5
    texto(8, "THE SETS")
    + texto(30, "A RUN - THREE IN ORDER ONE SUIT")
    + centradas(44, "p3 p4 p5")
    + texto(78, "A TRIPLET - THREE THE SAME")
    + centradas(92, "s8 s8 s8")
    + texto(126, "A PAIR - TWO THE SAME")
    + centradas(140, "RO RO")
    + FIN,
    # 6
    texto(8, "CALLING")
    + texto(26, "WHEN A RIVAL THROWS")
    + texto(53, "PON", 16) + fichas(48, 56, "s2 s2 | s2") + texto(53, "A TRIPLET", 130)
    + texto(83, "CHI", 16) + fichas(78, 56, "m3 m4 | m5") + texto(83, "A RUN", 130)
    + texto(113, "KAN", 16) + fichas(108, 56, "N N N | N") + texto(113, "FOUR", 130)
    + texto(143, "RON", 16) + fichas(138, 56, "p9") + texto(143, "YOU WIN WITH IT", 80)
    + texto(176, "A BOX OPENS - PICK WITH SPACE")
    + FIN,
    # 7
    texto(8, "RIICHI AND TSUMO")
    + texto(32, "RIICHI", 16) + texto(32, "CLOSED AND READY", 80)
    + centradas(48, "m1 m2 m3 p4 p5 p6 s7 s8 s9 E E m4 m5 | m6")
    + texto(78, "BET 1000 - ONE TILE TO WIN")
    + texto(116, "TSUMO", 16) + texto(116, "WIN ON YOUR OWN DRAW", 72)
    + centradas(132, "m6")
    + FIN,
    # 8
    texto(8, "THE MENUS")
    + texto(34, "STYLE - HOW EACH RIVAL PLAYS")
    + texto(52, "RIVALS - PICK THREE")
    + texto(70, "RULES - OPTIONAL RULES")
    + texto(88, "SCREEN - MOVE THE PICTURE")
    + texto(106, "DONE - START")
    + texto(146, "IN PRACTICE PRESS DOWN ON YOUR")
    + texto(164, "TURN - OPEN SHOWS THEIR HANDS")
    + FIN,
    # 9
    texto(8, "THE RIVALS LEARN")
    + texto(30, "EACH HAS SEVEN BARS OF STYLE")
    + texto(48, "AND THEY LEARN FROM YOUR WINS")
    + texto(84, "MUSIC")
    + texto(106, "ON YOUR TURN F1 STOPS IT")
    + texto(124, "F2 TO F5 CHANGE IT")
    + texto(160, "F1 ON THE FIRST MENU")
    + texto(178, "BRINGS THIS BACK")
    + FIN,
]


def bytes_tutorial():
    out = []
    for p in PANTALLAS:
        out += p
    out.append(0xFD)
    for b in out:
        assert 0 <= b <= 0xFF
    return bytes(out)


def main(argv):
    datos = bytes_tutorial()
    tabla = bytes(letra(c) for c in CINCO)
    assert len(tabla) <= 31
    with open(argv[1], "w", encoding="ascii") as s:
        s.write("tabla5:\t\t; el codigo de 5 bits - 1 -> la letra de la rejilla\n\tdefb "
                + ",".join("0%02Xh" % x for x in tabla) + "\n")
        s.write("; lo escribe tools/textos.py: %d pantallas, %d bytes\n" % (len(PANTALLAS), len(datos)))
        s.write("diapos:\n")
        for i in range(0, len(datos), 16):
            s.write("\tdefb " + ",".join("0%02Xh" % x for x in datos[i:i + 16]) + "\n")
    print("%d pantallas, %d bytes" % (len(PANTALLAS), len(datos)))


if __name__ == "__main__":
    main(sys.argv)
