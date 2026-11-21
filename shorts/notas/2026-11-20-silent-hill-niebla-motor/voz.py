import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Silent Hill da miedo por culpa de una consola que no podía.",
    "Es 1999, PlayStation, y el pueblo está cubierto de niebla.",
    "No ves más allá de unos pasos. Algo se mueve… y no sabes qué.",
    "Pero la niebla no se puso solo para asustar.",
    "Y eso no es lo más raro: la niebla nació de un problema.",
    "¿Cuál? La PlayStation no podía dibujar el pueblo a lo lejos sin que los edificios aparecieran de golpe.",
    "Konami lo tapó con niebla.",
    "Así que lo que más miedo da en Silent Hill… es lo que la consola no podía mostrarte.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Silent Hill": "Sáilent Jil", "1999": "mil novecientos noventa y nueve", "PlayStation": "Pléisteishon", "Konami": "Konámi"}
PAUSAS = {0: 0.5, 1: 0.45, 2: 0.5, 3: 0.4, 4: 0.8, 5: 0.35, 6: 0.55}
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
