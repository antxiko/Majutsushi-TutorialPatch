#!/usr/bin/env python3
"""Los rotulos de las llamadas (ポン! チー! カン! ロン! ツモ! リーチ!) en ingles.

Cada rotulo son 16 patrones de sprite de 16 x 16 (512 bytes) que p00:58A2 vuelca a la VRAM 0xFE00
con el RLE de p00:4E2D, desde la tabla de seis punteros de p00:58B9 (bancos 5-6). p03:A7A1 los pone
en 2 filas de 4 casillas (64 x 32 puntos): en cada casilla dos sprites, el patron par en rojo
(color 9, el relleno, plano mas bajo: va encima) y el impar en blanco (color 15, el contorno).

Aqui se dibuja el texto con una letra gruesa inclinada (traduccion/rotulos/*.txt si existe el
dibujo a mano; si no, se genera con la fuente de Windows y se guarda alli para retocarlo), se le
pone un contorno de un punto y se codifica en RLE.

Uso: rotulos.py dibuja     (genera traduccion/rotulos/*.txt que falten y una hoja en work/)"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, "traduccion", "rotulos")
TABLA = 0x58B9                       # p00: seis punteros (bancos 5-6 en 0x8000-0xBFFF)
ZONA = (0xB557, 0xBEC2)              # los seis RLE originales, seguidos
NOMBRES = ["PON!", "CHI!", "KAN!", "RON!", "TSUMO!", "RIICHI!"]
FUENTE = r"C:\Windows\Fonts\impact.ttf"


def rom_b56(d):
    return 5 * 0x2000 + d - 0x8000


# ------------------------------------------------------------------ RLE (p00:4E2D)
def descomprime(rom, d):
    out = bytearray(512)
    dst, i = 0xFE00, rom_b56(d)
    while True:
        x = rom[i]
        i += 1
        if x == 0:
            return bytes(out)
        if x < 0x80:
            for _ in range(x):
                out[dst - 0xFE00] = rom[i]
                dst += 1
            i += 1
        elif x == 0x80:
            dst = rom[i] | rom[i + 1] << 8
            i += 2
        else:
            for _ in range(x & 0x7F):
                out[dst - 0xFE00] = rom[i]
                i += 1
                dst += 1


def comprime(datos):
    """RLE de p00:4E2D: tiras de 3 o mas iguales con n < 0x80 y el byte; el resto en copias de
    0x81-0xFF (hasta 127 bytes). Empieza en 0xFE00, que ya es donde escribe p00:58AE."""
    out = bytearray()
    i, lit = 0, bytearray()

    def suelta():
        while lit:
            trozo = lit[:127]
            out.append(0x80 | len(trozo))
            out.extend(trozo)
            del lit[:127]
    while i < len(datos):
        n = 1
        while i + n < len(datos) and datos[i + n] == datos[i] and n < 127:
            n += 1
        if n >= 3:
            suelta()
            out += bytes([n, datos[i]])
            i += n
        else:
            lit.extend(datos[i:i + n])
            i += n
    suelta()
    out.append(0)
    return bytes(out)


# ------------------------------------------------------------------ dibujos
def a_patrones(relleno, contorno):
    """Dos mascaras de 64 x 32 (listas de filas de 0/1) -> 512 bytes: casilla (fila r, columna c),
    patron 2 x (4r + c) el relleno y el siguiente el contorno; cada patron, 16 bytes de la mitad
    izquierda y 16 de la derecha."""
    out = bytearray(512)
    for r in range(2):
        for c in range(4):
            for capa, m in ((0, relleno), (1, contorno)):
                p = 2 * (4 * r + c) + capa
                for y in range(16):
                    for mitad in range(2):
                        v = 0
                        for k in range(8):
                            if m[r * 16 + y][c * 16 + mitad * 8 + k]:
                                v |= 0x80 >> k
                        out[32 * p + 16 * mitad + y] = v
    return bytes(out)


def de_patrones(datos):
    relleno = [[0] * 64 for _ in range(32)]
    contorno = [[0] * 64 for _ in range(32)]
    for r in range(2):
        for c in range(4):
            for capa, m in ((0, relleno), (1, contorno)):
                p = 2 * (4 * r + c) + capa
                for y in range(16):
                    for x in range(16):
                        if datos[32 * p + y + (16 if x >= 8 else 0)] & (0x80 >> (x % 8)):
                            m[r * 16 + y][c * 16 + x] = 1
    return relleno, contorno


def silueta(relleno):
    """La capa blanca: el relleno engordado un punto. El sprite rojo es el del plano mas bajo y se
    pinta encima, asi que se ve como un contorno; y una silueta maciza comprime mejor que el anillo
    (tiras de 0xFF en el RLE)."""
    c = contorno_de(relleno)
    return [[1 if relleno[y][x] or c[y][x] else 0 for x in range(64)] for y in range(32)]


def contorno_de(relleno):
    """Un punto alrededor del relleno (ocho vecinos), sin pisarlo."""
    c = [[0] * 64 for _ in range(32)]
    for y in range(32):
        for x in range(64):
            if relleno[y][x]:
                continue
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < 32 and 0 <= xx < 64 and relleno[yy][xx]:
                        c[y][x] = 1
    return c


def genera(texto):
    """El relleno de 64 x 32 de un texto con Impact, inclinado: se dibuja grande y se reduce a 30
    puntos de alto; si pasa de 62 de ancho se estrecha (las palabras largas quedan igual de altas)."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FUENTE, 120)
    im = Image.new("L", (900, 200), 0)
    ImageDraw.Draw(im).text((40, 10), texto, font=f, fill=255)
    im = im.transform(im.size, Image.AFFINE, (1, 0.25, -30, 0, 1, 0), resample=Image.BICUBIC)
    im = im.crop(im.point(lambda v: 255 if v > 128 else 0).getbbox())
    w, h = im.size
    alto = 30
    ancho = min(62, round(w * alto / h))
    im = im.resize((ancho, alto), Image.LANCZOS).point(lambda v: 255 if v > 120 else 0)
    lz = [[0] * 64 for _ in range(32)]
    ox, oy = (64 - ancho) // 2, 1
    for y in range(alto):
        for x in range(ancho):
            if im.getpixel((x, y)):
                lz[oy + y][ox + x] = 1
    return lz


