# omsx_tuto.tcl - prueba del parche en openMSX: pulsa espacio hasta que sale el primer menu
# (0xC000 = 3, 0xC001 = 1), pulsa F1 y va pasando las paginas con espacio, con una captura de cada
# una, otra del menu al volver, el cursor abajo y arriba, y otra tras elegir (el juego sigue). Los
# bancos puestos al entrar en el menu quedan en bancos.txt.
#
# Uso: openmsx -machine C-BIOS_MSX2 -carta work/majutsushi_tutorial.rom -romtype Majutsushi
#              -script tools/omsx_tuto.tcl        (las capturas van a TUTO_SALIDA, work/tuto)
set ::SALIDA work/tuto
if {[info exists env(TUTO_SALIDA)]} { set ::SALIDA $env(TUTO_SALIDA) }
file mkdir $::SALIDA
set throttle off
set ::n 0

proc tecla {fila mascara} {
    keymatrixdown $fila $mascara
    after time 0.15 "keymatrixup $fila $mascara"
}
proc foto {nombre} {
    screenshot [file join $::SALIDA "$nombre.png"]
    set f [open [file join $::SALIDA "$nombre.vram"] wb]
    fconfigure $f -translation binary
    puts -nonewline $f [debug read_block VRAM 0 131072]
    close $f
    set g [open [file join $::SALIDA "$nombre.vdp"] w]
    for {set i 0} {$i < 24} {incr i} { puts $g [format "R%d = 0x%02X" $i [debug read "VDP regs" $i]] }
    for {set i 0} {$i < 16} {incr i} {
        puts $g [format "P%d = 0x%04X" $i [expr {[debug read "VDP palette" [expr {$i*2}]] | ([debug read "VDP palette" [expr {$i*2+1}]] << 8)}]]
    }
    close $g
}
proc vigila {} {
    if {[peek 0xC000] == 3 && [peek 0xC001] == 1} {
        set ::throttle on
        set f [open [file join $::SALIDA bancos.txt] w]
        puts $f "bancos al entrar en el menu: [peek 0xF0F1] [peek 0xF0F2] [peek 0xF0F3]"
        close $f
        foto menu
        tecla 6 0x20
        for {set i 1} {$i <= 5} {incr i} {
            after time [expr {3.0 * $i - 1}] "foto pagina$i"
            after time [expr {3.0 * $i}] "tecla 8 0x01"
        }
        after time 17.5 "foto vuelta; puts \"C000=\[peek 0xC000\] C001=\[peek 0xC001\]\""
        after time 18.5 "tecla 8 0x40"
        after time 19.5 "foto abajo"
        after time 20 "tecla 8 0x20"
        after time 21 "foto arriba"
        after time 22 "tecla 8 0x01"
        after time 27 "foto sigue; puts \"C000=\[peek 0xC000\] C001=\[peek 0xC001\]\""
        after time 28 exit
        return
    }
    incr ::n
    if {$::n % 6 == 0} { tecla 8 0x01 }
    if {$::n > 400} { foto atascado; exit }
    after time 0.5 vigila
}
after time 5 vigila
