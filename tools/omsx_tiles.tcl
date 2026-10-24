# omsx_tiles.tcl - apunta cada lista de tiles de 8 x 8 que dibuja el cartucho (p00:5363 y 5369 HL =
# X, Y, tiles; p00:58C5/58C9 bloques; p00:5C92 texto de tiles), cada imagen (p00:5911, HL = lista) y
# cada texto de 16 puntos (p00:5ACF), con el estado y los bancos; la primera vez que sale cada lista
# vuelca la VRAM (128 KB) y los registros/paleta para leer los tiles con tools/hoja_tiles.py.
# Variables: TIL_SALIDA (carpeta), TIL_HASTA (segundos), TIL_TECLAS "t:fila:mascara[:dur] ...",
# TIL_POKES "t:dir:valor ...", TIL_FOTOS "t1 t2 ..." (capturas a esos segundos)
proc opcion {nombre porDefecto} {
    global env
    if {[info exists env($nombre)]} { return $env($nombre) }
    return $porDefecto
}
set ::SALIDA [opcion TIL_SALIDA work/tiles]
file mkdir $::SALIDA
set throttle off
# el throttle se pide y se suelta con un contador: varias capturas pueden esperar a la vez
set ::pedidos 0
proc pide {} { incr ::pedidos; set ::throttle on }
proc suelta {} { incr ::pedidos -1; if {$::pedidos <= 0} { set ::pedidos 0; set ::throttle off } }
set ::f [open [file join $::SALIDA tiles.txt] w]
array set ::visto {}
set ::n 0
proc bytes {hl cuantos} {
    set l {}
    for {set i 0} {$i < $cuantos} {incr i} {
        set b [peek [expr {($hl + $i) & 0xFFFF}]]
        lappend l [format %02X $b]
        if {$b == 0xFF} break
    }
    return $l
}
proc vuelca {n} {
    set f [open [file join $::SALIDA "vram-$n.bin"] wb]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block VRAM 0 131072]
    close $f
    set g [open [file join $::SALIDA "vdp-$n.txt"] w]
    for {set i 0} {$i < 47} {incr i} { puts $g [format "R%d = 0x%02X" $i [debug read "VDP regs" $i]] }
    for {set i 0} {$i < 16} {incr i} {
        puts $g [format "P%d = 0x%04X" $i [expr {[debug read "VDP palette" [expr {$i*2}]] | ([debug read "VDP palette" [expr {$i*2+1}]] << 8)}]]
    }
    close $g
}
proc apunta {tipo} {
    set hl [reg HL]
    set sp [reg SP]
    set vuelta [expr {[peek $sp] | ([peek [expr {$sp + 1}]] << 8)}]
    set k "$tipo:[format %04X $hl]:[peek 0xF0F1],[peek 0xF0F2],[peek 0xF0F3]"
    if {[info exists ::visto($k)]} return
    incr ::n
    set ::visto($k) $::n
    puts $::f [format "%s %04X desde=%04X DE=%04X estado=%d.%d bancos=%d,%d,%d t=%.1f n=%d : %s" $tipo $hl $vuelta \
        [reg DE] [peek 0xC000] [peek 0xC001] [peek 0xF0F1] [peek 0xF0F2] [peek 0xF0F3] [machine_info time] $::n \
        [bytes $hl 64]]
    flush $::f
    if {$tipo ne "I"} {
        # la hoja de tiles ya esta cargada cuando se dibuja la lista; la captura, un poco despues
        vuelca $::n
        after time 0.8 "screenshot [file join $::SALIDA s$::n.png]"
        # captura buena: con throttle (sin el, la captura va por detras de la VRAM), 1,2 s despues
        pide
        after realtime 1.2 "screenshot [file join $::SALIDA s${::n}b.png]; suelta"
        # la captura va por detras de la VRAM sin throttle: el volcado de medio segundo despues es el bueno
        after time 0.5 "vuelca ${::n}b"
    }
}
debug set_bp 0x5363 {} {apunta S}
debug set_bp 0x58C5 {} {apunta B}
debug set_bp 0x58C9 {} {apunta B}
debug set_bp 0x5C92 {} {apunta X}
debug set_bp 0x5911 {} {apunta I}
debug set_bp 0x5ACF {} {apunta T}
# TIL_VOZ=1: cada vez que alguien canta (p03:A6BE muestra_voz, con el banco 3 en 0xA000) pone el
# throttle (la captura sin throttle va por detras) y captura con el rotulo encima
set ::voces 0
proc voz {} {
    if {[peek 0xF0F3] != 3 || $::voces >= 12} return
    incr ::voces
    set a [expr {[reg AF] >> 8}]
    pide
    after realtime 0.6 "screenshot [file join $::SALIDA voz$::voces-$a.png]; suelta"
}
if {[opcion TIL_VOZ 0] == 1} { debug set_bp 0xA6BE {} voz }
# TIL_YAKU="08 27 ...": en p04:A9A0 (escribe el nombre del yaku A, con el banco 4 en 0xA000) cambia A
# por el siguiente de la lista, para ver nombres de yaku que no salen solos
set ::yakus [opcion TIL_YAKU {}]
proc fuerza_yaku {} {
    if {[peek 0xF0F3] != 4 || [llength $::yakus] == 0} return
    set y [lindex $::yakus 0]
    set ::yakus [lrange $::yakus 1 end]
    reg A [expr {"0x$y"}]
}
if {[llength $::yakus] > 0} { debug set_bp 0xA9A0 {} fuerza_yaku }
foreach k [opcion TIL_TECLAS {}] {
    lassign [split $k :] t fi m d
    if {$d eq ""} { set d 0.15 }
    after time $t "keymatrixdown $fi $m; after time $d {keymatrixup $fi $m}"
}
foreach k [opcion TIL_POKES {}] {
    lassign [split $k :] t d v
    after time $t "poke $d $v"
}
foreach t [opcion TIL_FOTOS {}] {
    after time $t "pide; after realtime 0.5 {screenshot [file join $::SALIDA foto-$t.png]; vuelca f$t; suelta}"
}
after time [opcion TIL_HASTA 120] {close $::f; exit}
