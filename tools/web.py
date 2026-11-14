#!/usr/bin/env python3
"""La web (GitHub Pages, main:/docs): el README en ingles en docs/ y el
castellano en docs/es/, una pagina por idioma, con el estilo de la serie.
El enlace de idioma del README sobra: la pagina lleva su selector."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import md2html  # noqa: E402
from contenido_web import REPOSITORIO, DESCARGAS, DESCARGAS_NOTA  # noqa: E402


def descargas(dest, idioma):
    """El parche, a mano: copia cada IPS a docs/ y pone sus botones de descarga
    justo debajo del titulo. Los IPS y sus rotulos los dice contenido_web.py."""
    botones = ""
    for ruta, rotulo in DESCARGAS:
        origen = RAIZ / ruta
        shutil.copy(origen, RAIZ / "docs" / origen.name)
        href = origen.name if idioma == "en" else "../" + origen.name
        botones += ('<a class="descarga" href="%s" download>&#8595; %s</a>'
                    % (href, rotulo[idioma]))
    nota = DESCARGAS_NOTA[idioma]
    pagina = RAIZ / dest / "index.html"
    html = pagina.read_text(encoding="utf-8")
    assert html.count("</h1>") == 1, "la pagina tiene que tener un solo titulo"
    html = html.replace("</h1>", '</h1>\n<p class="descargas">%s<small>%s</small></p>'
                        % (botones, nota))
    pagina.write_text(html, encoding="utf-8")


for readme, dest, idioma in (("README.md", "docs", "en"), ("README.es.md", "docs/es", "es")):
    texto = (RAIZ / readme).read_text(encoding="utf-8")
    texto = re.sub(r"^\*\[(English|Español)\]\(README(\.es)?\.md\)\*\n\n", "", texto, flags=re.M)
    # las imagenes viven en docs/imagenes; los demas enlaces relativos del README apuntan a
    # ficheros del repositorio, que la web no sirve: van a GitHub
    texto = texto.replace("](docs/imagenes/", "](imagenes/" if idioma == "en" else "](../imagenes/")
    texto = re.sub(r"\]\((?!https?:|#|imagenes/|\.\./imagenes/)([^)]+)\)",
                   lambda m: "](%s/blob/main/%s)" % (REPOSITORIO, m.group(1)), texto)
    (RAIZ / dest).mkdir(parents=True, exist_ok=True)
    (RAIZ / dest / "index.md").write_text(texto, encoding="utf-8")
    md2html.main(str(RAIZ / dest), idioma)
    descargas(dest, idioma)
subprocess.run([sys.executable, str(RAIZ / "tools" / "check_enlaces.py"), str(RAIZ / "docs")], check=True)
