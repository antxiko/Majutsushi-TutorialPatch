# Hai no Majutsushi — tutorial patch

牌の魔術師 (*Hai no Majutsushi - Mahjong 2*; Konami, 1989, RC-765) is a mahjong game for the MSX2 with all its menus and messages in Japanese. This patch adds a short **tutorial in English** to the cartridge: press **F1** on the first menu and five pages explain how to play, the two menus, the calls, the rivals and the music keys. Space turns the page; after the last one you are back at the menu. The rest of the game is unchanged.

**1,264** bytes changed in **6** places · **1,302**-byte IPS · all in space the cartridge does not use · no ROM distributed

![The first page of the tutorial](imagenes/tutorial_1.png)

## How to use it

1. On the title screen press space: the first menu appears (練習対局, practice; 実戦対局, real game).
2. Press **F1**. The tutorial opens.
3. **Space** for the next page. After the fifth one the menu comes back, and the game carries on as usual.

| | |
|---|---|
| ![page 2](imagenes/tutorial_2.png) | ![page 3](imagenes/tutorial_3.png) |
| ![page 4](imagenes/tutorial_4.png) | ![page 5](imagenes/tutorial_5.png) |

## What you need

- **The game ROM**, which this repository does not distribute: *Hai no Majutsushi - Mahjong 2* (Konami, 1989, RC-765), 131,072 bytes, sha256 `7839c843dc787e01765c1ba3efbd26dcf5209d27e38bcee1345db3b3cffdf5db`.
- Any IPS tool (Lunar IPS, Floating IPS, RomPatcher.js). Apply [parche/majutsushi_tutorial.ips](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/parche/majutsushi_tutorial.ips) to the ROM and you get the patched one, sha256 `7bd8b0686b13c6c57fcff8f89f79af7d8622e4fcec1a5b0b6d1c040e229ce543`.

In openMSX the cartridge needs its mapper (Konami with a DAC):

```
openmsx -machine C-BIOS_MSX2 -cart majutsushi_tutorial.rom -romtype Majutsushi
```

## Building it

With Python 3 and [pasmo](https://pasmo.speccy.org/) in the PATH, and the ROM in the root as `majutsushi.rom`:

```
python tools/construye.py majutsushi.rom
```

It assembles [src/tutorial.asm](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/src/tutorial.asm), checks that every place it writes holds what the original cartridge has there (or 0xFF where it uses free space), and writes `work/majutsushi_tutorial.rom` and the IPS. It refuses any other ROM. The texts and the font are in [tools/textos.py](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/tools/textos.py), which writes `src/datos.inc`. `python -m unittest discover -s tests` runs the 6 tests: the texts are the ones in the source, the IPS only touches the six declared places, and, with the ROM in the root, the IPS is the one the source gives and original + IPS is the original byte for byte outside those places.

## How it works

- **The hook.** The first menu runs every frame from p00:4396 (entry 1 of the state table at p00:4313). That block, together with the cursor sound and the cursor drawing behind it, is 61 bytes. The patch writes it again in the same 61 bytes: `bit 4,a` instead of `ld c,a / and 10h / ld a,c`, and the two cursor sprites written with `ld l,4` instead of switching between HL and HL' with `exx`. That leaves room to look at F1 on entry (bit 0 of 0xC00C, the function keys just pressed) and for the jump to the tutorial. The cursor and its sound move a few bytes, so the three instructions that enter them are corrected (p00:436F, 4834 and 483B). Nothing else changes in bank 0.
- **The tutorial.** 104 bytes in bank 15, at 0xAD8B, in the 117 bytes of 0xFF between a tile table and the voice at 0xAE00. It switches banks 13-14-15 in with the cartridge's own routine (p00:4246) and draws with the cartridge's routines: it clears the screen (p00:4E50, p00:4FE5), waits for the VDP (p00:4EEA), draws each letter as an 8 × 8 one-bit tile (p00:52A3) and reads the keys (p00:55F0). On leaving, it sets the menu back to step 0, so the menu draws itself again, and puts back banks 1-2-3, which are the ones the menu has (measured in openMSX).
- **The texts.** 1,097 bytes at the end of bank 14 (0xBB7B), in the cartridge's largest stretch of 0xFF (1,157 bytes): a 35-letter 5 × 7 font (280 bytes) and the five pages (817 bytes), one byte per letter.
- **The free space is measured.** In a 15-minute openMSX run of title, menus and play, with a watchpoint on every ROM read, nobody reads the 0xFF at the end of bank 14 or the 0xFF at p15:AD8B.
- The addresses come from the [annotated disassembly of Hai no Majutsushi](https://antxiko.github.io/Majutsushi-disassembly/).

## Tested

In openMSX (C-BIOS MSX2): F1 on the first menu opens the tutorial, the five pages turn with space, the menu comes back, the cursor moves up and down, and choosing practice leads to the second menu. Not tested on a real MSX yet.

## Licence

MIT ([LICENSE](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/LICENSE)) for the patch, the tools and the documentation. The game belongs to its rights holders: see [LEGAL-NOTICE.md](https://github.com/antxiko/Majutsushi-TutorialPatch/blob/main/LEGAL-NOTICE.md).
