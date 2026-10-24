# lanza_tiles.ps1 <dir> <hasta> "<teclas>" "<pokes>" "<fotos>" <rom>: UN openMSX (MSX2) con tools/omsx_tiles.tcl, fuera del sandbox.
param([string]$dir, [string]$hasta = "120", [string]$teclas = "", [string]$pokes = "", [string]$fotos = "", [string]$rom = "majutsushi.rom", [string]$voz = "0", [string]$yaku = "")
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz
$env:TIL_SALIDA = "work/$dir"
$env:TIL_HASTA = $hasta
$env:TIL_TECLAS = $teclas
$env:TIL_POKES = $pokes
$env:TIL_FOTOS = $fotos
$env:TIL_VOZ = $voz
$env:TIL_YAKU = $yaku
New-Item -ItemType Directory -Force "work/$dir" | Out-Null
$args_ = @("-machine", "C-BIOS_MSX2", "-carta", $rom, "-romtype", "Majutsushi", "-script", "tools/omsx_tiles.tcl")
Start-Process -FilePath "C:\Program Files\openMSX\openmsx.exe" -ArgumentList $args_ -Wait -WindowStyle Minimized
"hecho" | Out-File -Encoding ascii "work/$dir/fin.txt"
