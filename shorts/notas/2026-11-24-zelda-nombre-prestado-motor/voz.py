import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Zelda se llama así por la esposa de un escritor famoso.",
    "Mediados de los ochenta. Miyamoto tenía juego, pero no tenía nombre.",
    "Un encargado de publicidad le propuso hacer un libro ilustrado con la aventura.",
    "A Miyamoto el libro no le convenció… pero algo de esa propuesta sí.",
    "Y eso no es lo más raro: la princesa debía ser una belleza eterna.",
    "¿De dónde salió el nombre?",
    "El publicista dijo: un autor estadounidense famoso tiene una esposa llamada Zelda. Era Zelda Fitzgerald, esposa del autor de El gran Gatsby.",
    "Así que la princesa más famosa de los videojuegos… lleva el nombre de una mujer real.",
]
# solo pronunciación (pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Fitzgerald", "Fitsyérald"), ("Gatsby", "Gátsbi"), ("Miyamoto", "Miyamóto")]
PAUSAS = {0: 0.45, 1: 0.4, 2: 0.4, 3: 0.55, 4: 0.6, 5: 0.45, 6: 0.55}
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [np.zeros(int(sr * 0.25), dtype=np.float32)], [], 0.25
for i, l in enumerate(LINEAS):
    lv = l
    for a_, b_ in PRON: lv = lv.replace(a_, b_)
    a, sr = k.create(lv, voice=VOZ, speed=VEL, lang=VOZ_LANG)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = PAUSAS.get(i, 0.3) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
