; =============================================================================
; HAI NO MAJUTSUSHI - parche TUTORIAL
; =============================================================================
;   menu       p00:4396-43D2, el paso 1 del menu de modo (練習/実戦), escrito de nuevo en
;              menos sitio: al entrar mira F1 (bit 0 de 0xC00C, recien pulsada) y, si
;              esta, salta al tutorial; si no, hace lo mismo que el original. Mas tres
;              direcciones corregidas (0x4370, 0x4835, 0x483C) y nada mas en el banco 0.
;   tutorial   p14:BB7B (1.157 bytes a 0xFF al final del banco), con el banco 14 en 0x8000:
;              el codigo principal, la tabla de letras y las nueve pantallas (tools/textos.py).
;              Y p15:AD8B (117 bytes a 0xFF entre la tabla de tiles de 0xAAA0 y la voz de
;              0xAE00), con el banco 15 en 0xA000: el resto del codigo.
;
; No lleva fuente ni dibujos: las fichas, las letras, los katakana y los kanji son los del
; propio cartucho, dibujados con sus rutinas.
; =============================================================================

LIMPIA          equ 04E50h      ; apaga la pantalla, quita los sprites, borra la VRAM visible
HOJA_FICHAS     equ 05746h      ; la hoja de fichas y su paleta en la pagina 1, como al empezar la partida (acaba con los bancos 1-2-3)
DIBUJA_MESA     equ 05A22h      ; dibuja_mesa: el alfabeto y los katakana en la pagina 1 (idem)
ESCRIBE         equ 05ACDh      ; escribe_texto: un texto en kanji del banco 0 (HL) en D,E (idem)
LMMM            equ 05151h      ; copia un rectangulo: HL origen, DE destino, BC tamano, A orden
PANT_ON         equ 04E69h      ; enciende la pantalla
HMMV            equ 04FE5h      ; rellena un rectangulo: HL origen, BC tamano, A color, D pagina
MANDOS          equ 055F0h      ; lee teclado y mandos: 0xC007 = lo recien pulsado
BANCOS_13_14_15 equ 04246h      ; pone los bancos 13, 14 y 15 (y sus copias en 0xF0F1-3)
BANCOS_123      equ 04207h      ; vuelve a poner los bancos 1-2-3
SONIDO_06       equ 04116h      ; pide el sonido del cursor
ELEGIDO         equ 043D3h      ; se ha elegido una opcion del menu
OPCION          equ 0C00Fh      ; la opcion del menu: 0 o 1
TECLAS          equ 0C007h
TECLAS_F        equ 0C00Ch
PASO            equ 0C001h



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
; Todo lo que se ve sale de la pagina 1 de la VRAM tal como la deja la mesa del juego: las letras
; (16 x 8) y los katakana de las filas 0xB0-0xC8 y la hoja de fichas (24 x 18), cargadas con p00:5746
; y p00:5A22, las dos rutinas con las que p00:495A prepara la mesa. Cada cosa es una
; copia LMMM (p00:5151) a la pagina 0. Las rutinas del juego que cambian de banco (la mesa y los
; kanji) se llaman dejando en la pila p00:4246 como vuelta: pone los bancos 13-14-15 y vuelve aqui.
                org 09B7Bh              ; p14:BB7B con el banco 14 en 0x8000
tutorial:       call LIMPIA             ; la pantalla apagada mientras se carga la mesa
                ld hl,cargada
                push hl
                ld hl,BANCOS_13_14_15
                push hl
                ld hl,DIBUJA_MESA
                push hl
                jp HOJA_FICHAS          ; HOJA_FICHAS -> DIBUJA_MESA -> 4246 -> cargada
cargada:        ld hl,diapos

diapo:          push hl
                call LIMPIA
                ld hl,0
                ld bc,000D8h
                ld a,0FFh               ; el fondo del color 15, el de detras de las letras
                ld d,0
                call HMMV
                pop hl
