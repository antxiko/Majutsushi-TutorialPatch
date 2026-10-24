"""La fuente de 16 puntos del cartucho (bancos 5-6, 64 bytes por letra, p00:5B29): el caracter de
cada codigo, leido de su dibujo (tools/inventario.py la usa para leer las cadenas)."""
FILAS = [
    "1234567890一二三四五六",
    "七八九十東南西北公荒家算子自振食",
    "人終種槓設切荘断大打直倒搭定局貫",
    "牌不風平刻満摸流了連輪和立ルオプ",
    "ンウマいしー○×暗河海開花気喜魚",
    "元口混国士純順小上色正清前全双対",
    "帯地通底天燈頭同盃発宝門無緑老嶺",
    "撈飜々ダブリチ回月降字車績戦搶待",
    "単半吊倍鳴面役き＊ドラ決手所相敵",
    "点符ち仮雀跳麻縛り戻るロ練習選択",
    "性格実ますかでたせんが画補ワセ（",
    "）SRAMYN／。続行沖初期",
]
CAR = {}
for f, s in enumerate(FILAS):
    for i, c in enumerate(s):
        CAR[f * 16 + i + 1] = c


def lee(codigos):
    return "".join(CAR.get(c, "[%02X]" % c) for c in codigos)
