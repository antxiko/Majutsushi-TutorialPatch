#!/usr/bin/env python3
"""Monta el parche: ensambla src/tutorial.asm, mete cada trozo en su banco y escribe el IPS.

Los trozos (ver la cabecera de src/tutorial.asm), con la direccion de CPU y el banco que la ve, y lo
que el cartucho tiene ahi (se comprueba antes de escribir; None = tiene que ser todo 0xFF).

Uso: construye.py majutsushi.rom   (escribe work/majutsushi_tutorial.rom y parche/majutsushi_tutorial.ips)
"""
import hashlib
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASMO = shutil.which("pasmo") or r"C:\Users\Antxiko\AppData\Local\Programs\pasmo\pasmo.exe"
SHA256 = "7839c843dc787e01765c1ba3efbd26dcf5209d27e38bcee1345db3b3cffdf5db"   # la ROM base

# (desde, hasta, banco, base de CPU del banco, lo que hay en el original)
TROZOS = [
    (0x4370, 0x4372, 0, 0x4000, "af43"),          # call L_43AF en 0x436F
    (0x4396, 0x43D3, 0, 0x4000, "3a07c04fe610"),  # el paso 1 del menu (empieza por ld a,(0xC007))
    (0x4835, 0x4837, 0, 0x4000, "af43"),          # jp z,L_43AF en 0x4834
    (0x483C, 0x483E, 0, 0x4000, "ac43"),          # jp L_43AC en 0x483B
    (0x9B7B, 0xA000, 14, 0x8000, None),           # la fuente y las paginas
    (0xAD8B, 0xAE00, 15, 0xA000, None),           # el tutorial
]


def ensambla():
    os.makedirs(os.path.join(RAIZ, "work"), exist_ok=True)
    binario = os.path.join(RAIZ, "work", "tutorial.bin")
    simbolos = os.path.join(RAIZ, "work", "tutorial.sym")
    subprocess.run([PASMO, "--bin", "-I", "src", "src/tutorial.asm", binario, simbolos], cwd=RAIZ, check=True)
    sim = {}
    for ln in open(simbolos, encoding="ascii"):
        q = ln.split()
        if len(q) >= 3 and q[1] == "EQU":
            sim[q[0].upper()] = int(q[2].rstrip("H"), 16)
    return open(binario, "rb").read(), sim


def main(argv):
    base = bytearray(open(argv[1], "rb").read())
    if hashlib.sha256(base).hexdigest() != SHA256:
        raise SystemExit("%s no es la ROM de Hai no Majutsushi (sha256 %s)" % (argv[1], SHA256))
    binario, sim = ensambla()
    if sim["FIN_MENU"] != 0x43D3:
        raise SystemExit("el menu acaba en %04X y tiene que acabar en 43D3" % sim["FIN_MENU"])
    ini = 0x4370                      # la direccion mas baja del fuente
    usado = {0x9B7B: sim["FIN_DATOS"], 0xAD8B: sim["FIN_TUTORIAL"]}
    print("menu 61 de 61 bytes, tutorial %d de 117, datos %d de 1157" % (
        usado[0xAD8B] - 0xAD8B, usado[0x9B7B] - 0x9B7B))
    nueva = bytearray(base)
    for desde, hasta, banco, cpu, original in TROZOS:
        fin = usado.get(desde, hasta)
        if fin > hasta:
            raise SystemExit("%04X: el trozo se sale (%04X > %04X)" % (desde, fin, hasta))
        off = banco * 0x2000 + desde - cpu
        viejo = bytes(base[off:off + fin - desde])
        if original is None and viejo != b"\xff" * len(viejo):
            raise SystemExit("%04X en el banco %d no esta libre" % (desde, banco))
        if original is not None and not viejo.hex().startswith(original):
            raise SystemExit("%04X no tiene lo esperado: %s" % (desde, viejo[:8].hex()))
        nueva[off:off + fin - desde] = binario[desde - ini:fin - ini]
    salida = os.path.join(RAIZ, "work", "majutsushi_tutorial.rom")
    open(salida, "wb").write(nueva)
    print("ROM parcheada", hashlib.sha256(nueva).hexdigest(), "->", salida)
    ips = os.path.join(RAIZ, "parche", "majutsushi_tutorial.ips")
    subprocess.run([sys.executable, os.path.join(RAIZ, "tools", "ips.py"), "make", argv[1], salida, ips], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
