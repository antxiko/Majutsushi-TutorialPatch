#!/usr/bin/env python3
"""Cuenta las casillas de la fuente de 16 puntos que pide un borrador ingles: cada cadena se parte
en casillas de 2 letras (o de 3 si la linea lleva '|3'); da los pares distintos y las casillas.

Uso: cuenta_pares.py FICHERO   (lineas "direccion japones ingles"; se uso con el borrador del paso 1)"""
import sys


def casillas(texto, ancho=2):
    texto = texto.strip()
    if len(texto) % ancho:
        texto += " " * (ancho - len(texto) % ancho)
    return [texto[i:i + ancho] for i in range(0, len(texto), ancho)]


def main(f):
    pares, total, n = {}, 0, 0
    for ln in open(f, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"):
            continue
        dire, jp, en = ln.rstrip("\n").split(" ", 2)
        ancho = 3 if en.endswith("|3") else 2
        en = en.replace("|3", "")
        c = casillas(en, ancho)
        n += 1
        total += len(c)
        for x in c:
            pares[x] = pares.get(x, 0) + 1
    print("cadenas %d, casillas %d, casillas distintas %d" % (n, total, len(pares)))
    print(" ".join("[%s]" % k for k in sorted(pares)))


if __name__ == "__main__":
    main(sys.argv[1])
