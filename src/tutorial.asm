; =============================================================================
; HAI NO MAJUTSUSHI - parche TUTORIAL
; =============================================================================
;   menu       p00:4396-43D2, el paso 1 del menu de modo (練習/実戦), escrito de nuevo en
;              menos sitio: al entrar mira F1 (bit 0 de 0xC00C, recien pulsada) y, si
;              esta, salta al tutorial; si no, hace lo mismo que el original. Mas tres
;              direcciones corregidas (0x4370, 0x4835, 0x483C) y nada mas en el banco 0.
;   tutorial   p15:AD8B (117 bytes a 0xFF entre la tabla de tiles de 0xAAA0 y la
;              voz de 0xAE00), con los bancos 13-14-15 puestos.
;   datos      p14:BB7B (1.157 bytes a 0xFF al final del banco), con el banco 14
;              en 0x8000: la fuente y las paginas (tools/textos.py).
;
; Todo lo que dibuja lo hace con las rutinas del propio cartucho.
; =============================================================================

LIMPIA          equ 04E50h      ; apaga la pantalla, quita los sprites, borra la VRAM visible
PANT_ON         equ 04E69h      ; enciende la pantalla
HMMV            equ 04FE5h      ; rellena un rectangulo: HL origen, BC tamano, A color, D pagina
ESPERA_VDP      equ 04EEAh      ; espera a que el VDP acabe la orden en marcha
TILE_1BIT       equ 052A3h      ; dibuja 8 x 8 de 1 bit (HL) en D,E con el color C (A = 0)
MANDOS          equ 055F0h      ; lee teclado y mandos: 0xC007 = lo recien pulsado
BANCOS_13_14_15 equ 04246h      ; pone los bancos 13, 14 y 15 (y sus copias en 0xF0F1-3)
BANCOS_123      equ 04207h      ; vuelve a poner los bancos 1-2-3
SONIDO_06       equ 04116h      ; pide el sonido del cursor
ELEGIDO         equ 043D3h      ; se ha elegido una opcion del menu
OPCION          equ 0C00Fh      ; la opcion del menu: 0 o 1
TECLAS          equ 0C007h
TECLAS_F        equ 0C00Ch
PASO            equ 0C001h
PAGINA_TILE     equ 0FAF6h      ; 0 = el tile va a la pagina visible


COLOR           equ 14              ; blanco en la paleta de los menus

; ------------------------------------------------------------------ el menu, compactado
; El bloque 0x4396-0x43D2 del cartucho (61 bytes) es el paso 1 del estado 3 (entrada 1 de la tabla
; de 0x4313), el sonido del cursor y el cursor. Escrito de nuevo hace lo mismo en menos sitio:
;   - `bit 4,a` en vez de `ld c,a / and 10h / ld a,c` (C no la lee nadie: 0x43D3 tampoco)
;   - el cursor escribe sus dos sprites con `ld l,4` en vez de alternar HL y HL' con exx
; y deja sitio para mirar F1 al entrar y para el salto al tutorial. El cursor y el sonido cambian de
; sitio, asi que se corrigen las tres instrucciones que entran en ellos (0x436F, 0x4834, 0x483B).
                org 04370h
                defw cursor             ; call cursor en 0x436F (el paso 0 del menu)

                org 04396h
gancho:         ld a,(TECLAS_F)
                rra                     ; F1 recien pulsada al acarreo
                jr c,al_tutorial
                ld a,(TECLAS)
                bit 4,a                 ; espacio o boton: elegido
                jr nz,ELEGIDO
                ld de,OPCION
                and 003h                ; arriba o abajo: cambia de opcion
                ld c,058h               ; la X del cursor
                jr z,cursor
                ld a,(de)
                xor 001h
                ld (de),a
sonido_cursor:  call SONIDO_06
cursor:         ld a,(de)               ; la Y del cursor: 0x5C la opcion 0, 0x74 la otra
                and a
                ld a,05Ch
                jr z,cursor_y
                ld a,074h
cursor_y:       ld hl,0CC00h            ; dos sprites en la copia de la tabla de atributos
                ld (hl),a
                inc l
                ld (hl),c
                inc l
                ld (hl),038h
                ld l,004h
                ld (hl),a
                inc l
                ld (hl),c
                inc l
                ld (hl),03Ch
                ret
al_tutorial:    call BANCOS_13_14_15    ; el tutorial en 0xA000 y sus datos en 0x8000
                jp tutorial
fin_menu:                               ; tiene que ser 0x43D3

                org 04835h
                defw cursor             ; jp z,cursor en 0x4834 (el otro menu de dos opciones)
                org 0483Ch
                defw sonido_cursor      ; jp sonido_cursor en 0x483B

; ------------------------------------------------------------------ el tutorial
                org 0AD8Bh
tutorial:       ld hl,paginas
pagina:         push hl
                call LIMPIA
                ld hl,0
                ld bc,000D8h
                ld a,0FFh               ; fondo: el color 15 (negro en la paleta de los menus)
                ld d,0
                call HMMV
                call ESPERA_VDP         ; las letras se escriben con la CPU: el relleno tiene que haber acabado
                pop hl
                ld de,00808h            ; D = X (en bytes), E = Y
letra:          ld a,(hl)
                inc hl
                cp 0FFh
                jr z,espera
                cp 0FEh
                jr nz,no_linea
                ld d,8
                ld a,e
                add a,10
                ld e,a
                jr letra
no_linea:       and a
                jr z,avanza             ; 0 = espacio
                push hl
                dec a
                ld l,a
                ld h,0
                add hl,hl
                add hl,hl
                add hl,hl
                ld bc,fuente
                add hl,bc
                xor a
                ld (PAGINA_TILE),a
                ld c,COLOR
                call TILE_1BIT
                pop hl
avanza:         ld a,d
                add a,8
                ld d,a
                jr letra
espera:         push hl
                call PANT_ON
tecla:          halt
                call MANDOS
                ld a,(TECLAS)
                and 010h                ; espacio o boton
                jr z,tecla
                pop hl
                ld a,(hl)
                cp 0FDh                 ; fin del tutorial
                jr nz,pagina
                xor a
                ld (PASO),a             ; el menu se vuelve a dibujar (paso 0)
                jp BANCOS_123           ; y vuelve con los bancos 1-2-3
fin_tutorial:

; ------------------------------------------------------------------ los datos
                org 09B7Bh              ; p14:BB7B con el banco 14 en 0x8000
                include "datos.inc"
fin_datos:
