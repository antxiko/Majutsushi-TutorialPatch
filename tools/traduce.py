#!/usr/bin/env python3
"""La traduccion al ingles: lee traduccion/textos_en.txt y cambia la ROM (letras de 16 puntos,
cadenas con sus punteros, tiles de 8 x 8) y pone los rotulos de las llamadas (tools/rotulos.py).
La usa tools/construye.py; sola, informa de lo que hace.

Las letras de 16 puntos (p00:5B29): 64 bytes por letra a 0x8000 + 64 x (A - 1) con los bancos 5-6
(en la ROM, 0xA000 + 64 x (A - 1)); 32 x 16 puntos de SCREEN 7 en ocho bloques de 8 x 8: los
cuatro de arriba de izquierda a derecha y luego los cuatro de abajo. Codigos 0x01-0xBD.
Los tiles de katakana (p00:5A6B, codigos 0x60-0x84): p07:6138, 16 bytes por tile de 16 x 8 puntos
de SCREEN 7 a 1 bit (bytes 0-7 la mitad izquierda de las ocho filas, 8-15 la derecha).

Uso: traduce.py majutsushi.rom     (escribe work/majutsushi_en.rom e informa)"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rotulos  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLA = os.path.join(RAIZ, "traduccion", "textos_en.txt")
FUENTES = os.path.join(RAIZ, "traduccion", "fuentes")

LETRAS = 5 * 0x2000          # la letra 0x01 en la ROM
ULTIMA = 0xBD                # la ultima letra de la fuente (detras hay otros datos)
KATA = 7 * 0x2000 + 0x138    # el tile 0x60 en la ROM
KATA_N = 0x25                # 37 tiles: 0x60-0x84
LATINA = {}                  # la letra de la hoja de tiles: 01-0A = 0-9, 0B-13 = A-I, 20-30 = J-Z
for i, c in enumerate("1234567890"):
    LATINA[c] = 0x01 + i
for i, c in enumerate("ABCDEFGHI"):
    LATINA[c] = 0x0B + i
for i, c in enumerate("JKLMNOPQRSTUVWXYZ"):
    LATINA[c] = 0x20 + i
LATINA[" "] = 0x00


def rom_off(banco, cpu, d):
    return banco * 0x2000 + d - cpu


BASE_CPU = {0: 0x4000, 1: 0x6000, 2: 0x8000, 3: 0xA000, 4: 0xA000}


def dir_rom(texto):
    """'3:A95F' -> desplazamiento en la ROM."""
    b, d = texto.split(":")
    b = int(b)
    return rom_off(b, BASE_CPU[b], int(d, 16))


# ------------------------------------------------------------------ fuentes
def lee_fuente(nombre, ancho, alto):
    glifos, g, filas = {}, None, []
    for ln in open(os.path.join(FUENTES, nombre), encoding="utf-8"):
        ln = ln.rstrip("\n")
        if ln.startswith("glifo "):
            if g is not None:
                glifos[g] = filas
            g, filas = ln[6:].strip(), []
        elif g is not None and re.fullmatch(r"[#.]+", ln):
            if len(ln) != ancho:
                raise SystemExit("%s: %s tiene una fila de %d" % (nombre, g, len(ln)))
            filas.append(ln)
    if g is not None:
        glifos[g] = filas
    for g, f in glifos.items():
        if len(f) != alto:
            raise SystemExit("%s: %s tiene %d filas" % (nombre, g, len(f)))
    glifos[" "] = ["." * ancho] * alto
    if "espacio" in glifos:
        glifos[" "] = glifos.pop("espacio")
    return glifos


ANCHA = lee_fuente("latina.txt", 8, 8)
ESTRECHA = lee_fuente("estrecha.txt", 3, 7)


def glifo(fuente, c):
    if c not in fuente:
        raise SystemExit("la fuente no tiene la letra %r" % c)
    return fuente[c]


def pinta(lienzo, filas, x0, y0, ex, ey):
    for y, f in enumerate(filas):
        for x, p in enumerate(f):
            if p == "#":
                for dy in range(ey):
                    for dx in range(ex):
                        lienzo[y0 + y * ey + dy][x0 + x * ex + dx] = 1


def casilla(texto, centro=False):
    """El dibujo de 32 x 16 de una casilla de 1-4 letras."""
    lz = [[0] * 32 for _ in range(16)]
    n = len(texto)
    if n <= 2:
        if centro and n == 1:
            pinta(lz, glifo(ANCHA, texto), 8, 0, 2, 2)
        for i, c in enumerate(texto if not (centro and n == 1) else ""):
            pinta(lz, glifo(ANCHA, c), 16 * i, 0, 2, 2)
    elif n == 3:
        for i, c in enumerate(texto):
            pinta(lz, glifo(ESTRECHA, c), 1 + 10 * i, 2, 3, 2)
    elif n == 4:
        for i, c in enumerate(texto):
            pinta(lz, glifo(ESTRECHA, c), 1 + 8 * i, 2, 2, 2)
    else:
        raise SystemExit("una casilla lleva cuatro letras como mucho: %r" % texto)
    return lz


def a_bytes(lz):
    out = bytearray(64)
    for mitad in range(2):
        for blq in range(4):
            for r in range(8):
                fila = lz[mitad * 8 + r]
                v = 0
                for k in range(8):
                    if fila[blq * 8 + k]:
                        v |= 0x80 >> k
                out[mitad * 32 + blq * 8 + r] = v
    return bytes(out)


def de_bytes(b):
    lz = [[0] * 32 for _ in range(16)]
    for mitad in range(2):
        for blq in range(4):
            for r in range(8):
                v = b[mitad * 32 + blq * 8 + r]
                for k in range(8):
                    lz[mitad * 8 + r][blq * 8 + k] = 1 if v & (0x80 >> k) else 0
    return lz


def tile_par(texto):
    """Un tile de 16 x 8 con dos letras estrechas (cada una 6 puntos de ancho y 7 de alto)."""
    lz = [[0] * 16 for _ in range(8)]
    for i, c in enumerate(texto):
        pinta(lz, glifo(ESTRECHA, c), 1 + 8 * i, 1, 2, 1)
    out = bytearray(16)
    for r in range(8):
        for mitad in range(2):
            v = 0
            for k in range(8):
                if lz[r][mitad * 8 + k]:
                    v |= 0x80 >> k
            out[mitad * 8 + r] = v
    return bytes(out)


# ------------------------------------------------------------------ textos
def casillas(texto):
    """'TEXTO' -> lista de casillas (str) o codigos ({XX} -> int)."""
    if "|" in texto:
        trozos = texto.split("|")
        # con casillas estrechas, las cortas se rellenan para tener la misma letra
        ancho = max(len(t) for t in trozos if not t.startswith("{"))
        if ancho > 2:
            trozos = [t if t.startswith("{") else t.ljust(ancho) for t in trozos]
    else:
        trozos = []
        t = texto
        while t:
            m = re.match(r"\{([0-9A-Fa-f]{2})\}", t)
            if m:
                trozos.append(t[:4])
                t = t[4:]
            else:
                trozos.append(t[:2])
                t = t[2:]
    out = []
    for tr in trozos:
        m = re.fullmatch(r"\{([0-9A-Fa-f]{2})\}", tr)
        out.append(int(m.group(1), 16) if m else tr)
    return out


def comillas(texto):
    return re.findall(r'"([^"]*)"', texto)


class Traduccion:
    def __init__(self, rom):
        self.base = bytes(rom)
        self.rom = rom
        self.codigo = {}          # casilla -> codigo de letra
        self.reservado = set()
        self.tiles = {}           # par -> codigo de tile
        self.informe = []
        self.cadenas = []         # (refs, bytes): cada cadena o bloque colocado, para los tests
        # los sitios que la traduccion puede cambiar (desde, hasta) en la ROM: la fuente entera y
        # los tiles de katakana, y lo que se apunte al ir (huecos, punteros, bytes, listas)
        self.zonas = [(LETRAS, LETRAS + 64 * ULTIMA), (KATA, KATA + 16 * KATA_N)]

    # -------------------------------------------------------------- letras
    def letra_libre(self):
        for c in range(1, ULTIMA + 1):
            if c not in self.reservado and c not in self.codigo.values():
                return c
        raise SystemExit("no quedan letras libres en la fuente de 16 puntos")

    def cod(self, cas):
        if isinstance(cas, int):
            return cas
        if cas.strip() == "":
            return 0x00
        if cas not in self.codigo:
            self.codigo[cas] = self.letra_libre()
        return self.codigo[cas]

    def codifica(self, texto):
        return bytes(self.cod(c) for c in casillas(texto)) + b"\xff"

    def letra(self, args):
        c = int(args[0], 16)
        self.reservado.add(c)
        if args[1] == "copia":
            fuentes = [int(x, 16) for x in args[2].split("+")]
            vieja = [de_bytes(self.base[LETRAS + 64 * (f - 1):LETRAS + 64 * f]) for f in fuentes]
            lz = [fila[:] for fila in vieja[0]]
            if len(vieja) > 1:
                for y in range(16):
                    lz[y][16:] = vieja[1][y][:16]
        else:
            texto = comillas(" ".join(args[1:]))[0]
            lz = casilla(texto, centro="centro" in args)
        self.pon_letra(c, a_bytes(lz))

    def pon_letra(self, c, b):
        o = LETRAS + 64 * (c - 1)
        self.rom[o:o + 64] = b

    # -------------------------------------------------------------- grupos de cadenas
    def grupo(self, cab, lineas):
        p = dict(x.split("=", 1) for x in cab.split()[2:])
        huecos = []
        for clave_b, clave_c, clave_h in (("banco", "cpu", "huecos"), ("banco2", "cpu2", "huecos2")):
            if clave_b not in p:
                continue
            b, cpu = int(p[clave_b]), int(p[clave_c], 16)
            for h in p[clave_h].split(","):
                d, a = (int(x, 16) for x in h.split("-"))
                huecos.append([b, cpu, d, a + 1])
        piezas = []      # (bytes, refs, solo): solo = el unico banco donde puede ir, o None
        for ln in lineas:
            tipo, resto = ln.split(" ", 1)
            m = re.match(r"ref=(\S+)\s+(?:solo=(\d+)\s+)?(.*)$", resto)
            refs = [dir_rom(r) for r in m.group(1).split(",")]
            solo = int(m.group(2)) if m.group(2) else None
            cuerpo = m.group(3)
            if tipo == "cadena":
                datos = self.codifica(comillas(cuerpo)[0])
            elif tipo == "bloque":
                datos = b""
                for reg in cuerpo.split(" | "):
                    xy, = re.findall(r"([0-9A-Fa-f]{2},[0-9A-Fa-f]{2})", reg)[:1]
                    x, y = (int(v, 16) for v in xy.split(","))
                    datos += bytes([x, y]) + self.codifica(comillas(reg)[0])
            else:
                raise SystemExit("linea rara en el grupo: %r" % ln)
            piezas.append((datos, refs, solo))
            self.cadenas.append((refs, datos))
        # las iguales comparten sitio (y el banco obligado de cualquiera de ellas)
        unidas, obligado = {}, {}
        for datos, refs, solo in piezas:
            unidas.setdefault(datos, []).extend(refs)
            if solo is not None:
                obligado[datos] = solo
        libre_antes = sum(h[3] - h[2] for h in huecos)
        # se borran los huecos (0xFF) y se colocan de mayor a menor en el hueco mas justo
        for b, cpu, d, a in huecos:
            o = rom_off(b, cpu, d)
            self.rom[o:o + a - d] = b"\xff" * (a - d)
            self.zonas.append((o, o + a - d))
        usado = 0
        # primero las que solo pueden ir en un banco, y de mayor a menor
        for datos in sorted(unidas, key=lambda d: (d not in obligado, -len(d))):
            cabe = [h for h in huecos if h[3] - h[2] >= len(datos)
                    and obligado.get(datos, h[0]) == h[0]]
            if not cabe:
                raise SystemExit("grupo %s: no cabe %s (%d bytes); quedan %s" % (
                    cab.split()[1], datos.hex(" "), len(datos),
                    [(hex(h[2]), h[3] - h[2]) for h in huecos]))
            h = min(cabe, key=lambda h: h[3] - h[2])
            b, cpu, d = h[0], h[1], h[2]
            o = rom_off(b, cpu, d)
            self.rom[o:o + len(datos)] = datos
            for r in unidas[datos]:
                self.rom[r] = d & 0xFF
                self.rom[r + 1] = d >> 8
                self.zonas.append((r, r + 2))
            h[2] += len(datos)
            usado += len(datos)
        self.informe.append("grupo %-8s %3d de %3d bytes, %d cadenas" % (
            cab.split()[1], usado, libre_antes, len(unidas)))

    # -------------------------------------------------------------- tiles
    def tile(self, par):
        if par not in self.tiles:
            if len(self.tiles) >= KATA_N:
                raise SystemExit("no quedan tiles de katakana para los pares")
            self.tiles[par] = 0x60 + len(self.tiles)
        return self.tiles[par]

    def tiles_de(self, texto):
        out = []
        for m in re.finditer(r'"([^"]*)"|\{(..)\}|\b([0-9A-Fa-f]{2})\b', texto):
            if m.group(1) is not None:
                out += [LATINA[c] for c in m.group(1)]
            elif m.group(2) is not None:
                out.append(self.tile(m.group(2)))
            else:
                out.append(int(m.group(3), 16))
        return bytes(out)

    def cambia_tiles(self, resto):
        sitio, cambio = resto.split(" ", 1)
        viejo, nuevo = cambio.split("=")
        viejo = bytes(int(x, 16) for x in viejo.split())
        nuevo = self.tiles_de(nuevo)
        o = dir_rom(sitio)
        if self.base[o:o + len(viejo)] != viejo:
            raise SystemExit("tiles %s: hay %s y no %s" % (sitio, self.base[o:o + len(viejo)].hex(" "),
                                                           viejo.hex(" ")))
        if len(nuevo) != len(viejo):
            raise SystemExit("tiles %s: %d tiles por %d" % (sitio, len(nuevo), len(viejo)))
        self.rom[o:o + len(nuevo)] = nuevo
        self.zonas.append((o, o + len(nuevo)))

    def nombres(self, listas, cambios):
        hechos = {}
        for sitio in listas:
            o = dir_rom(sitio)
            o += 2
            while True:
                ini = o
                while self.base[o] not in (0xFE, 0xFF):
                    o += 1
                trozo = bytes(self.base[ini:o])
                for viejo, nuevo in cambios:
                    if trozo == viejo:
                        self.rom[ini:o] = nuevo
                        self.zonas.append((ini, o))
                        hechos[viejo] = hechos.get(viejo, 0) + 1
                if self.base[o] == 0xFF:
                    break
                o += 3
        for viejo, _ in cambios:
            if viejo not in hechos:
                raise SystemExit("el nombre %s no esta en ninguna lista" % viejo.hex(" "))
        self.informe.append("nombres: %s" % ", ".join("%s x%d" % (v.hex(), n) for v, n in hechos.items()))

    def pon_tiles(self):
        for par, c in self.tiles.items():
            o = KATA + 16 * (c - 0x60)
            self.rom[o:o + 16] = tile_par(par)
        self.informe.append("tiles de pares: %d de %d (%s)" % (
            len(self.tiles), KATA_N, " ".join("[%s]" % p for p in self.tiles)))

    # -------------------------------------------------------------- todo
    def aplica(self):
        lineas = [ln.rstrip("\n") for ln in open(TABLA, encoding="utf-8")]
        lineas = [ln for ln in lineas if ln.strip() and not ln.startswith("#")]
        for ln in lineas:                       # primero las letras reservadas
            if ln.startswith("letra "):
                self.letra(ln.split()[1:])
            elif ln.startswith("reserva "):
                for x in ln.split()[1:]:
                    d, _, a = x.partition("-")
                    self.reservado.update(range(int(d, 16), int(a or d, 16) + 1))
        cab, cuerpo, listas, cambios = None, [], [], []
        for ln in lineas + ["fin"]:
            if cab and not ln.startswith(("cadena ", "bloque ", "byte ")):
                self.grupo(cab, cuerpo)
                cab, cuerpo = None, []
            if ln.startswith("grupo "):
                cab = ln
            elif ln.startswith(("cadena ", "bloque ")):
                cuerpo.append(ln)
            elif ln.startswith("bytes "):
                sitio, cambio = ln.split(" ", 2)[1:]
                viejo, nuevo = cambio.split("=")
                nuevo = bytes(int(x, 16) for x in nuevo.split())
                viejo = b"\xff" * len(nuevo) if viejo.strip() == "libre" else \
                    bytes(int(x, 16) for x in viejo.split())
                o = dir_rom(sitio)
                if self.base[o:o + len(viejo)] != viejo or len(viejo) != len(nuevo):
                    raise SystemExit("bytes %s: hay %s" % (sitio, self.base[o:o + len(nuevo)].hex(" ")))
                self.rom[o:o + len(nuevo)] = nuevo
                self.zonas.append((o, o + len(nuevo)))
            elif ln.startswith("byte "):
                sitio, cambio = ln.split(" ", 2)[1:]
                viejo, nuevo = (int(x, 16) for x in cambio.split("="))
                o = dir_rom(sitio)
                if self.base[o] != viejo:
                    raise SystemExit("byte %s: hay %02X y no %02X" % (sitio, self.base[o], viejo))
                self.rom[o] = nuevo
                self.zonas.append((o, o + 1))
            elif ln.startswith("tiles "):
                self.cambia_tiles(ln[6:])
            elif ln.startswith("listas "):
                listas = ln.split()[1:]
            elif ln.startswith("nombre "):
                viejo, nuevo = ln[7:].split("=")
                cambios.append((bytes(int(x, 16) for x in viejo.split()), self.tiles_de(nuevo)))
        if cambios:
            self.nombres(listas, cambios)
        for cas, c in self.codigo.items():
            self.pon_letra(c, a_bytes(casilla(cas)))
        self.pon_tiles()
        zonas, usado = rotulos.aplica(self.rom)
        self.zonas += zonas
        import demo
        zonas, linea = demo.aplica(self.rom)
        self.zonas += zonas
        self.informe.append(linea)
        import logotipo
        zonas, linea = logotipo.aplica(self.rom)
        self.zonas += zonas
        self.informe.append(linea)
        import fondo_demo
        zonas, linea = fondo_demo.aplica(self.rom)
        self.zonas += zonas
        self.informe.append(linea)
        import caras
        zonas, linea = caras.aplica(self.rom)
        self.zonas += zonas
        self.informe.append(linea)
        self.informe.append("rotulos de las llamadas: %d de %d bytes" % (usado, rotulos.ZONA[1] - rotulos.ZONA[0]))
        self.informe.append("letras de 16 puntos: %d nuevas + %d redibujadas, %d libres" % (
            len(self.codigo), len(self.reservado),
            ULTIMA - len(self.codigo) - len(self.reservado)))
        return self.informe


def aplica(rom):
    """Cambia la ROM (bytearray) en su sitio y devuelve el informe."""
    return Traduccion(rom).aplica()


def donde(rom, ref):
    """El sitio en la ROM al que apunta la palabra que hay en ref: el banco que se ve en esa
    direccion es el 0 por debajo de 0x6000, el 1 hasta 0x8000, el 2 hasta 0xA000 y, por encima, el
    de la ref si es el 3 o el 4, o el 4 (la puntuacion se lee con los bancos 1, 2 y 4)."""
    d = rom[ref] | rom[ref + 1] << 8
    if d < 0x6000:
        banco = 0
    elif d < 0x8000:
        banco = 1
    elif d < 0xA000:
        banco = 2
    else:
        banco = ref // 0x2000 if ref // 0x2000 in (3, 4) else 4
    return rom_off(banco, BASE_CPU[banco], d)


def main(argv):
    rom = bytearray(open(argv[1], "rb").read())
    for ln in aplica(rom):
        print(ln)
    salida = os.path.join(RAIZ, "work", "majutsushi_en.rom")
    open(salida, "wb").write(rom)
    print("->", salida)


if __name__ == "__main__":
    main(sys.argv)
