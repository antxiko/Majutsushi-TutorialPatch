# Hai no Majutsushi — English translation and tutorial

牌の魔術師 (*Hai no Majutsushi - Mahjong 2*; Konami, 1989, RC-765) is a mahjong game for the MSX2 with all its menus and messages in Japanese. This patch puts **everything you need to read to play in English** — the menus, the rules and style screens, the rivals' names, the call menus, the yaku and the scores, the end-of-hand messages and the red PON! / CHI! / KAN! / RON! / TSUMO! / RIICHI! call-outs — and adds a **tutorial** on **F1** in the first menu: nine screens on the tiles, the goal, the sets, the calls, riichi and tsumo, the menus and the music keys.

**15,508** bytes changed · **15,936**-byte IPS · 144 new letters, 35 new small tiles, 6 new call-outs · no ROM distributed

![The tutorial: the menu, F1, the nine screens and back to the menu](imagenes/tutorial.gif)

| Japanese | English |
|---|---|
| ![first menu, Japanese](imagenes/modo_jp.png) | ![first menu, English](imagenes/modo_en.png) |
| ![settings menu, Japanese](imagenes/ajustes_jp.png) | ![settings menu, English](imagenes/ajustes_en.png) |
| ![rules, Japanese](imagenes/reglas_jp.png) | ![rules, English](imagenes/reglas_en.png) |
| ![rivals' style, Japanese](imagenes/estilo_jp.png) | ![rivals' style, English](imagenes/estilo_en.png) |

| | | |
|---|---|---|
| ![the seat draw](imagenes/partida_sorteo.png) | ![the call menu](imagenes/partida_llamada.png) | ![PON!](imagenes/partida_pon.png) |
| ![the yaku and the score](imagenes/partida_yaku.png) | ![a drawn hand](imagenes/partida_aborto.png) | |

## How to use it

1. On the title screen press space: the first menu appears (PRACTICE, MATCH).
2. **F1** opens the tutorial; **space** turns the page, and after the ninth the menu comes back.
3. In PRACTICE, **down** on your turn opens a box with SCORE and OPEN (OPEN shows the rivals' hands).

## What you need

- **The game ROM**, which this repository does not distribute: *Hai no Majutsushi - Mahjong 2* (Konami, 1989, RC-765), 131,072 bytes, sha256 `7839c843dc787e01765c1ba3efbd26dcf5209d27e38bcee1345db3b3cffdf5db`.
- Any IPS tool (Lunar IPS, Floating IPS, RomPatcher.js). Apply [parche/majutsushi_en.ips](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/parche/majutsushi_en.ips) to the ROM and you get the patched one, sha256 `334c944a39b3e36eee541c01c7b38b0a6d29704442bd6e24cbae06ee818899ff`.

In openMSX the cartridge needs its mapper (Konami with a DAC):

```
openmsx -machine C-BIOS_MSX2 -cart majutsushi_en.rom -romtype Majutsushi
```

## Building it

With Python 3, Pillow and [pasmo](https://pasmo.speccy.org/) in the PATH, and the ROM in the root as `majutsushi.rom`:

```
python tools/construye.py majutsushi.rom
```

It assembles the tutorial ([src/tutorial.asm](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/src/tutorial.asm)), applies the translation from [traduccion/textos_en.txt](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/traduccion/textos_en.txt) with [tools/traduce.py](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/tools/traduce.py), checks that every place it writes holds what the original cartridge has there, and writes `work/majutsushi_en.rom` and the IPS. It refuses any other ROM. `python -m unittest discover -s tests` runs the 13 tests. What was measured before translating (every text, how it is drawn, where it is, how much room there is) is in [traduccion/inventario.md](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/traduccion/inventario.md).

## How it works

The game writes in three different ways, and each one is translated in its own way.

- **The 16-dot letters** (menus, rules, yaku, scores; the routine at p00:5ACD). Each letter is 32 × 16 dots of SCREEN 7 in 64 bytes (banks 5-6), and the font has 189 of them. The translation redraws them as **pairs of letters** — the Konami 8 × 8 alphabet at double size, two per kanji cell — or three or four narrower ones where the space is tight (the style labels, HAN, PTS). 144 cells are new; the letters the code draws one by one are redrawn in place: the han numerals 一 to 十 become digits, 東南西北 become E S W N, 家 becomes SEAT, 飜 HAN, 点 PTS. The digits and the ○ and × of the rules screen stay as they are.
- **The strings move.** English needs more bytes than kanji. The strings of each bank are placed again in the room of the old ones and every pointer is corrected (the `ld hl` of each call, the yaku table at p01:6664, the limit tables at p01:6640 and 664E). The yaku do not fit in bank 1: the rest go to the free bytes at the end of bank 4. The text routine puts banks 5-6 in for every letter and leaves banks 1-2-3 when it returns, so a string in bank 4 would only be read up to its first letter: the three calls that write names from the tables (p04:A9B0, AE1E, AA41) go first through a 36-byte routine at p04:BF97 that copies the string onto the stack and writes it from there. Three windows needed a byte changed: the rules screen writes 12 texts instead of 16, its second column moves six dots right and the first four left so SHIISANPUTAA fits, and SCREEN is centred in its box.
- **The 8 × 8 tiles** (call menus, names; the list routine at p00:5363). The tile sheet already has the whole Latin alphabet: PON, CHI, KAN, RON, OPEN, HIDE and DRAW are written with it. The 37 katakana tiles (p07:6138) are redrawn as 35 tiles of **two narrow letters** each, so the names and RIICHI, TSUMO, SCORE and LEFT fit in exactly the same bytes as the katakana. The names change in the eleven lists where they appear (rival choice, style, results and the attract introduction).
- **The call-outs** (p00:58A2) are 16 sprite patterns per word, RLE-compressed: red letters on top and a dark outline below. The six are drawn again with a heavy slanted letter; the outline sprite is the whole shape one dot fatter (the red one covers it), which compresses better: 1,970 bytes where the six old ones took 2,411.
- **The tutorial** is the one from the earlier version of this patch, with the calls, riichi/tsumo and menus screens rewritten in English as the game now shows them (it used to point at the katakana and the kanji). Its hook in the first menu is the same: 61 bytes of p00:4396 written again in the same space, and the screens in the free bytes at the end of bank 14 and at p15:AD8B.
- The addresses come from the [annotated disassembly of Hai no Majutsushi](https://antxiko.github.io/Majutsushi-disassembly/).

What stays in Japanese: the captions of the attract introduction (each rival's title and phrase), the title logo, the big 麻雀 behind it, and the faces of the tiles (萬 and the winds, as on real tiles).

## Tested

In openMSX (C-BIOS MSX2), with captures taken with the throttle on: the first and settings menus, rules, style and rival choice, the seat draw, the round box, the call menus (with a rival's discard, on your turn, the pause box with SCORE, OPEN and LEFT), the yaku lists with FU, HAN and PTS (the rarest yaku forced from the debugger to see the ones in bank 4), DRAW, GAME END, NEXT and QUIT, the results table, the names in the introduction, the PON! and CHI! call-outs and the nine tutorial screens. Checked only in the code and by measuring the windows, not seen on screen: 9 TERMINALS, 4 WINDS, 4 RIICHI, 4 KANS, 3 RON and the disk SAVE menu. Not tested on a real MSX yet.

## Licence

MIT ([LICENSE](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/LICENSE)) for the patch, the tools and the documentation. The game belongs to its rights holders: see [LEGAL-NOTICE.md](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/LEGAL-NOTICE.md).
