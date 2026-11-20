import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Street Fighter II nunca debió tener combos: nacieron por accidente.",
    "Es 1991 y Capcom está terminando su juego de peleas.",
    "Un golpe, y el rival tiene tiempo de cubrirse. Así debía ser.",
    "Pero probando el juego, alguien notó algo raro.",
    "Si cancelabas un golpe normal justo a tiempo, el especial entraba antes de que el rival reaccionara.",
    "¿Y por qué no lo arreglaron?",
    "Al principio querían quitarlo. Pero el juego era mucho más divertido así… y lo dejaron escondido.",
    "Así que cada combo que has hecho en tu vida… nació de un accidente.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Street Fighter II": "Strit Fáiter dos", "1991": "mil novecientos noventa y uno", "Capcom": "Cápcom"}
PAUSAS = {0: 0.5, 1: 0.4, 2: 0.45, 3: 0.4, 4: 0.55, 5: 0.45, 6: 0.5}
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
