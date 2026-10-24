# Hai no Majutsushi — parche tutorial

牌の魔術師 (*Hai no Majutsushi - Mahjong 2*; Konami, 1989, RC-765) es un mahjong para MSX2 con todos sus menús y mensajes en japonés. Este parche le añade un **tutorial corto en inglés**: con **F1** en el primer menú, cinco páginas explican cómo se juega, los dos menús, las llamadas, los rivales y las teclas de la música. Espacio pasa de página; tras la última se vuelve al menú. El resto del juego no cambia.

**1.264** bytes cambiados en **6** sitios · IPS de **1.302** bytes · todo en espacio que el cartucho no usa · no se distribuye ninguna ROM

![La primera página del tutorial](../imagenes/tutorial_1.png)

## Cómo se usa

1. En el título, espacio: sale el primer menú (練習対局, práctica; 実戦対局, partida de verdad).
2. **F1**. Se abre el tutorial.
3. **Espacio** para la página siguiente. Tras la quinta vuelve el menú y el juego sigue como siempre.

| | |
|---|---|
| ![página 2](../imagenes/tutorial_2.png) | ![página 3](../imagenes/tutorial_3.png) |
| ![página 4](../imagenes/tutorial_4.png) | ![página 5](../imagenes/tutorial_5.png) |

## Qué hace falta

- **La ROM del juego**, que este repositorio no distribuye: *Hai no Majutsushi - Mahjong 2* (Konami, 1989, RC-765), 131.072 bytes, sha256 `7839c843dc787e01765c1ba3efbd26dcf5209d27e38bcee1345db3b3cffdf5db`.
- Cualquier herramienta de IPS (Lunar IPS, Floating IPS, RomPatcher.js). Se aplica [parche/majutsushi_tutorial.ips](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/parche/majutsushi_tutorial.ips) a la ROM y sale la parcheada, sha256 `7bd8b0686b13c6c57fcff8f89f79af7d8622e4fcec1a5b0b6d1c040e229ce543`.

En openMSX el cartucho necesita su mapper (Konami con DAC):

```
openmsx -machine C-BIOS_MSX2 -cart majutsushi_tutorial.rom -romtype Majutsushi
```

## Montarlo

Con Python 3 y [pasmo](https://pasmo.speccy.org/) en el PATH, y la ROM en la raíz como `majutsushi.rom`:

```
python tools/construye.py majutsushi.rom
```

Ensambla [src/tutorial.asm](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/src/tutorial.asm), comprueba que cada sitio donde escribe tiene lo que tiene el cartucho original (o 0xFF donde usa espacio libre) y escribe `work/majutsushi_tutorial.rom` y el IPS. Cualquier otra ROM la rechaza. Los textos y la fuente están en [tools/textos.py](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/tools/textos.py), que escribe `src/datos.inc`. `python -m unittest discover -s tests` pasa los 6 tests: los textos son los del fuente, el IPS solo toca los seis sitios declarados y, con la ROM en la raíz, el IPS es el que sale del fuente y original + IPS es el original byte a byte fuera de esos sitios.

## Cómo funciona

- **El gancho.** El primer menú corre a cada cuadro desde p00:4396 (la entrada 1 de la tabla de estados de p00:4313). Ese bloque, con el sonido del cursor y el dibujo del cursor detrás, son 61 bytes. El parche lo escribe de nuevo en los mismos 61 bytes: `bit 4,a` en vez de `ld c,a / and 10h / ld a,c`, y los dos sprites del cursor escritos con `ld l,4` en vez de alternar HL y HL' con `exx`. Así queda sitio para mirar F1 al entrar (el bit 0 de 0xC00C, las teclas de función recién pulsadas) y para el salto al tutorial. El cursor y su sonido se mueven unos bytes, así que se corrigen las tres instrucciones que entran en ellos (p00:436F, 4834 y 483B). Nada más cambia en el banco 0.
- **El tutorial.** 104 bytes en el banco 15, en 0xAD8B, dentro de los 117 bytes a 0xFF que hay entre una tabla de tiles y la voz de 0xAE00. Pone los bancos 13-14-15 con la rutina del propio cartucho (p00:4246) y dibuja con las rutinas del cartucho: borra la pantalla (p00:4E50, p00:4FE5), espera al VDP (p00:4EEA), dibuja cada letra como un tile de 8 × 8 a un bit (p00:52A3) y lee las teclas (p00:55F0). Al salir deja el menú en el paso 0, para que se vuelva a dibujar, y repone los bancos 1-2-3, que son los que tiene el menú (medido en openMSX).
- **Los textos.** 1.097 bytes al final del banco 14 (0xBB7B), en el mayor tramo de 0xFF del cartucho (1.157 bytes): una fuente de 35 letras de 5 × 7 (280 bytes) y las cinco páginas (817 bytes), un byte por letra.
- **El espacio libre está medido.** En 15 minutos de openMSX entre título, menús y partida, con un punto de vigilancia en cada lectura de la ROM, nadie lee los 0xFF del final del banco 14 ni los de p15:AD8B.
- Las direcciones salen del [desensamblado comentado de Hai no Majutsushi](https://antxiko.github.io/Majutsushi-disassembly/es/).

## Probado

En openMSX (C-BIOS MSX2): F1 en el primer menú abre el tutorial, las cinco páginas pasan con espacio, vuelve el menú, el cursor sube y baja y al elegir práctica se llega al segundo menú. Aún sin probar en un MSX de verdad.

## Licencia

MIT ([LICENSE](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/LICENSE)) para el parche, las herramientas y la documentación. El juego es de sus titulares: ver [AVISO-LEGAL.md](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/AVISO-LEGAL.md).