def lee_dibujo(nombre):
    ruta = os.path.join(DIR, nombre + ".txt")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        filas = [ln.strip() for ln in f if re.fullmatch(r"[#.]+", ln.strip())]
    if len(filas) != 32 or any(len(f) != 64 for f in filas):
        raise SystemExit("%s: hacen falta 32 filas de 64" % ruta)
    return [[1 if c == "#" else 0 for c in f] for f in filas]


def archivo(texto):
    return {"PON!": "pon", "CHI!": "chi", "KAN!": "kan", "RON!": "ron", "TSUMO!": "tsumo",
            "RIICHI!": "riichi"}[texto]


def dibujo(texto):
    lz = lee_dibujo(archivo(texto))
    return lz if lz is not None else genera(texto)


def aplica(rom):
    """Pone los seis rotulos nuevos en la zona de los viejos y la tabla de p00:58B9. Devuelve
    las zonas cambiadas."""
    sitio = ZONA[0]
    zonas = []
    o = rom_b56(ZONA[0])
    rom[o:rom_b56(ZONA[1])] = b"\xff" * (ZONA[1] - ZONA[0])
    zonas.append((o, rom_b56(ZONA[1])))
    for k, texto in enumerate(NOMBRES):
        r = dibujo(texto)
        rle = comprime(a_patrones(r, silueta(r)))
        if sitio + len(rle) > ZONA[1]:
            raise SystemExit("los rotulos no caben (%s)" % texto)
        rom[rom_b56(sitio):rom_b56(sitio) + len(rle)] = rle
        t = TABLA - 0x4000 + 2 * k
        rom[t] = sitio & 0xFF
        rom[t + 1] = sitio >> 8
        zonas.append((t, t + 2))
        sitio += len(rle)
    return zonas, sitio - ZONA[0]


def main(argv):
    from PIL import Image
    os.makedirs(DIR, exist_ok=True)
    E = 4
    hoja = Image.new("RGB", (2 * 70 * E, 3 * 36 * E), (40, 120, 40))
    px = hoja.load()
    for k, texto in enumerate(NOMBRES):
        ruta = os.path.join(DIR, archivo(texto) + ".txt")
        r = dibujo(texto)
        if not os.path.exists(ruta):
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write("# %s: el relleno rojo (64 x 32, '#'); el contorno blanco sale solo\n" % texto)
                for fila in r:
                    f.write("".join("#" if v else "." for v in fila) + "\n")
        c = contorno_de(r)
        ox, oy = (k % 2) * 70, (k // 2) * 36
        for y in range(32):
            for x in range(64):
                col = (220, 30, 30) if r[y][x] else ((255, 255, 255) if c[y][x] else None)
                if col:
                    for dy in range(E):
                        for dx in range(E):
                            px[(ox + x) * E + dx, (oy + y) * E + dy] = col
    os.makedirs(os.path.join(RAIZ, "work"), exist_ok=True)
    hoja.save(os.path.join(RAIZ, "work", "rotulos.png"))
    print("->", os.path.join(RAIZ, "work", "rotulos.png"))


if __name__ == "__main__":
    main(sys.argv)
