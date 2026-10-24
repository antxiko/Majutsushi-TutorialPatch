#!/usr/bin/env python3
"""La web (GitHub Pages, main:/docs): el README en ingles en docs/ y el
castellano en docs/es/, una pagina por idioma, con el estilo de la serie.
El enlace de idioma del README sobra: la pagina lleva su selector."""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))
import md2html  # noqa: E402
from contenido_web import REPOSITORIO  # noqa: E402

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
subprocess.run([sys.executable, str(RAIZ / "tools" / "check_enlaces.py"), str(RAIZ / "docs")], check=True)
