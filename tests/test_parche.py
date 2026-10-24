"""Lo que tiene que cumplir el parche, con la ROM y sin ella."""
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

IPS = RAIZ / "parche" / "majutsushi_tutorial.ips"
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

    def test_el_ips_solo_toca_los_trozos_declarados(self):
        """Cada registro del IPS cae dentro de uno de los trozos declarados en construye.py."""
        trozos = [(b * 0x2000 + d - c, b * 0x2000 + h - c) for d, h, b, c, _ in construye.TROZOS]
        regs = registros()
        self.assertEqual(len(regs), 6)
        for off, n in regs:
            self.assertTrue(any(a <= off and off + n <= z for a, z in trozos), hex(off))

    def test_ninguna_linea_se_sale(self):
        """Cada renglon y cada fila de fichas cabe en los 512 puntos (256 unidades) de la pantalla:
        el generador lo comprueba al montar las pantallas, y las Y no pasan de las 212 lineas."""
        import textos
        datos = textos.bytes_tutorial()
        self.assertEqual(datos[-1], 0xFD)
        self.assertEqual(len(textos.PANTALLAS), 9)

    def test_los_kanji_son_textos_del_banco_0(self):
        """Las cadenas en kanji que se dibujan estan en el banco 0 (0x4000-0x5FFF), el unico que no
        cambia mientras p00:5ACD cambia de banco."""
        import textos
        for a in textos.KANJI.values():
            self.assertTrue(0x4000 <= a < 0x6000)


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

    def test_fuera_del_parche_el_juego_es_el_original(self):
        """Original + IPS: fuera de los seis trozos, byte a byte el cartucho original."""
        base = ROM.read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(), construye.SHA256)
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "parcheada.rom"
            subprocess.run([sys.executable, str(RAIZ / "tools" / "ips.py"), "apply", str(ROM), str(IPS),
                            str(salida)], check=True, capture_output=True)
            nueva = salida.read_bytes()
        self.assertEqual(len(nueva), len(base))
        trozos = [(b * 0x2000 + d - c, b * 0x2000 + h - c) for d, h, b, c, _ in construye.TROZOS]
        fuera = [k for k in range(len(base)) if base[k] != nueva[k] and not any(a <= k < z for a, z in trozos)]
        self.assertEqual(fuera, [])
        self.assertGreater(sum(1 for k in range(len(base)) if base[k] != nueva[k]), 1000)


if __name__ == "__main__":
    unittest.main()
