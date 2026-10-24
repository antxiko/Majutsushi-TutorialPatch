#!/usr/bin/env python3
"""La fuente y las paginas del tutorial: de aqui sale src/datos.inc (bytes para pasmo).

La fuente son glifos de 8 x 8 a un bit por punto (el bit 7 es el de la izquierda), como los
que dibuja p00:52A3 del cartucho. Las paginas van codificadas con el numero de glifo + 1;
0 es un espacio, 0xFE baja de linea, 0xFF acaba la pagina y 0xFD acaba el tutorial.

Uso: textos.py src/datos.inc
"""
import sys

# 5 x 7 dentro de 8 x 8: columnas 1-5, filas 0-6
G = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
}

PAGINAS = [
    'HAI NO MAJUTSUSHI - TUTORIAL||RIICHI MAHJONG FOR FOUR. YOU|ARE THE PLAYER AT THE BOTTOM.||LEFT AND RIGHT CHOOSE THE|TILE, SPACE THROWS IT.||TO WIN: FOUR GROUPS AND A PAIR|WITH AT LEAST ONE YAKU.'.replace("|", chr(10)),
    "THE TWO MENUS||FIRST: TOP LINE PRACTICE,|BOTTOM LINE REAL GAME.||SECOND, FROM TOP TO BOTTOM:|RIVALS' STYLE, CHOOSE THE|THREE RIVALS, RULES, SCREEN|ADJUST, PLAY.".replace("|", chr(10)),
    'CALLS||WHEN A RIVAL THROWS A TILE|YOU CAN USE, A BOX OPENS:|PON, CHI, KAN OR RON. MOVE TO|ONE AND PRESS SPACE.||RIICHI: A CLOSED HAND WAITING|FOR ONE TILE, 1000 POINTS.'.replace("|", chr(10)),
    'THE RIVALS LEARN||EACH RIVAL HAS SEVEN BARS:|RIICHI, CALLS, TANYAO, FLUSH,|TRIPLETS, KOKUSHI, FOLD.||YOUR WINS PUSH THEM TOWARDS|THE HANDS YOU WIN WITH.'.replace("|", chr(10)),
    'MUSIC||IN PLAY F2, F3, F4 AND F5|CHANGE THE TUNE, F1 STOPS IT.||F1 ON THE FIRST MENU OPENS|THIS TUTORIAL. SPACE: NEXT.||ANTXIKO.GITHUB.IO'.replace("|", chr(10)),
]


def fuente():
    letras = sorted(set("".join(PAGINAS)) - {" ", "\n"})
    faltan = [c for c in letras if c not in G]
    if faltan:
        raise SystemExit("faltan glifos: %r" % faltan)
    datos = bytearray()
    for c in letras:
        filas = G[c] + ["....."]
        for f in filas:
            b = 0
            for k, x in enumerate(f):
                if x == "#":
                    b |= 0x40 >> k
            datos.append(b)
    return letras, bytes(datos)


def paginas(letras):
    out = bytearray()
    for i, p in enumerate(PAGINAS):
        for c in p:
            if c == "\n":
                out.append(0xFE)
            elif c == " ":
                out.append(0)
            else:
                out.append(letras.index(c) + 1)
        out.append(0xFF)
    out.append(0xFD)
    return bytes(out)


def main(argv):
    letras, f = fuente()
    t = paginas(letras)
    with open(argv[1], "w", encoding="ascii") as s:
        s.write("; lo escribe tools/textos.py: %d glifos (%d bytes) y %d paginas (%d bytes)\n"
                % (len(letras), len(f), len(PAGINAS), len(t)))
        s.write("fuente:\n")
        for i in range(0, len(f), 8):
            s.write("\tdefb " + ",".join("0%02Xh" % x for x in f[i:i + 8]) + "\t; %s\n" % letras[i // 8])
        s.write("paginas:\n")
        for i in range(0, len(t), 16):
            s.write("\tdefb " + ",".join("0%02Xh" % x for x in t[i:i + 16]) + "\n")
    print("%d glifos, %d bytes de fuente, %d de paginas" % (len(letras), len(f), len(t)))


if __name__ == "__main__":
    main(sys.argv)
