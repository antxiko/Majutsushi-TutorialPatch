"""Lo que la web dice de este juego (la maquinaria de tools/ no nombra ninguno)."""
NOMBRE = "Hai no Majutsushi — English translation and tutorial"
COMPANIA = "Konami"
ANIO = 1989
REPOSITORIO = "https://github.com/antxiko/Majutsushi-TutorialPatch"
PIE_LEGAL = {
    "es": "<em>Hai no Majutsushi - Mahjong 2</em> lo public&oacute; Konami para MSX2 en 1989; "
          "son 128 KB. Todos los derechos sobre el juego siguen siendo de sus "
          "titulares. Esto es un parche extraoficial: aqu&iacute; nunca se "
          "distribuye la imagen del cartucho.",
    "en": "<em>Hai no Majutsushi - Mahjong 2</em> was published by Konami for the MSX2 in 1989; "
          "it is 128 KB. All rights in the game remain with their holders. This "
          "is an unofficial patch: the cartridge image is never distributed here.",
}

# El parche para descargar, que la web pone bajo el titulo: (fichero, rotulo)
DESCARGAS = [
    ("parche/majutsushi_en.ips",
     {"es": "Descargar el parche IPS", "en": "Download the IPS patch"}),
]
DESCARGAS_NOTA = {
    "es": "22.997 bytes. Se aplica a tu ROM del juego con cualquier programa de "
          "parches IPS.",
    "en": "22,997 bytes. Apply it to your own ROM of the game with any IPS tool.",
}
