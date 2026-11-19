import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Pokémon Rojo y Azul tenían un error que multiplicaba tus objetos.",
    "Hablabas con un viejito que te enseña a atrapar Pokémon.",
    "Luego volabas a una isla y nadabas por su costa, de arriba abajo.",
    "Pero lo que salía del agua no era un Pokémon: era un bloque de píxeles rotos.",
    "Y al terminar, el sexto objeto de tu mochila sumaba 128 más.",
    "Y eso no es lo más raro.",
    "¿Por qué? El juego leía tu nombre, guardado en la escena del viejito, como si fueran Pokémon salvajes.",
    "Nintendo hasta pidió no tocarlo.",
    "Así que el error más famoso de Pokémon… era un regalo para tu mochila.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Pokémon": "Pokémon", "128": "ciento veintiocho", "Nintendo": "Nintendo"}
PAUSAS = {0: 0.4, 1: 0.25, 2: 0.3, 3: 0.35, 4: 0.25, 5: 0.35, 6: 0.35, 7: 0.45}
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [np.zeros(int(sr * 0.25), dtype=np.float32)], [], 0.25
for i, l in enumerate(LINEAS):
    lv = l
    for a_, b_ in PRON.items(): lv = lv.replace(a_, b_)
    a, sr = k.create(lv, voice=VOZ, speed=VEL, lang=VOZ_LANG)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = PAUSAS.get(i, 0.2) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