elemento:       ld e,(hl)               ; Y
                inc hl
                ld a,e
                inc a
                jp z,espera             ; 0xFF: se acaba la pantalla
                ld d,(hl)               ; X (en unidades de 2 puntos)
                inc hl
                bit 7,(hl)
                jp z,palabras           ; texto empaquetado
bytes:          ld a,(hl)               ; renglon de bytes: fichas, katakana, huecos, kanji
                inc hl
                cp 0FEh
                jr z,elemento
                cp 0C0h
                jp z,kanji
                ld bc,bytes             ; cada dibujo vuelve aqui
                push bc
                cp 080h
                jr c,letra
                and 07Fh
                jr z,hueco
                push hl                 ; la ficha A: palo en los bits 4-5, numero en 0-3
                push de
                ld c,a
                and 00Fh
                dec a
                ld b,a
                add a,a
                add a,b
                add a,a
                add a,a                 ; 12 x (numero - 1)
                bit 4,c
                jr z,ficha_x
                add a,06Ch              ; los palos 1 y 3, en la mitad derecha de la hoja
ficha_x:        ld h,a
                xor a
                bit 5,c
                jr z,ficha_y
                ld a,012h               ; los palos 2 y 3, una fila mas abajo
ficha_y:        ld l,a
                ld bc,00C12h            ; 24 x 18 puntos
                jr copia
hueco:          ld b,6
                jr avanza
letra:          and a                   ; A = fila x 32 + columna en la rejilla de 0xB0; 0 = espacio
                ld b,8
                jr z,avanza
                push hl
                push de
                ld c,a
                and 01Fh
                add a,a
                add a,a
                add a,a
                ld h,a                  ; 8 x columna
                ld a,c
                and 060h
                rrca
                rrca
                add a,0B0h
                ld l,a                  ; 0xB0 + 8 x fila
                ld bc,00808h            ; 16 x 8 puntos
copia:          push bc
                ld a,028h               ; de la pagina 1 a la 0, transparente
                call LMMM
                pop bc
                pop de
                pop hl
avanza:         ld a,d
                add a,b
                ld d,a
                ret

                include "datos.inc"     ; la tabla de las letras de 5 bits y las pantallas
fin_datos:

; ------------------------------------------------------------------ el resto, en el banco 15
                org 0AD8Bh              ; p15:AD8B, con el banco 15 en 0xA000
kanji:          ld c,(hl)               ; la direccion del texto en el banco 0
                inc hl
                ld b,(hl)
                inc hl
                push hl
                ld hl,kanji_fin
                push hl
                ld hl,BANCOS_13_14_15
                push hl
                ld h,b
                ld l,c
                jp ESCRIBE              ; ESCRIBE -> 4246 -> kanji_fin
kanji_fin:      pop hl
                jp bytes

palabras:       ld b,(hl)               ; tres letras de 5 bits en 16: 0aaaaabb bbbccccc
                inc hl
                ld c,(hl)
                inc hl
                push bc
                ld a,b
                rrca
                rrca
                call letra5             ; aaaaa
                pop bc
                push bc
                ld a,b
                and 003h
                ld b,a
                ld a,c
                and 0E0h
                or b
                rlca
                rlca
                rlca
                call letra5             ; bbbbb (la b de 0aaaaabb queda en los bits 4-3)
                pop bc
                push bc
                ld a,c
                call letra5             ; ccccc
                pop bc
                jr palabras
letra5:         and 01Fh                ; 0: se acaba el renglon
                jr z,fin_texto
                push hl
                ld hl,tabla5-1          ; el codigo de 5 bits -> la letra de la rejilla
                add a,l
                ld l,a
                jr nc,letra5_t
                inc h
letra5_t:       ld a,(hl)
                pop hl
                jp letra                ; (su ret vuelve a palabras)
fin_texto:      pop af                  ; la vuelta de letra5
                pop af                  ; y el BC guardado
                jp elemento

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
                jp nz,diapo
                xor a
                ld (PASO),a             ; el menu se vuelve a dibujar (paso 0)
                jp BANCOS_123           ; y vuelve con los bancos 1-2-3
fin_tutorial:
