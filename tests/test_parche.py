"""Lo que tiene que cumplir el parche (tutorial y traduccion), con la ROM y sin ella."""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import construye  # noqa: E402
import ips  # noqa: E402
import traduce  # noqa: E402

IPS = RAIZ / "parche" / "majutsushi_en.ips"
ROM = RAIZ / "majutsushi.rom"


def registros():
    datos = IPS.read_bytes()
    assert datos[:5] == b"PATCH"
    i, out = 5, []
    while datos[i:i + 3] != b"EOF":
        off = int.from_bytes(datos[i:i + 3], "big")
        n = int.from_bytes(datos[i + 3:i + 5], "big")
        out.append((off, n))
        i += 5 + n
    return out


class SinRom(unittest.TestCase):
    def test_los_textos_son_los_del_fuente(self):
        """src/datos.inc es lo que sale de tools/textos.py."""
        with tempfile.TemporaryDirectory() as tmp:
            nuevo = Path(tmp) / "datos.inc"
            subprocess.run([sys.executable, str(RAIZ / "tools" / "textos.py"), str(nuevo)],
                           check=True, capture_output=True)
            self.assertEqual(nuevo.read_text(), (RAIZ / "src" / "datos.inc").read_text())

    def test_ninguna_linea_se_sale(self):
        """Cada renglon y cada fila de fichas cabe en los 512 puntos (256 unidades) de la pantalla:
        el generador lo comprueba al montar las pantallas, y las Y no pasan de las 212 lineas."""
        import textos
        datos = textos.bytes_tutorial()
        self.assertEqual(datos[-1], 0xFD)
        self.assertEqual(len(textos.PANTALLAS), 9)

    def test_el_tutorial_no_usa_katakana_ni_kanji(self):
        """Con la traduccion, los tiles de katakana (fila 0xC8) y las letras de 16 puntos son otros:
        el generador ya no los sabe escribir."""
        import textos
        with self.assertRaises(SystemExit):
            textos.letra("\u30dd")
        self.assertFalse(hasattr(textos, "KANJI"))

    def test_la_tabla_de_la_traduccion_se_lee(self):
        """Cada texto de traduccion/textos_en.txt se parte en casillas de 1-4 letras que la fuente
        sabe dibujar."""
        with open(RAIZ / "traduccion" / "textos_en.txt", encoding="utf-8") as f:
            lineas = f.readlines()
        for ln in lineas:
            if ln.startswith(("cadena ", "bloque ")):
                for t in traduce.comillas(ln):
                    for cas in traduce.casillas(t):
                        if isinstance(cas, str):
                            self.assertLessEqual(len(cas), 4, t)
                            traduce.casilla(cas)


class ConRom(unittest.TestCase):
    def setUp(self):
        if not ROM.exists():
            self.skipTest("sin majutsushi.rom")

    def test_el_ips_es_el_que_sale_del_fuente(self):
        guardado = IPS.read_bytes()
        subprocess.run([sys.executable, str(RAIZ / "tools" / "construye.py"), str(ROM)],
                       check=True, capture_output=True)
        self.assertEqual(IPS.read_bytes(), guardado)

    def test_rechaza_otra_rom(self):
        with tempfile.TemporaryDirectory() as tmp:
            falsa = Path(tmp) / "falsa.rom"
            falsa.write_bytes(bytes(131072))
            r = subprocess.run([sys.executable, str(RAIZ / "tools" / "construye.py"), str(falsa)],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)

    def traducida(self):
        t = traduce.Traduccion(bytearray(ROM.read_bytes()))
        t.aplica()
        return t

    def test_cada_cadena_esta_donde_apunta(self):
        """Cada puntero de la traduccion lleva a su cadena (o bloque), entera."""
        t = self.traducida()
        self.assertGreater(len(t.cadenas), 70)
        for refs, datos in t.cadenas:
            for r in refs:
                o = traduce.donde(t.rom, r)
                self.assertEqual(bytes(t.rom[o:o + len(datos)]), datos, hex(r))

    def test_las_cadenas_del_banco_4_pasan_por_la_copia(self):
        """La rutina de texto (p00:5ACF) deja los bancos 1-2-3 tras cada letra: una cadena del banco
        4 solo se lee entera copiada antes a la pila (p04:BF97). Solo la tabla de yaku (p01:6664)
        puede apuntar alli, y las tres llamadas que la escriben van a la copia."""
        t = self.traducida()
        for refs, _ in t.cadenas:
            for r in refs:
                if t.rom[r + 1] >= 0xA0 and r // 0x2000 == 1:
                    self.assertTrue(traduce.dir_rom("1:6664") <= r < traduce.dir_rom("1:66D0"), hex(r))
        for sitio in ("4:A9B0", "4:AE1E", "4:AA41"):
            o = traduce.dir_rom(sitio)
            self.assertEqual(bytes(t.rom[o:o + 3]), bytes([0xCD, 0x97, 0xBF]), sitio)

    def test_las_letras_sueltas_reservadas_no_cambian(self):
        """Las cifras (0x01-0x0A) y el circulo y la cruz de las reglas (0x47, 0x48) los pinta el
        codigo sueltos: siguen siendo los del cartucho."""
        t = self.traducida()
        for c in list(range(0x01, 0x0B)) + [0x47, 0x48]:
            o = traduce.LETRAS + 64 * (c - 1)
            self.assertEqual(t.rom[o:o + 64], t.base[o:o + 64], hex(c))

    def test_las_letras_nuevas_son_de_la_fuente(self):
        """Cada casilla nueva tiene un codigo de la fuente (0x01-0xBD) que no es de los reservados,
        y su dibujo es el de la casilla."""
        t = self.traducida()
        for cas, c in t.codigo.items():
            self.assertTrue(1 <= c <= traduce.ULTIMA and c not in t.reservado, cas)
            o = traduce.LETRAS + 64 * (c - 1)
            self.assertEqual(bytes(t.rom[o:o + 64]), traduce.a_bytes(traduce.casilla(cas)), cas)

    def test_ya_no_quedan_nombres_en_katakana(self):
        """En las once listas de nombres no queda ningun tile de katakana que no sea de los pares."""
        t = self.traducida()
        pares = set(t.tiles.values())
        for sitio in ("3:AEB9", "3:B118", "3:BD33", "4:B545", "4:B56C", "4:B592", "4:B5B8", "4:B5E0",
                      "4:B605", "4:B62E", "4:B656"):
            o = traduce.dir_rom(sitio) + 2
            while t.rom[o] != 0xFF:
                if t.rom[o] == 0xFE:
                    o += 3
                    continue
                if 0x60 <= t.rom[o] <= 0x84:
                    self.assertIn(t.rom[o], pares, sitio)
                o += 1

    def test_los_mapas_nuevos_se_leen_enteros(self):
        """El logotipo (p11:A453) y el fondo de la demo (p15:AAA0) se releen con las mismas casillas
        que el original: un literal de 127 llevaria la cabecera 0xFF, que es el final del mapa."""
        import fondo_demo
        import logotipo
        t = self.traducida()
        for mod in (logotipo, fondo_demo):
            xy0, c0, _ = mod.lee_mapa(t.base)
            xy1, c1, _ = mod.lee_mapa(t.rom)
            self.assertEqual((xy1, sorted(c1)), (xy0, sorted(c0)), mod.__name__)
        tiles = fondo_demo.lee_tiles(t.rom)
        self.assertTrue(set(fondo_demo.lee_mapa(t.rom)[1].values()) <= set(tiles))

    def test_las_caras_solo_cambian_los_man_y_los_vientos(self):
        """En los cuatro juegos de fichas, los nueve 萬 y los cuatro vientos son todos distintos entre
        si y distintos del original; las otras 22 fichas, punto a punto las del cartucho."""
        import caras
        t = self.traducida()
        cambian = set(caras.MAN) | set(caras.VIENTOS)
        for lista, paletas, disp, w, h, _ in caras.JUEGOS:
            fichas = []
            for rom in (t.base, t.rom):
                gs = caras.grupos(rom, lista, paletas)
                hoja = {g["c"] + k: caras.lee_tile(rom, g, k) for g in gs for k in range(g["n"])}
                fichas.append([caras.compone(c, w, hoja) for _, c in caras.disposicion(rom, disp, w, h)])
            antes, ahora = fichas
            self.assertEqual(len(ahora), 35)
            for i in range(35):
                if i in cambian:
                    self.assertNotEqual(ahora[i], antes[i], (hex(disp), i))
                else:
                    self.assertEqual(ahora[i], antes[i], (hex(disp), i))
            for grupo in (caras.MAN, caras.VIENTOS):
                vistas = [str(ahora[i]) for i in grupo]
                self.assertEqual(len(set(vistas)), len(vistas), hex(disp))

    def test_el_ips_solo_cambia_lo_declarado(self):
        """Cada byte que cambia un registro del IPS cae en un trozo del tutorial o en un sitio de la
        traduccion (un registro puede llevar bytes iguales entre dos cambios cercanos)."""
        t = self.traducida()
        zonas = [(b * 0x2000 + d - c, b * 0x2000 + h - c) for d, h, b, c, _ in construye.TROZOS] + t.zonas
        datos, base = IPS.read_bytes(), t.base
        i = 5
        while datos[i:i + 3] != b"EOF":
            off = int.from_bytes(datos[i:i + 3], "big")
            n = int.from_bytes(datos[i + 3:i + 5], "big")
            for k in range(n):
                if datos[i + 5 + k] != base[off + k]:
                    self.assertTrue(any(a <= off + k < z for a, z in zonas), hex(off + k))
            i += 5 + n

    def test_fuera_del_parche_el_juego_es_el_original(self):
        """Original + IPS: fuera de los trozos del tutorial y de los sitios de la traduccion, byte a
        byte el cartucho original."""
        base = ROM.read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(), construye.SHA256)
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "parcheada.rom"
            subprocess.run([sys.executable, str(RAIZ / "tools" / "ips.py"), "apply", str(ROM), str(IPS),
                            str(salida)], check=True, capture_output=True)
            nueva = salida.read_bytes()
        self.assertEqual(len(nueva), len(base))
        trozos = [(b * 0x2000 + d - c, b * 0x2000 + h - c) for d, h, b, c, _ in construye.TROZOS]
        trozos += self.traducida().zonas
        fuera = [k for k in range(len(base)) if base[k] != nueva[k] and not any(a <= k < z for a, z in trozos)]
        self.assertEqual(fuera, [])
        self.assertGreater(sum(1 for k in range(len(base)) if base[k] != nueva[k]), 1000)


if __name__ == "__main__":
    unittest.main()
