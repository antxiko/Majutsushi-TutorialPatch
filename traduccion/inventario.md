# Inventario de textos de Hai no Majutsushi (paso 1 de la traduccion)

Medido el 2026-10-24 sobre la ROM original (majutsushi.rom). Fuentes de la medida:
`tools/omsx_textos.tcl` (work/textos2), `tools/omsx_tiles.tcl` (work/t1: demo sin teclas,
work/t2: 1.200 s de partida con espacio cada 2 s) y las capturas de los menus del desensamblado
(desensamblados/MAJUTSUSHI_DISAM/work/m2-m5).

El juego escribe de tres maneras. Cada una pide un arreglo distinto.

## A. Fuente de 16 puntos (p00:5ACD/5ACF, letra en p00:5B29)

Bancos 5-6, 64 B por letra, codigos 0x01-0xBD (189). `tools/fuente16.py` = codigo -> caracter.
Cadenas: codigos y 0xFF. Arreglo: casillas con 2 letras latinas (3 en las estrechas), como el Dojo.

| Donde | Que | Notas |
|---|---|---|
| p00:438C, 4391 | 練習対局 / 実戦対局 | primer menu |
| p00:59F5 (lista), 59F7-5A14 | 性格設定 面子選択 ルール設定 画面補正 終了 | menu de ajustes |
| p00:4765 | 半荘終了 | fin de partida |
| p00:481E, 4821 | 続行 / 終了 | seguir o acabar |
| p02:8FFF | 仮東 | sorteo del asiento |
| p03:A96E (92 B, 16 textos X,Y,codigos,FF; p03:A95E) | ル ー ル 設 定 (letra a letra) + 10 reglas + 終了 | pantalla de reglas |
| p03:B33B (40 B, 8 textos; p03:B327) | 立直 鳴き 断么 清一 対々 国士 降りる 終了 | pantalla de estilo; casillas de 2 letras de ancho |
| p03:B7B5-B7CD | 流局 九種九牌倒牌 四風連打 四人立直 四開槓 三家和 | abortos |
| p01:662B-67BF (404 B) | yaku, 役満, 満貫..., ドラ, 符 飜 | puntuacion; la apuntan p01:661D, p03:AEF7, p03:B787, p04:A9F5/AA33/AA48 y la tabla p01:6664 (p04:A9A9, AE15): se reempaqueta entera |
| letras sueltas | p03:A66C-A698 recuadro de ronda: 東南 + 一二三四 + 局 + 東南西北 + 家; p00:5AC2/5AC9 cifras y 点 | se redibuja la letra, no la cadena |

La tabla final de la traduccion: `textos_en.txt` (la lee tools/traduce.py).

## B. Letra de tiles 8 x 8 (p00:5363 lista X,Y,tiles,0xFE X,Y...,0xFF)

Hoja de tiles en la pagina 1 de la VRAM (p00:53DE: X = (A & 0x1F) x 16, Y = 0xB0 + (A >> 5) x 8),
cargada por pantalla. En la partida (work/g1/vram-108): 01-0A = 0-9, 0B-13 = A-I, 20-30 = J-Z,
31 = (c), 32 = -, 60-84 = katakana y 本 場. **El alfabeto latino ya esta**: el arreglo es cambiar
bytes (y mover la lista si crece). `tools/hoja_tiles.py` pinta la hoja de un volcado.

| Donde | Japones | Ingles ya puesto | Pantalla |
|---|---|---|---|
| p02:98E3 | ポン チー カン ロン | EXIT | menu al tirar otro |
| p02:9902 | カン リーチ ツモ | EXIT | menu en tu turno |
| p02:9D0E | タオパイ (九種九牌) | EXIT | menu de nueve terminales |
| p01:60FA-613F (p00:5EEF-5F35) | スコアー オープン クローズ | EXIT | menu de pausa |
| p01:6140 | ノコリ | | fichas que quedan |
| p03:A699 | x00本 x00本場 | | recuadro de ronda |
| p03:AEB9, p03:B118 | 8 nombres de rivales | | eleccion de rivales, estilo |
| p03:BD33 | 8 nombres | NAME SCORE ROUND PLAYER | resultados por rival |
| p04:B535 (8 listas) | nombre de cada rival | | demo de presentacion |

Nombres (codigos de la hoja de partida): シモン 73 68 61, アフロディーテ 72 77 65 78 79 63 7A,
スナッチャー 70 7B 7C 62 7D 63, ヴェノム 7F 80 81 82, ゴエモン 74 7E 68 61, ポポロン 60 60 65 61,
ペンギン 75 61 76 61, モアイ 68 72 6C.

## C. Dibujos (tiles de imagenes, p00:5911)

| Que | Donde | Peso para jugar |
|---|---|---|
| Titulo de cada rival "騎士代表"... (4 x 2 tiles) y su frase (fila de 6-8 tiles) | demo de presentacion, p04:B545.. filas Y=40/48/58 | ninguno (demo) |
| ポン! チー! ... rojo sobre la cara | p03:A6BE muestra_voz | poco: la voz dice lo mismo |
| 麻雀 de fondo, logotipo, caras de las fichas (萬, vientos, 中) | | se dejan |

Los "dialogos" de p00:576A (letras de 3 x 3 tiles) son los marcos de los retratos, no texto.

## Letras de 16 puntos que se dibujan sueltas (medido: work/textos*, vuelta de p00:5B2B)

Cifras 01-0A (puntos, fu), numerales 一-十 0B-14 (han: p04:A9BC `add a,0Ah`; total p04:AA19),
東南西北 15-18 y 局 2F, 家 1B (recuadro de ronda p03:A66C-A698; 東 tambien en p02:8F87), 飜 72
(p04:A9D4), 点 91 (p04:AA27), 符 92 (cadena p01:663B). Son 29 letras: se redibujan (E, S, W, N,
1-10, HAN, PT, FU...) sin tocar codigo, y no se pueden usar para pares. Quedan 160 casillas.

## Cuentas (antes de montar; tools/traduce.py da las de verdad)

93 cadenas, 413 casillas, 137 casillas distintas de 2 letras: 137 + 29 = 166 de 189. Cabe.
Zona de yaku p01:662B-67BF (404 B): las cadenas pasan de ~242 B a 325 B (+83).

## Espacio libre (tiras de 0xFF/0x00 de 24 B o mas)

p00-p03: nada. p04: 105 B en p04:BF97 (se ve en 0xBF97 con los bancos 1,2,4 de la puntuacion: los
yaku que no quepan en p01 van alli, la tabla p01:6664 apunta a ellos; p03:AEF7 y B787 leen con p03
puesto: sus cadenas se quedan en p01). OJO, medido despues en openMSX: p00:5ACF pone los bancos 5-6
para cada letra y al volver deja los 1-2-3, asi que una cadena en p04 solo se lee hasta su primera
letra; las llamadas p04:A9B0, AE1E y AA41 pasan por una rutina que la copia a la pila (p04:BF97). p06 208, p09 163, p15 118 (p15 AD8B.. ya lo usa el tutorial),
p14: 1.157 B que ya usa el tutorial (fuente y paginas).

Listas de tiles (B) en p01-p04 sin hueco: los nombres y los menus no pueden crecer. Salida sin
mover nada: redibujar los tiles de katakana (60-84, datos sin comprimir de p00:5911) como pares de
letras de media anchura (8 x 8 en 512 puntos) y dejar cada lista con sus mismos bytes. PON, CHI, KAN,
RON y OPEN caben con las letras enteras que ya hay (0B-30).

## Lo que hay que leer para jugar

A entero, B entero. C queda fuera del minimo (se decide al disenar el parche).
