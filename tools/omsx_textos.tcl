# omsx_textos.tcl - apunta cada texto de 16 puntos que dibuja el cartucho (entrada comun de las
# rutinas de texto, p00:5ACF: HL = la cadena, DE = la posicion) y los dialogos (p00:576A), con el
# estado del juego y una captura la primera vez que sale cada cadena. Pulsa teclas con una secuencia
# pseudoaleatoria fija para recorrer menus y partida.
#
# Variables: TXT_SALIDA (carpeta, work/textos), TXT_HASTA (segundos emulados, 900)
proc opcion {nombre porDefecto} {
    global env
    if {[info exists env($nombre)]} { return $env($nombre) }
    return $porDefecto
}
set ::SALIDA [opcion TXT_SALIDA work/textos]
file mkdir $::SALIDA
set throttle off
set ::f [open [file join $::SALIDA textos.txt] w]
array set ::visto {}
set ::n 0
proc cadena {hl} {
    set l {}
    for {set i 0} {$i < 48} {incr i} {
        set b [peek [expr {($hl + $i) & 0xFFFF}]]
        if {$b == 0xFF} break
        lappend l [format %02X $b]
    }
    return $l
}
proc texto {tipo} {
    set hl [reg HL]
    set k "$tipo:[cadena $hl]"
    if {![info exists ::visto($k)]} {
        incr ::n
        set ::visto($k) $::n
        puts $::f [format "%s %04X DE=%04X estado=%d.%d bancos=%d,%d,%d t=%.1f n=%d : %s" $tipo $hl [reg DE] \
            [peek 0xC000] [peek 0xC001] [peek 0xF0F1] [peek 0xF0F2] [peek 0xF0F3] [machine_info time] $::n [cadena $hl]]
        flush $::f
        after time 1.5 "screenshot [file join $::SALIDA t$::n.png]"
    }
}
debug set_bp 0x5ACF {} {texto T}
debug set_bp 0x576A {} {texto D}
# las letras sueltas (p00:5B2B, la entrada comun de dibuja_letra y sus variantes): A = el codigo; se
# apunta quien llama (la direccion de vuelta en la pila) y el estado
proc letra {} {
    set a [expr {[reg AF] >> 8}]
    set sp [reg SP]
    set vuelta [expr {[peek $sp] | ([peek [expr {$sp + 1}]] << 8)}]
    set k "L:[format %04X $vuelta]:[format %02X $a]"
    if {![info exists ::visto($k)]} {
        set ::visto($k) 1
        puts $::f [format "L %04X DE=%04X estado=%d.%d bancos=%d,%d,%d t=%.1f : %02X" $vuelta [reg DE]             [peek 0xC000] [peek 0xC001] [peek 0xF0F1] [peek 0xF0F2] [peek 0xF0F3] [machine_info time] $a]
        flush $::f
    }
}
debug set_bp 0x5B2B {} letra
# teclas: espacio, arriba, abajo, izquierda, derecha y ESC, con un generador lineal fijo
set ::semilla 12345
proc pulsa {} {
    set ::semilla [expr {($::semilla * 1103515245 + 12345) & 0x7FFFFFFF}]
    set r [expr {($::semilla >> 16) % 10}]
    switch $r {
        0 - 1 - 2 - 3 { set fm {8 0x01} }
        4 { set fm {8 0x20} }
        5 - 6 { set fm {8 0x40} }
        7 { set fm {8 0x10} }
        8 { set fm {8 0x80} }
        9 { set fm {7 0x04} }
    }
    lassign $fm fila mascara
    keymatrixdown $fila $mascara
    after time 0.12 "keymatrixup $fila $mascara"
    after time 0.6 pulsa
}
if {[opcion TXT_AZAR 1] == 1} { after time 12 pulsa } else {
    # espacio cada 2 s: juega manos (como la pasada de cobertura)
    proc espacio {} { keymatrixdown 8 0x01; after time 0.12 {keymatrixup 8 0x01}; after time 2 espacio }
    after time 13 espacio
}
after time [opcion TXT_HASTA 900] {close $::f; exit}
