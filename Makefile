# Hai no Majutsushi - parche TUTORIAL. La ROM no se distribuye: va en la raiz
# como majutsushi.rom (sha256 en tools/construye.py).

ROM = majutsushi.rom

all: parche test

# los textos y la fuente -> src/datos.inc
textos:
	python3 tools/textos.py src/datos.inc

# ensambla, comprueba los sitios y escribe work/majutsushi_tutorial.rom y el IPS
parche: $(ROM)
	python3 tools/construye.py $(ROM)

# la web: el README en docs/ (ingles) y docs/es/ (castellano)
web:
	python3 tools/web.py

test:
	python3 -m unittest discover -s tests -v

.PHONY: all textos parche web test
