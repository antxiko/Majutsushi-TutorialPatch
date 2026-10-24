# omsx_pcs.tcl - apunta que codigo escribe en el VDP (puertos 0x98, 0x99, 0x9B) entre dos instantes:
# cada PC distinto una vez, con la cima de la pila (quien llamo) y los bancos de 0xF0F1-3.
# Variables: PCS_SALIDA (fichero), PCS_DESDE, PCS_HASTA (segundos), PCS_TECLAS "t:fila:mascara ..."
proc opcion {nombre porDefecto} {
    global env
    if {[info exists env($nombre)]} { return $env($nombre) }
    return $porDefecto
}
set throttle off
set ::f [open [opcion PCS_SALIDA work/pcs.txt] w]
array set ::visto {}
proc apunta {puerto} {
    set pc [reg PC]
    set sp [reg SP]
    set ret [expr {[peek $sp] | ([peek [expr {$sp + 1}]] << 8)}]
    set clave [format "%04X-%04X" $pc $ret]
    if {[info exists ::visto($clave)]} return
    set ::visto($clave) 1
    puts $::f [format "%s puerto=%02X pc=%04X pila=%04X bancos=%d,%d,%d estado=%d.%d t=%.2f" \
        $clave $puerto $pc $ret [peek 0xF0F1] [peek 0xF0F2] [peek 0xF0F3] [peek 0xC000] [peek 0xC001] \
        [expr {[machine_info time]}]]
}
foreach k [opcion PCS_TECLAS {}] {
    lassign [split $k :] t fi m
    after time $t "keymatrixdown $fi $m; after time 0.15 {keymatrixup $fi $m}"
}
after time [opcion PCS_DESDE 24] {
    debug set_watchpoint write_io 0x98 {} {apunta 0x98}
    debug set_watchpoint write_io 0x99 {} {apunta 0x99}
    debug set_watchpoint write_io 0x9B {} {apunta 0x9B}
}
after time [opcion PCS_HASTA 27] {close $::f; exit}
